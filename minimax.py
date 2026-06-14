"""
Maximin search for simultaneous-choice Pokemon battles.

Both players choose simultaneously, so we use maximin:
  best_action = argmax over our_actions of (
                  min over their_moves of evaluate(state after both actions)
                )

Our actions include both moves AND switches. Switching costs the attack turn
(0 damage out) but the opponent still attacks into the incoming pokemon.

Force switches (after a faint) are handled separately by score_switch_in().
"""

from dataclasses import dataclass, replace
from typing import List, Optional, Tuple

from Pokemon import Move as AIMove, Pokemon as AIPokemon
from libs import TypeChart, calcDamge, moveEffectiveness, nameFormat

DEFAULT_DEPTH = 8

# Fraction of our own max HP subtracted from a switch action's score.
# Represents the opportunity cost of not attacking this turn.
SWITCH_COST = 0.12

# HP-fraction-equivalent value of one offensive stat stage at the leaf.
# Gives standing boosts positional value so the search will invest a turn in
# setup even before it has cashed the boost in as damage. Tunable.
BOOST_VALUE = 0.05

# Hardest cap on how many setup (pure stat-boost) moves may be used in a row.
# Once this many boosts have been chained, the search will not consider another
# setup move and must attack or switch instead.
MAX_CONSECUTIVE_BOOSTS = 2

# Moves that only cure the team's status conditions — useless with nothing to cure.
TEAM_CURE_MOVES = {'healbell', 'aromatherapy'}

# ---------------------------------------------------------------------------
# Status / hazard modeling constants (all in HP-fraction-equivalent units)
# ---------------------------------------------------------------------------

# Leaf penalty for the ACTIVE pokemon carrying a status (subtracted for us, added
# for the opponent). Scaled by the pokemon's HP fraction at the leaf.
STATUS_VALUE = {
    'slp': 0.30, 'frz': 0.30,   # can't act for multiple turns
    'tox': 0.12, 'par': 0.12,   # escalating chip / speed + skip chance
    'brn': 0.10,                # halves physical + chip
    'psn': 0.06,                # flat chip
}

# Leaf penalty for being "drowsy" (Yawn): sleep is one turn away.
DROWSY_VALUE = 0.15

# Positional value of hazards sitting on the OPPONENT's side (we can't simulate
# their switches, so this is the only credit for setting them). Our-side hazards
# are charged concretely as switch-in damage instead — no eval term, no double count.
OPP_HAZARD_VALUE = {'sr': 0.10, 'spikes': 0.04, 'tspikes': 0.05}  # spikes is per layer

SLEEP_TURNS = 2          # expected forced-sleep duration (real range 1-3)
PARA_OUTPUT_MULT = 0.75  # 25% full-paralysis chance → expected output
PARA_SPEED_MULT = 0.25   # paralysis quarters Speed for turn-order

BRN_CHIP = 1 / 16
PSN_CHIP = 1 / 8
TOX_UNIT = 1 / 16        # toxic damage = TOX_UNIT * counter each turn

# Type-based status immunities (defender's type can't receive the status).
_BURN_IMMUNE_TYPES = {'Fire'}
_FREEZE_IMMUNE_TYPES = {'Ice'}
_PARA_IMMUNE_TYPES = {'Electric'}
_POISON_IMMUNE_TYPES = {'Poison', 'Steel'}


@dataclass(frozen=True)
class Cond:
    """Status state of one side's ACTIVE pokemon."""
    status: Optional[str] = None   # 'brn'/'psn'/'tox'/'par'/'slp'/'frz' or None
    tox_counter: int = 1           # escalating toxic multiplier
    drowsy: int = 0                # turns until Yawn puts us to sleep (0 = none)
    sleep_turns: int = 0           # remaining forced-sleep turns


@dataclass(frozen=True)
class Hazards:
    """Entry hazards sitting on one side of the field."""
    sr: bool = False
    spikes: int = 0
    tspikes: int = 0


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _primary_attack_stat(pokemon: AIPokemon) -> str:
    """Whether this pokemon attacks mainly off Attack or Special Attack."""
    return 'atk' if pokemon.data.get('atk', 0) >= pokemon.data.get('spa', 0) else 'spa'


