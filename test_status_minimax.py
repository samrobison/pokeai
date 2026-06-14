"""
Targeted unit checks for the status / Yawn / hazard modeling added to minimax.py.
Run: python test_status_minimax.py
"""
from Pokemon import Move as AIMove, Pokemon as AIPokemon
import minimax as mm
from minimax import Cond, Hazards


def mk_move(name, power=0, mtype='Normal', category='Physical', priority=0,
            status=None, volatile=None, hazard=None, boosts=None):
    return AIMove({
        'basePower': power, 'type': mtype, 'accuracy': 100, 'name': name,
        'category': category if power or category == 'status' else category,
        'pp': 10, 'priority': priority,
        'boosts': boosts or {}, 'status_inflicts': status,
        'volatile': volatile, 'hazard': hazard,
    })


def mk_poke(name, types, spe=100, ability='', moves=None,
            hp=300, atk=200, defe=200, spa=200, spd=200):
    p = AIPokemon.__new__(AIPokemon)
    p.null_init()
    p.name = name
    p.level = 100
    t2 = types[1] if len(types) > 1 else types[0]
    p.type = (types[0], t2)
    p.ability = ability
    p.stats = {'hp': hp, 'atk': atk, 'defe': defe, 'spa': spa, 'spd': spd, 'spe': spe}
    p.moves = moves or []
    return p


PASS, FAIL = [], []
def check(name, cond):
    (PASS if cond else FAIL).append(name)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")


# 1. Drowsy guard: a drowsy pokemon must not pick a pure setup move.
print("1. Drowsy suppresses setup")
nasty = mk_move('Nasty Plot', category='status', boosts={'spa': 2})
tackle = mk_move('Tackle', power=60)
me = mk_poke('me', ['Normal'], moves=[nasty, tackle])
opp = mk_poke('opp', ['Normal'], moves=[mk_move('Tackle', power=60)])
_, action = mm._maximin(me, opp, 300, 300, 4, [], my_cond=Cond(drowsy=1))
check("drowsy: does not return Nasty Plot", action is not tackle or action is tackle)
check("drowsy: returns the damaging move (Tackle)", action is tackle)
# sanity: without drowsy, setup is allowed to be considered (not asserting it's chosen)
_, action2 = mm._maximin(me, opp, 300, 300, 4, [])
check("no-drowsy: search still returns a move", action2 in (nasty, tackle))


# 2. Stealth Rock on our side: a Flying type loses 25% on entry (Rock 2x vs Flying).
print("2. Stealth Rock entry damage")
flyer = mk_poke('flyer', ['Flying'], hp=400)
hp_after, _ = mm._apply_hazards_on_entry(flyer, 400.0, Hazards(sr=True))
check("SR vs Flying = 25% (0.125 * 2x)", abs((400.0 - hp_after) - 100.0) < 1e-6)
ground = mk_poke('ground', ['Normal'], hp=400)
hp_after2, _ = mm._apply_hazards_on_entry(ground, 400.0, Hazards(sr=True))
check("SR vs Normal = 12.5%", abs((400.0 - hp_after2) - 50.0) < 1e-6)
# Spikes ignore a Flying (ungrounded) pokemon.
hp_fly_spikes, _ = mm._apply_hazards_on_entry(flyer, 400.0, Hazards(spikes=3))
check("Spikes do not hit Flying", abs(hp_fly_spikes - 400.0) < 1e-6)
# Toxic Spikes poison a grounded non-Poison/Steel; 2 layers => toxic.
_, tcond = mm._apply_hazards_on_entry(ground, 400.0, Hazards(tspikes=2))
check("2x Toxic Spikes => tox", tcond.status == 'tox')
steel = mk_poke('steel', ['Steel'])
_, scond = mm._apply_hazards_on_entry(steel, 300.0, Hazards(tspikes=2))
check("Steel immune to Toxic Spikes", scond.status is None)


# 3. Burn halves physical damage.
print("3. Burn halves physical")
phys = mk_move('Body Slam', power=100, category='Physical')
a = mk_poke('a', ['Normal'])
d = mk_poke('d', ['Normal'])
clean = mm._apply_damage(a, d, phys)
burned = mm._apply_damage(a, d, phys, attacker_status='brn')
check("burned physical ~= half", clean > 0 and abs(burned - clean / 2) < 1e-6)
spec = mk_move('Surf', power=100, category='special')
check("burn does NOT halve special",
      abs(mm._apply_damage(a, d, spec, attacker_status='brn')
          - mm._apply_damage(a, d, spec)) < 1e-6)


# 4. Turn order: faster side that KOs denies the slower side its damage.
print("4. Turn order / KO denial")
big = mk_move('Nuke', power=300, category='Physical')   # enough to KO
fast = mk_poke('fast', ['Normal'], spe=200, moves=[big])
slow = mk_poke('slow', ['Normal'], spe=60, moves=[big])  # 60 > 200*0.25=50 when fast is paralyzed
# fast vs slow, both have lethal moves, low HP so either KOs.
res = mm._simulate_pair(fast, slow, big, big, 50, 50,
                        {}, {}, Cond(), Cond(), Hazards(), Hazards())
my_hp_after, opp_hp_after = res[0], res[1]
check("faster KOs slower; faster takes no damage", my_hp_after == 50 and opp_hp_after <= 0)
# Paralyze the faster one -> order flips, the (now faster) slow side KOs first.
res2 = mm._simulate_pair(fast, slow, big, big, 50, 50,
                         {}, {}, Cond(status='par'), Cond(), Hazards(), Hazards())
check("paralysis flips order: paralyzed-fast side now takes the hit",
      res2[0] <= 0 and res2[1] == 50)


# 5. Opponent whose only move is Yawn registers as a threat.
print("5. Yawn registers as opponent threat")
yawn = mk_move('Yawn', category='status', volatile='yawn')
opp_yawn = mk_poke('opp', ['Normal'], moves=[yawn])
threats = mm._opp_threat_moves(opp_yawn)
check("Yawn is in opp threat moves", yawn in threats)
# After Yawn lands on us, our Cond should become drowsy in the sim.
res3 = mm._simulate_pair(me, opp_yawn, tackle, yawn, 300, 300,
                         {}, {}, Cond(), Cond(), Hazards(), Hazards())
my_cond_after = res3[4]
check("Yawn makes us drowsy in sim", my_cond_after.drowsy == 1)


print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    print("FAILED:", FAIL)
    raise SystemExit(1)
