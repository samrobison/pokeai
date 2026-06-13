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

from typing import List, Optional, Tuple

from Pokemon import Move as AIMove, Pokemon as AIPokemon
from libs import calcDamge, nameFormat

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
) -> float:
    score = (my_hp / my_max) - (opp_hp / opp_max)
    if my_boosts and my_hp > 0:
        # Only credit the pokemon's primary attacking stat (atk OR spa), scaled
        # by HP fraction: a +6 sweeper at 5% HP can't cash its boosts in.
        stat = _primary_attack_stat(my_poke)
        score += BOOST_VALUE * my_boosts.get(stat, 0) * (my_hp / my_max)
    return score


def _stage_mult(stage: int) -> float:
    """Gen 3+ stat stage multiplier: +1=1.5x, +2=2.0x, -1=0.67x, etc."""
    return max(2, 2 + stage) / max(2, 2 - stage)


def _apply_damage(
    attacker: AIPokemon,
    defender: AIPokemon,
    move: AIMove,
    atk_stage: int = 0,
    def_stage: int = 0,
) -> float:
    if not move.category or move.power == 0:
        return 0.0
    try:
        min_dmg, max_dmg, _ = calcDamge(attacker, defender, move, defender.stats['hp'])
        raw = (min_dmg + max_dmg) / 2.0
        return raw * _stage_mult(atk_stage) / _stage_mult(def_stage)
    except Exception:
        return 0.0


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
    return move.power == 0 and _has_positive_boost(move)


def _viable_moves(pokemon: AIPokemon) -> List[AIMove]:
    """Our moves: damaging moves plus pure status moves that buff us."""
    moves = [
        m for m in pokemon.moves
        if m.category and (m.power > 0 or _has_positive_boost(m))
    ]
    return moves if moves else (pokemon.moves or [AIMove(None)])


def _opp_threat_moves(pokemon: AIPokemon) -> List[AIMove]:
    """
    Opponent's threat moves. If we haven't seen any moves yet, substitute a
    phantom move so we don't assume they're harmless.
    """
    moves = [m for m in pokemon.moves if m.category and m.power > 0]
    return moves if moves else [_phantom_move(pokemon)]


def _best_damage(attacker: AIPokemon, defender: AIPokemon) -> float:
    """Max damage attacker can deal — used for force-switch scoring."""
    return max((_apply_damage(attacker, defender, m) for m in _opp_threat_moves(attacker)), default=0.0)


# ---------------------------------------------------------------------------
# Maximin search
# ---------------------------------------------------------------------------