def _eval(
    my_poke: AIPokemon,
    my_hp: float,
    my_max: float,
    opp_hp: float,
    opp_max: float,
    my_boosts: Optional[dict] = None,
    my_cond: Optional[Cond] = None,
    opp_cond: Optional[Cond] = None,
    opp_hazards: Optional[Hazards] = None,
) -> float:
    score = (my_hp / my_max) - (opp_hp / opp_max)
    if my_boosts and my_hp > 0:
        # Only credit the pokemon's primary attacking stat (atk OR spa), scaled
        # by HP fraction: a +6 sweeper at 5% HP can't cash its boosts in.
        stat = _primary_attack_stat(my_poke)
        score += BOOST_VALUE * my_boosts.get(stat, 0) * (my_hp / my_max)

    # Status: bad on us, good on them (scaled by the sufferer's remaining HP —
    # a status on a near-dead pokemon barely matters).
    if my_cond and my_hp > 0 and my_cond.status in STATUS_VALUE:
        score -= STATUS_VALUE[my_cond.status] * (my_hp / my_max)
    if opp_cond and opp_hp > 0 and opp_cond.status in STATUS_VALUE:
        score += STATUS_VALUE[opp_cond.status] * (opp_hp / opp_max)

    # Drowsy (Yawn): sleep is imminent.
    if my_cond and my_cond.drowsy > 0 and my_hp > 0:
        score -= DROWSY_VALUE * (my_hp / my_max)
    if opp_cond and opp_cond.drowsy > 0 and opp_hp > 0:
        score += DROWSY_VALUE * (opp_hp / opp_max)

    # Hazards on the opponent's side are positional value for us.
    if opp_hazards:
        if opp_hazards.sr:
            score += OPP_HAZARD_VALUE['sr']
        score += OPP_HAZARD_VALUE['spikes'] * opp_hazards.spikes
        if opp_hazards.tspikes:
            score += OPP_HAZARD_VALUE['tspikes']

    return score


def _stage_mult(stage: int) -> float:
    """Gen 3+ stat stage multiplier: +1=1.5x, +2=2.0x, -1=0.67x, etc."""
    return max(2, 2 + stage) / max(2, 2 - stage)


# Abilities that grant full immunity to an entire move type. Keys are normalized
# ability ids (lowercase, no spaces); values are the immune move type.
ABILITY_TYPE_IMMUNITY = {
    'levitate':      'Ground',
    'flashfire':     'Fire',
    'wellbakedbody': 'Fire',
    'waterabsorb':   'Water',
    'stormdrain':    'Water',
    'dryskin':       'Water',
    'voltabsorb':    'Electric',
    'lightningrod':  'Electric',
    'motordrive':    'Electric',
    'sapsipper':     'Grass',
    'eartheater':    'Ground',
}

# Abilities that grant immunity to a class of moves identified by a move flag,
# regardless of type (Soundproof blocks Psychic Noise, Boomburst, Hyper Voice...).
ABILITY_FLAG_IMMUNITY = {
    'soundproof':  'sound',
    'bulletproof': 'bullet',
    'overcoat':    'powder',
    'windrider':   'wind',
}


def _ability_negates(defender: AIPokemon, move: AIMove) -> bool:
    """True if the defender's ability makes it immune to this move."""
    ability = (getattr(defender, 'ability', '') or '').replace(' ', '').lower()
    if not ability:
        return False

    # Type immunity (Levitate vs Ground, Flash Fire vs Fire, ...)
    immune_type = ABILITY_TYPE_IMMUNITY.get(ability)
    if immune_type and bool(move.type) and move.type.capitalize() == immune_type:
        return True

    # Move-flag immunity (Soundproof vs sound, Bulletproof vs bullet, ...)
    immune_flag = ABILITY_FLAG_IMMUNITY.get(ability)
    if immune_flag and immune_flag in getattr(move, 'flags', ()):
        return True

    return False


def _deals_fixed(move: AIMove) -> bool:
    """A fixed-damage move (Seismic Toss, Night Shade, Sonic Boom, Dragon Rage)."""
    return bool(getattr(move, 'fixed_damage', 0))


def _deals_damage(move: AIMove) -> bool:
    """Whether a move does any damage at all (normal power or fixed)."""
    return move.power > 0 or _deals_fixed(move)


def _apply_damage(
    attacker: AIPokemon,
    defender: AIPokemon,
    move: AIMove,
    atk_stage: int = 0,
    def_stage: int = 0,
    attacker_status: Optional[str] = None,
) -> float:
    if _ability_negates(defender, move):
        return 0.0  # e.g. Ground move into Levitate, Fire into Flash Fire

    # Fixed-damage moves ignore stats/STAB but still respect type immunity
    # (Seismic Toss/Fighting can't hit Ghost; Night Shade/Ghost can't hit Normal).
    if _deals_fixed(move):
        if moveEffectiveness(move, defender) == 0:
            return 0.0
        fd = move.fixed_damage
        return float(attacker.level or 100) if fd == 'level' else float(fd)

    if not move.category or move.power == 0:
        return 0.0
    try:
        min_dmg, max_dmg, _ = calcDamge(attacker, defender, move, defender.stats['hp'])
        raw = (min_dmg + max_dmg) / 2.0
        dmg = raw * _stage_mult(atk_stage) / _stage_mult(def_stage)
        # Burn halves physical output.
        if attacker_status == 'brn' and move.category == 'Physical':
            dmg *= 0.5
        return dmg
    except Exception:
        return 0.0


def _grounded(pokemon: AIPokemon) -> bool:
    """Affected by Spikes / Toxic Spikes (not Flying-type, not Levitate)."""
    if 'Flying' in pokemon.type:
        return False
    ability = (getattr(pokemon, 'ability', '') or '').replace(' ', '').lower()
    return ability != 'levitate'


def _can_status(defender: AIPokemon, status: str, existing: Optional[str]) -> bool:
    """Whether `status` can land on `defender` (no existing status, not type-immune)."""
    if existing:
        return False  # major statuses don't stack
    types = set(defender.type)
    if status == 'brn' and types & _BURN_IMMUNE_TYPES:
        return False
    if status == 'frz' and types & _FREEZE_IMMUNE_TYPES:
        return False
    if status == 'par' and types & _PARA_IMMUNE_TYPES:
        return False
    if status in ('psn', 'tox') and types & _POISON_IMMUNE_TYPES:
        return False
    return True


def _effective_speed(pokemon: AIPokemon, boosts: dict, status: Optional[str]) -> float:
    """Speed for turn-order: base × stage multiplier × paralysis penalty."""
    spe = pokemon.stats.get('spe', 0) * _stage_mult(boosts.get('spe', 0))
    if status == 'par':
        spe *= PARA_SPEED_MULT
    return spe


def _apply_move_effects(move: AIMove, target: str, st: dict,
                        target_alive: bool, target_poke: AIPokemon) -> None:
    """
    Apply `move`'s status / Yawn / hazard onto `target` ('me' or 'opp'),
    mutating the running turn state dict `st`.
    """
    prefix = 'my' if target == 'me' else 'opp'
    cond_key, haz_key = f'{prefix}_cond', f'{prefix}_hazards'

    # Primary status (Spore, Toxic, Will-O-Wisp, Thunder Wave, ...).
    status = getattr(move, 'status_inflicts', None)
    if status and target_alive:
        cond = st[cond_key]
        if _can_status(target_poke, status, cond.status):
            if status == 'slp':
                st[cond_key] = replace(cond, status='slp', sleep_turns=SLEEP_TURNS)
            elif status == 'tox':
                st[cond_key] = replace(cond, status='tox', tox_counter=1)
            else:
                st[cond_key] = replace(cond, status=status)

    # Yawn → drowsy (only on a statusless, awake target). Counter starts at 2 so
    # it survives this turn's end-of-turn and converts to sleep at the end of the
    # *next* turn — matching Yawn's one-turn delay.
    if getattr(move, 'volatile', None) == 'yawn' and target_alive:
        cond = st[cond_key]
        if not cond.status and cond.drowsy == 0:
            st[cond_key] = replace(cond, drowsy=2)

    # Entry hazards land on the target's side regardless of the active pokemon.
    hz = getattr(move, 'hazard', None)
    if hz:
        h = st[haz_key]
        if hz == 'sr':
            st[haz_key] = replace(h, sr=True)
        elif hz == 'spikes':
            st[haz_key] = replace(h, spikes=min(3, h.spikes + 1))
        elif hz == 'tspikes':
            st[haz_key] = replace(h, tspikes=min(2, h.tspikes + 1))


def _end_of_turn(cond: Cond, hp: float, max_hp: float) -> Tuple[Cond, float]:
    """Residual chip + sleep/drowsy progression for one side after a turn."""
    if hp <= 0:
        return cond, hp

    # Residual status damage.
    if cond.status == 'brn':
        hp -= BRN_CHIP * max_hp
    elif cond.status == 'psn':
        hp -= PSN_CHIP * max_hp
    elif cond.status == 'tox':
        hp -= TOX_UNIT * cond.tox_counter * max_hp
        cond = replace(cond, tox_counter=min(15, cond.tox_counter + 1))

    # A pokemon that spent this turn asleep ticks toward waking.
    if cond.status == 'slp' and cond.sleep_turns > 0:
        ns = cond.sleep_turns - 1
        cond = replace(cond, status=None, sleep_turns=0) if ns <= 0 else replace(cond, sleep_turns=ns)

    # Yawn countdown: when it expires the (still statusless) target falls asleep.
    if cond.drowsy > 0:
        nd = cond.drowsy - 1
        if nd == 0 and not cond.status:
            cond = replace(cond, drowsy=0, status='slp', sleep_turns=SLEEP_TURNS)
        else:
            cond = replace(cond, drowsy=nd)

    return cond, max(0.0, hp)