# An action is either an AIMove (use it) or an AIPokemon (switch to it).
Action = object


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
) -> Tuple[float, Optional[Action]]:
    my_boosts = my_boosts or {}
    my_max = my_poke.stats['hp']
    opp_max = opp_poke.stats['hp']

    if depth == 0 or my_hp <= 0 or opp_hp <= 0:
        return _eval(my_poke, my_hp, my_max, opp_hp, opp_max, my_boosts), None

    # Opponent moves sorted best-first for early cutoffs (no boost tracking for opp yet)
    opp_moves = sorted(
        _opp_threat_moves(opp_poke),
        key=lambda m: _apply_damage(opp_poke, my_poke, m),
        reverse=True,
    )

    best_score = float('-inf')
    best_action: Optional[Action] = None

    # Sort our moves: damaging moves by expected damage first, boost moves last
    def _move_priority(m: AIMove) -> float:
        if m.power > 0:
            atk_s, def_s = _boost_stages(m, my_boosts, {})
            return _apply_damage(my_poke, opp_poke, m, atk_s, def_s)
        return -1.0  # boost moves sorted after damaging moves

    my_move_options = sorted(_viable_moves(my_poke), key=_move_priority, reverse=True)

    for my_move in my_move_options:
        # Stat changes this move applies to US (can be positive like Swords Dance
        # or negative like Draco Meteor's -2 SpA). Always a dict here, possibly empty.
        self_boosts = my_move.boosts if isinstance(my_move.boosts, dict) else {}

        # Enforce the hard cap on chained setup moves.
        is_setup = _is_setup_move(my_move)
        if is_setup and consecutive_boosts >= MAX_CONSECUTIVE_BOOSTS:
            continue
        next_consec = consecutive_boosts + 1 if is_setup else 0

        worst = float('inf')
        for opp_move in opp_moves:
            # Damage we deal this turn, using our CURRENT boosts (a damaging move
            # with a self-debuff still hits at full power this turn — the debuff
            # only bites on subsequent turns).
            if my_move.power > 0:
                atk_s, def_s = _boost_stages(my_move, my_boosts, {})
                my_dmg = _apply_damage(my_poke, opp_poke, my_move, atk_s, def_s)
            else:
                my_dmg = 0.0

            # Damage opponent deals to us (uses our current def/spd boosts)
            opp_atk_s, my_def_s = _boost_stages(opp_move, {}, my_boosts)
            opp_dmg = _apply_damage(opp_poke, my_poke, opp_move, opp_atk_s, my_def_s)

            # Our self-boosts apply from next turn onward (e.g. Draco Meteor drops
            # our SpA, so the next Draco / special move is weaker in the subtree).
            next_boosts = _apply_boosts(my_boosts, self_boosts) if self_boosts else my_boosts

            score, _ = _maximin(
                my_poke, opp_poke,
                max(0.0, my_hp  - opp_dmg),
                max(0.0, opp_hp - my_dmg),
                depth - 1, my_bench,
                alpha=alpha,
                my_boosts=next_boosts,
                consecutive_boosts=next_consec,
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
        bench_max = bench_poke.stats['hp']
        worst = float('inf')
        for opp_move in opp_moves:
            # We deal 0 damage this turn; opponent attacks the incoming pokemon
            opp_dmg = _apply_damage(opp_poke, bench_poke, opp_move)
            new_bench_hp = max(0.0, bench_hp - opp_dmg)

            # Remaining bench after we switch in bench_poke
            new_bench = [(p, h) for p, h in my_bench if p.name != bench_poke.name]
            # Previous active goes to bench at current hp
            new_bench.append((my_poke, my_hp))

            score, _ = _maximin(
                bench_poke, opp_poke,
                new_bench_hp, opp_hp,
                depth - 1, new_bench,
                alpha=alpha,
                my_boosts={},          # boosts reset on switch
                consecutive_boosts=0,  # switching breaks the setup chain
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

def score_switch_in(candidate: AIPokemon, opp: AIPokemon) -> float:
    """
    Score a candidate pokemon to send in against opp.
    Higher = better. Combines:
      - bulk against opp's best attack (how many hits can we take)
      - damage we can deal to opp (can we threaten a KO)
    """
    incoming_dmg = _best_damage(opp, candidate)
    outgoing_dmg = _best_damage(candidate, opp)

    hits_to_ko_us   = candidate.stats['hp'] / (incoming_dmg + 1)
    pct_dmg_to_opp  = outgoing_dmg / (opp.stats['hp'] + 1)

    return hits_to_ko_us + pct_dmg_to_opp * 10


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

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

        # Replace my moves with only what's available this turn
        ai_moves_by_id: dict = {}
        for env_move in battle.available_moves:
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
        current_boosts = {k: v for k, v in my_env.boosts.items()
                          if k in ('atk', 'def', 'spa', 'spd', 'spe')}

        _, best_action = _maximin(my_poke, opp_poke, my_hp, opp_hp, depth, bench,
                                  my_boosts=current_boosts,
                                  consecutive_boosts=consecutive_boosts)

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
        best_env, best_score = None, float('-inf')
        for env_sw in battle.available_switches:
            candidate = pokemon_from_env(env_sw)
            s = score_switch_in(candidate, opp_poke)
            if s > best_score:
                best_score, best_env = s, env_sw
        return best_env
    except Exception as e:
        print(f"Switch scoring error: {e}")
        return None