def _apply_hazards_on_entry(poke: AIPokemon, hp: float,
                            hazards: Optional[Hazards]) -> Tuple[float, Cond]:
    """Damage + status a pokemon takes from our-side hazards as it switches in."""
    cond = Cond()
    if hazards is None:
        return hp, cond
    max_hp = poke.stats['hp']
    t1, t2 = poke.type[0], poke.type[1]

    if hazards.sr:
        rock = TypeChart.get('Rock', {})
        # Single-typed pokemon are stored as (t, t); multiplying both slots would
        # double-count, so dedupe to get the true Rock effectiveness.
        mult = rock.get(t1, 1.0) if t1 == t2 else rock.get(t1, 1.0) * rock.get(t2, 1.0)
        hp -= 0.125 * mult * max_hp

    if hazards.spikes and _grounded(poke):
        frac = {1: 1 / 8, 2: 1 / 6, 3: 1 / 4}.get(hazards.spikes, 1 / 4)
        hp -= frac * max_hp

    if hazards.tspikes and _grounded(poke):
        if not (set(poke.type) & _POISON_IMMUNE_TYPES):  # Poison absorbs, Steel immune
            cond = replace(cond, status='tox', tox_counter=1) if hazards.tspikes >= 2 \
                else replace(cond, status='psn')

    return max(0.0, hp), cond


def _boost_stages(move: AIMove, attacker_boosts: dict, defender_boosts: dict):
    """Return (atk_stage, def_stage) for the damage calc given move category."""
    if move.category == 'Physical':
        return attacker_boosts.get('atk', 0), defender_boosts.get('def', 0)
    elif move.category == 'special':
        return attacker_boosts.get('spa', 0), defender_boosts.get('spd', 0)
    return 0, 0


def _apply_boosts(current: dict, delta: dict) -> dict:
    """Return new boosts dict after applying delta, clamped to [-6, +6]."""
    merged = dict(current)
    for stat, amount in delta.items():
        merged[stat] = max(-6, min(6, merged.get(stat, 0) + amount))
    return merged


def _phantom_move(pokemon: AIPokemon) -> AIMove:
    """
    Synthetic threat for an opponent whose moves we haven't seen yet.
    Uses their best offensive stat and primary type (STAB) at a typical base power.
    """
    use_physical = pokemon.data.get('atk', 0) >= pokemon.data.get('spa', 0)
    move_hash = {
        'basePower': 85,
        'type': pokemon.type[0],
        'accuracy': 100,
        'name': 'unknown',
        'category': 'Physical' if use_physical else 'special',
        'pp': 10,
        'priority': 0,
    }
    return AIMove(move_hash)


def _has_positive_boost(move: AIMove) -> bool:
    return (
        isinstance(move.boosts, dict)
        and any(v > 0 for v in move.boosts.values())
    )


def _is_setup_move(move: AIMove) -> bool:
    """A pure stat-boost move: deals no damage and raises one of our stats."""
    return not _deals_damage(move) and _has_positive_boost(move)


def _heals(move: AIMove) -> bool:
    """A pure self-heal move (Recover, Soft-Boiled, Roost)."""
    return getattr(move, 'heal', 0.0) > 0


def _has_status_effect(move: AIMove) -> bool:
    """A move that inflicts status, applies Yawn, or sets an entry hazard."""
    return bool(
        getattr(move, 'status_inflicts', None)
        or getattr(move, 'volatile', None) == 'yawn'
        or getattr(move, 'hazard', None)
    )


def _viable_moves(pokemon: AIPokemon) -> List[AIMove]:
    """Damaging, setup, healing, and status/hazard-inflicting moves."""
    moves = [
        m for m in pokemon.moves
        if m.category and (
            _deals_damage(m) or _has_positive_boost(m) or _heals(m) or _has_status_effect(m)
        )
    ]
    return moves if moves else (pokemon.moves or [AIMove(None)])


def _opp_threat_moves(pokemon: AIPokemon) -> List[AIMove]:
    """
    Opponent's threat moves — damaging moves plus status/Yawn/hazard moves (so
    enemy Spore, Toxic, Thunder Wave, Stealth Rock, etc. register as threats). If
    we haven't seen any moves yet, substitute a phantom move so we don't assume
    they're harmless.
    """
    moves = [
        m for m in pokemon.moves
        if m.category and (_deals_damage(m) or _has_status_effect(m))
    ]
    return moves if moves else [_phantom_move(pokemon)]


def _best_damage(
    attacker: AIPokemon,
    defender: AIPokemon,
    atk_boosts: Optional[dict] = None,
    def_boosts: Optional[dict] = None,
) -> float:
    """Max damage attacker can deal — used for force-switch scoring."""
    atk_boosts = atk_boosts or {}
    def_boosts = def_boosts or {}
    best = 0.0
    for m in _opp_threat_moves(attacker):
        a_s, d_s = _boost_stages(m, atk_boosts, def_boosts)
        best = max(best, _apply_damage(attacker, defender, m, a_s, d_s))
    return best


# ---------------------------------------------------------------------------
# Maximin search
# ---------------------------------------------------------------------------

# An action is either an AIMove (use it) or an AIPokemon (switch to it).
Action = object


def _simulate_pair(
    my_poke: AIPokemon, opp_poke: AIPokemon,
    my_move: AIMove, opp_move: AIMove,
    my_hp: float, opp_hp: float,
    my_boosts: dict, opp_boosts: dict,
    my_cond: Cond, opp_cond: Cond,
    my_hazards: Hazards, opp_hazards: Hazards,
):
    """
    Resolve one turn of (my_move vs opp_move) with turn order, status effects,
    burn/paralysis, residual chip, and status/Yawn/hazard application. Returns the
    post-turn state tuple for recursion.
    """
    my_max, opp_max = my_poke.stats['hp'], opp_poke.stats['hp']

    # Sleep/freeze means the side can't act at all this turn.
    my_acts = my_cond.status not in ('slp', 'frz')
    opp_acts = opp_cond.status not in ('slp', 'frz')

    def _dmg(att, dfn, mv, att_b, dfn_b, att_status, acts):
        if not acts or not _deals_damage(mv):
            return 0.0
        a_s, d_s = _boost_stages(mv, att_b, dfn_b)
        d = _apply_damage(att, dfn, mv, a_s, d_s, attacker_status=att_status)
        if att_status == 'par':
            d *= PARA_OUTPUT_MULT  # expected output given the 25% full-para chance
        return d

    my_dmg = _dmg(my_poke, opp_poke, my_move, my_boosts, opp_boosts, my_cond.status, my_acts)
    opp_dmg = _dmg(opp_poke, my_poke, opp_move, opp_boosts, my_boosts, opp_cond.status, opp_acts)

    # Turn order by (priority, effective speed). Equal → simultaneous (legacy behavior).
    my_key = (my_move.priority if my_acts else -99,
              _effective_speed(my_poke, my_boosts, my_cond.status))
    opp_key = (opp_move.priority if opp_acts else -99,
               _effective_speed(opp_poke, opp_boosts, opp_cond.status))
    if my_key > opp_key:
        order = ['me', 'opp']
    elif opp_key > my_key:
        order = ['opp', 'me']
    else:
        order = None  # simultaneous

    st = {
        'my_hp': my_hp, 'opp_hp': opp_hp,
        'my_boosts': my_boosts, 'opp_boosts': opp_boosts,
        'my_cond': my_cond, 'opp_cond': opp_cond,
        'my_hazards': my_hazards, 'opp_hazards': opp_hazards,
    }

    def _act(side, faint_denies):
        """Apply one side's move. If faint_denies, a fainted actor does nothing."""
        if side == 'me':
            if not my_acts or (faint_denies and st['my_hp'] <= 0):
                return
            st['opp_hp'] -= my_dmg
            heal = my_move.heal * my_max if getattr(my_move, 'heal', 0.0) else 0.0
            if getattr(my_move, 'drain', 0.0):
                heal += my_move.drain * my_dmg
            if heal:
                st['my_hp'] = min(my_max, st['my_hp'] + heal)
            sb = my_move.boosts if isinstance(my_move.boosts, dict) else {}
            if sb:
                st['my_boosts'] = _apply_boosts(st['my_boosts'], sb)
            _apply_move_effects(my_move, 'opp', st, st['opp_hp'] > 0, opp_poke)
        else:
            if not opp_acts or (faint_denies and st['opp_hp'] <= 0):
                return
            st['my_hp'] -= opp_dmg
            # Opponent self-boosts are intentionally not modeled inside the tree
            # (the min node already assumes their worst move); their standing
            # boosts persist via opp_boosts.
            _apply_move_effects(opp_move, 'me', st, st['my_hp'] > 0, my_poke)

    if order is None:
        _act('me', faint_denies=False)
        _act('opp', faint_denies=False)
    else:
        _act(order[0], faint_denies=True)
        _act(order[1], faint_denies=True)

    # End-of-turn residual + sleep/drowsy progression for survivors.
    st['my_cond'], st['my_hp'] = _end_of_turn(st['my_cond'], st['my_hp'], my_max)
    st['opp_cond'], st['opp_hp'] = _end_of_turn(st['opp_cond'], st['opp_hp'], opp_max)

    return (max(0.0, st['my_hp']), max(0.0, st['opp_hp']),
            st['my_boosts'], st['opp_boosts'],
            st['my_cond'], st['opp_cond'], st['my_hazards'], st['opp_hazards'])


def _maximin(
    my_poke: AIPokemon,
    opp_poke: AIPokemon,
    my_hp: float,
    opp_hp: float,
    depth: int,
    my_bench: List[Tuple[AIPokemon, float]],
    alpha: float = float('-inf'),
    my_boosts: Optional[dict] = None,
    consecutive_boosts: int = 0,
    opp_boosts: Optional[dict] = None,
    my_cond: Optional[Cond] = None,
    opp_cond: Optional[Cond] = None,
    my_hazards: Optional[Hazards] = None,
    opp_hazards: Optional[Hazards] = None,
) -> Tuple[float, Optional[Action]]:
    my_boosts = my_boosts or {}
    # Opponent's standing boosts (offensive AND defensive) stay constant in-tree —
    # they make our damage reflect their Iron Defense / Calm Mind and their damage
    # reflect their Swords Dance / Nasty Plot.
    opp_boosts = opp_boosts or {}
    my_cond = my_cond or Cond()
    opp_cond = opp_cond or Cond()
    my_hazards = my_hazards or Hazards()
    opp_hazards = opp_hazards or Hazards()
    my_max = my_poke.stats['hp']
    opp_max = opp_poke.stats['hp']

    if depth == 0 or my_hp <= 0 or opp_hp <= 0:
        return _eval(my_poke, my_hp, my_max, opp_hp, opp_max, my_boosts,
                     my_cond, opp_cond, opp_hazards), None

    # Opponent moves sorted best-first for early cutoffs (factor their atk boosts)
    def _opp_dmg_for_sort(m: AIMove) -> float:
        a_s, d_s = _boost_stages(m, opp_boosts, my_boosts)
        return _apply_damage(opp_poke, my_poke, m, a_s, d_s)

    opp_moves = sorted(_opp_threat_moves(opp_poke), key=_opp_dmg_for_sort, reverse=True)

    best_score = float('-inf')
    best_action: Optional[Action] = None

    # Sort our moves: damaging moves by expected damage first, boost moves last
    def _move_priority(m: AIMove) -> float:
        if _deals_damage(m):
            atk_s, def_s = _boost_stages(m, my_boosts, opp_boosts)
            return _apply_damage(my_poke, opp_poke, m, atk_s, def_s)
        return -1.0  # boost moves sorted after damaging moves

    my_move_options = sorted(_viable_moves(my_poke), key=_move_priority, reverse=True)

    for my_move in my_move_options:
        is_setup = _is_setup_move(my_move)
        # Hard cap on chained setup moves.
        if is_setup and consecutive_boosts >= MAX_CONSECUTIVE_BOOSTS:
            continue
        # Don't set up while drowsy or asleep — the boost gets wasted when we sleep.
        if is_setup and (my_cond.drowsy > 0 or my_cond.status in ('slp', 'frz')):
            continue
        next_consec = consecutive_boosts + 1 if is_setup else 0

        worst = float('inf')
        for opp_move in opp_moves:
            (m_hp, o_hp, m_b, o_b, m_c, o_c, m_hz, o_hz) = _simulate_pair(
                my_poke, opp_poke, my_move, opp_move,
                my_hp, opp_hp, my_boosts, opp_boosts,
                my_cond, opp_cond, my_hazards, opp_hazards,
            )
            score, _ = _maximin(
                my_poke, opp_poke, m_hp, o_hp,
                depth - 1, my_bench, alpha=alpha,
                my_boosts=m_b, consecutive_boosts=next_consec, opp_boosts=o_b,
                my_cond=m_c, opp_cond=o_c, my_hazards=m_hz, opp_hazards=o_hz,
            )
            if score < worst:
                worst = score
            if worst <= alpha:
                break

        if worst > best_score:
            best_score = worst
            best_action = my_move
            if best_score > alpha:
                alpha = best_score

    # --- Option B: switch to a benched pokemon ---
    for bench_poke, bench_hp in my_bench:
        # Our-side hazards hit the incoming pokemon before the opponent attacks.
        entry_hp, entry_cond = _apply_hazards_on_entry(bench_poke, bench_hp, my_hazards)
        worst = float('inf')
        for opp_move in opp_moves:
            # Opponent attacks the incoming pokemon (incoming has no boosts yet;
            # opponent keeps their offensive boosts). A sleeping/frozen opp can't.
            if opp_cond.status not in ('slp', 'frz') and _deals_damage(opp_move):
                opp_atk_s, _ = _boost_stages(opp_move, opp_boosts, {})
                opp_dmg = _apply_damage(opp_poke, bench_poke, opp_move, opp_atk_s, 0,
                                        attacker_status=opp_cond.status)
                if opp_cond.status == 'par':
                    opp_dmg *= PARA_OUTPUT_MULT
            else:
                opp_dmg = 0.0
            new_bench_hp = max(0.0, entry_hp - opp_dmg)

            # Remaining bench after we switch in bench_poke; previous active benched.
            new_bench = [(p, h) for p, h in my_bench if p.name != bench_poke.name]
            new_bench.append((my_poke, my_hp))

            # A turn passes for the opponent: residual chip + sleep/drowsy progress.
            o_cond_after, o_hp_after = _end_of_turn(opp_cond, opp_hp, opp_max)

            score, _ = _maximin(
                bench_poke, opp_poke,
                new_bench_hp, max(0.0, o_hp_after),
                depth - 1, new_bench, alpha=alpha,
                my_boosts={},          # boosts reset on switch
                consecutive_boosts=0,  # switching breaks the setup chain
                opp_boosts=opp_boosts,  # opponent's boosts persist when we switch
                my_cond=entry_cond,    # fresh (plus any Toxic Spikes poison)
                opp_cond=o_cond_after,
                my_hazards=my_hazards,  # our hazards stay on our side
                opp_hazards=opp_hazards,
            )
            if score < worst:
                worst = score
            if worst <= alpha:
                break
        # Deduct switch cost: we gave up an attack turn
        worst -= SWITCH_COST
        if worst > best_score:
            best_score = worst
            best_action = bench_poke
            if best_score > alpha:
                alpha = best_score

    return best_score, best_action


# ---------------------------------------------------------------------------
# Force-switch scoring (no search needed — just pick the best incoming pokemon)
# ---------------------------------------------------------------------------

def score_switch_in(candidate: AIPokemon, opp: AIPokemon,
                    opp_boosts: Optional[dict] = None,
                    my_hazards: Optional[Hazards] = None) -> float:
    """
    Score a candidate pokemon to send in against opp.
    Higher = better. Combines:
      - bulk against opp's best attack (how many hits can we take)
      - damage we can deal to opp (can we threaten a KO)

    opp_boosts factors in the opponent's standing boosts: their offensive boosts
    raise the damage we'd take, their defensive boosts lower the damage we'd deal.
    my_hazards charges the entry damage the candidate eats on the way in, so the
    scorer avoids walking a fragile / Rock-weak pokemon into Stealth Rock & Spikes.
    """
    opp_boosts = opp_boosts or {}
    incoming_dmg = _best_damage(opp, candidate, atk_boosts=opp_boosts)
    outgoing_dmg = _best_damage(candidate, opp, def_boosts=opp_boosts)

    eff_hp = candidate.stats['hp']
    if my_hazards is not None:
        eff_hp, _ = _apply_hazards_on_entry(candidate, eff_hp, my_hazards)

    hits_to_ko_us   = eff_hp / (incoming_dmg + 1)
    pct_dmg_to_opp  = outgoing_dmg / (opp.stats['hp'] + 1)

    return hits_to_ko_us + pct_dmg_to_opp * 10


def _cond_from_env(env_poke) -> Cond:
    """Build a Cond from a poke-env pokemon's live status / toxic counter / Yawn."""
    from poke_env.battle import Status
    from poke_env.battle.effect import Effect

    status, sleep_turns, tox = None, 0, 1
    if env_poke.status and env_poke.status != Status.FNT:
        status = env_poke.status.name.lower()
        if status == 'slp':
            sleep_turns = SLEEP_TURNS
        elif status == 'tox':
            tox = max(1, getattr(env_poke, 'status_counter', 1) or 1)

    drowsy = 0
    try:
        if Effect.YAWN in (env_poke.effects or {}):
            drowsy = 2  # matches the in-sim convention (see _apply_move_effects)
    except Exception:
        pass

    return Cond(status=status, tox_counter=tox, drowsy=drowsy, sleep_turns=sleep_turns)


def _hazards_from_env(side_conditions) -> Hazards:
    """Build a Hazards from a poke-env side_conditions mapping."""
    from poke_env.battle.side_condition import SideCondition

    sc = side_conditions or {}
    return Hazards(
        sr=SideCondition.STEALTH_ROCK in sc,
        spikes=sc.get(SideCondition.SPIKES, 0) or 0,
        tspikes=sc.get(SideCondition.TOXIC_SPIKES, 0) or 0,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _guess_opponent_kit(opp_poke: AIPokemon, opp_env) -> None:
    """
    Fill an opponent AIPokemon with likely moves and ability from random-battle
    data: the union of revealed moves and every move the species can carry, plus
    its ability when randbats pins it to a single option.
    """
    from converters import move_from_env
    from poke_env.battle.move import Move as EnvMove
    from randbats import possible_moves, sole_ability

    move_ids = set(opp_env.moves.keys()) | set(possible_moves(opp_env.species))
    guessed = []
    for mid in move_ids:
        try:
            guessed.append(move_from_env(EnvMove(mid, gen=9)))
        except Exception:
            pass
    if guessed:
        opp_poke.moves = guessed

    if not opp_env.ability:
        pinned = sole_ability(opp_env.species)
        if pinned:
            opp_poke.ability = pinned


def choose_best_move(battle, depth: int = DEFAULT_DEPTH, consecutive_boosts: int = 0):
    """
    Run maximin search over moves AND switches.

    consecutive_boosts is how many setup moves we've already used in a row this
    battle; the search refuses to plan more than MAX_CONSECUTIVE_BOOSTS in total.

    Returns a poke-env Move or Pokemon order object, or None on failure.
    """
    from converters import move_from_env, pokemon_from_env

    my_env  = battle.active_pokemon
    opp_env = battle.opponent_active_pokemon

    if my_env is None or opp_env is None:
        return None

    if not battle.available_moves and not battle.available_switches:
        return None

    try:
        my_poke  = pokemon_from_env(my_env)
        opp_poke = pokemon_from_env(opp_env, use_max_stats=True)
        _guess_opponent_kit(opp_poke, opp_env)

        # Replace my moves with only what's available this turn. Drop team-cure
        # moves (Heal Bell / Aromatherapy) when nobody is statused — but never
        # filter down to zero moves.
        team_has_status = any(p.status for p in battle.team.values())
        usable_moves = battle.available_moves
        if not team_has_status:
            filtered = [m for m in usable_moves if m.id not in TEAM_CURE_MOVES]
            if filtered:
                usable_moves = filtered

        ai_moves_by_id: dict = {}
        for env_move in usable_moves:
            ai_move = move_from_env(env_move)
            ai_moves_by_id[nameFormat(env_move.id)] = (env_move, ai_move)
        my_poke.moves = [ai for _, ai in ai_moves_by_id.values()]

        # Build bench: (AIPokemon, hp) for each available switch
        bench: List[Tuple[AIPokemon, float]] = []
        env_bench_map: dict = {}  # ai_name -> env_pokemon
        for env_sw in battle.available_switches:
            ai_sw = pokemon_from_env(env_sw)
            hp = float(env_sw.current_hp_fraction * ai_sw.stats['hp'])
            bench.append((ai_sw, hp))
            env_bench_map[ai_sw.name] = env_sw

        my_hp  = float(my_env.current_hp_fraction * my_poke.stats['hp'])
        opp_hp = float(opp_env.current_hp_fraction * opp_poke.stats['hp'])

        # Seed with current boosts so the search starts from real battle state
        stat_keys = ('atk', 'def', 'spa', 'spd', 'spe')
        current_boosts = {k: v for k, v in my_env.boosts.items() if k in stat_keys}
        opp_current_boosts = {k: v for k, v in opp_env.boosts.items() if k in stat_keys}

        # Seed live status / Yawn / entry hazards.
        my_cond = _cond_from_env(my_env)
        opp_cond = _cond_from_env(opp_env)
        my_hazards = _hazards_from_env(battle.side_conditions)
        opp_hazards = _hazards_from_env(battle.opponent_side_conditions)

        _, best_action = _maximin(my_poke, opp_poke, my_hp, opp_hp, depth, bench,
                                  my_boosts=current_boosts,
                                  consecutive_boosts=consecutive_boosts,
                                  opp_boosts=opp_current_boosts,
                                  my_cond=my_cond, opp_cond=opp_cond,
                                  my_hazards=my_hazards, opp_hazards=opp_hazards)

        if best_action is None:
            return None

        # Map back to poke-env object
        if isinstance(best_action, AIMove):
            target_key = nameFormat(best_action.name)
            for env_move, ai_move in ai_moves_by_id.values():
                if nameFormat(ai_move.name) == target_key:
                    return env_move

        if isinstance(best_action, AIPokemon):
            return env_bench_map.get(best_action.name)

    except Exception as e:
        print(f"Minimax error: {e}")

    return None


def choose_best_switch(battle) -> Optional[object]:
    """
    Score each available switch for a force-switch situation and return
    the best poke-env Pokemon to send in.
    """
    from converters import pokemon_from_env

    opp_env = battle.opponent_active_pokemon
    if opp_env is None or not battle.available_switches:
        return None

    try:
        opp_poke = pokemon_from_env(opp_env, use_max_stats=True)
        _guess_opponent_kit(opp_poke, opp_env)
        opp_boosts = {k: v for k, v in opp_env.boosts.items()
                      if k in ('atk', 'def', 'spa', 'spd', 'spe')}
        my_hazards = _hazards_from_env(battle.side_conditions)
        best_env, best_score = None, float('-inf')
        for env_sw in battle.available_switches:
            candidate = pokemon_from_env(env_sw)
            s = score_switch_in(candidate, opp_poke, opp_boosts=opp_boosts,
                                my_hazards=my_hazards)
            if s > best_score:
                best_score, best_env = s, env_sw
        return best_env
    except Exception as e:
        print(f"Switch scoring error: {e}")
        return None
