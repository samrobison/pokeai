"""
Convert a game_logger state dict → fixed-length float32 vector for DQN input.

Layout (STATE_DIM = 671):
  My active pokemon     57   hp(1) + status_oh(7) + type1_oh(18) + type2_oh(18) + stats(6) + boosts(7)
  My moves × 4        100   per slot: valid(1) + power(1) + type_oh(18) + cat_oh(3) + pp(1) + eff(1) = 25
  My bench × 5        220   per slot: alive(1) + hp(1) + type1_oh(18) + type2_oh(18) + stats(6) = 44
  Opp active            50   hp(1) + status_oh(7) + type1_oh(18) + type2_oh(18) + stats(6)  [no boosts]
  Opp bench × 5       220   same per-slot encoding as my bench
  Weather               8   one-hot (0=clear, 1-7)
  Fields               16   binary flags
  ─────────────────────────
  STATE_DIM           671

Actions (ACTION_DIM = 9):
  0–3  → available_moves[0–3]
  4–8  → available_switches[0–4]
"""

from __future__ import annotations

import numpy as np
from typing import Optional

# ── Type table ────────────────────────────────────────────────────────────────
TYPES = [
    "Normal", "Fire", "Water", "Electric", "Grass", "Ice",
    "Fighting", "Poison", "Ground", "Flying", "Psychic", "Bug",
    "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy",
]
_TYPE_IDX: dict[str, int] = {t.upper(): i for i, t in enumerate(TYPES)}
N_TYPES = 18  # len(TYPES)

# ── Status table ──────────────────────────────────────────────────────────────
_STATUSES = ["BRN", "FRZ", "PAR", "PSN", "TOX", "SLP"]
_STATUS_IDX: dict[str, int] = {s: i + 1 for i, s in enumerate(_STATUSES)}
N_STATUS = 7  # 0 = healthy

# ── Weather table ─────────────────────────────────────────────────────────────
_WEATHERS = [
    "SUNNYDAY", "DESOLATELAND",
    "RAINDANCE", "PRIMORDIALSEA",
    "SANDSTORM", "HAIL", "SNOW",
]
_WEATHER_IDX: dict[str, int] = {w: i + 1 for i, w in enumerate(_WEATHERS)}
N_WEATHER = 8  # 0 = clear

# ── Field table ───────────────────────────────────────────────────────────────
FIELDS_LIST = [
    "TRICKROOM", "GRAVITY", "MAGICROOM", "WONDERROOM",
    "ELECTRICTERRAIN", "GRASSYTERRAIN", "MISTYTERRAIN", "PSYCHICTERRAIN",
    "TAILWINDALLY", "TAILWINDENEMY",
    "STEALTHROCKALLY", "STEALTHROCKENEMY",
    "SPIKESALLY", "SPIKESENEMY",
    "TOXICSPIKESALLY", "TOXICSPIKESENEMY",
]
_FIELD_IDX: dict[str, int] = {f: i for i, f in enumerate(FIELDS_LIST)}
N_FIELDS = 16  # len(FIELDS_LIST)

# ── Dimension constants ───────────────────────────────────────────────────────
_ACTIVE_DIM  = 57   # my active (with boosts)
_OPP_ACT_DIM = 50   # opp active (no boosts)
_MOVE_DIM    = 25   # per move slot
_BENCH_DIM   = 44   # per bench slot

STATE_DIM  = (
    _ACTIVE_DIM          # my active
    + 4 * _MOVE_DIM      # my 4 move slots
    + 5 * _BENCH_DIM     # my 5 bench slots
    + _OPP_ACT_DIM       # opp active
    + 5 * _BENCH_DIM     # opp 5 bench slots
    + N_WEATHER          # weather one-hot
    + N_FIELDS           # fields binary
)  # = 671

ACTION_DIM = 9  # 4 moves + 5 switches


# ── Low-level encoding helpers ────────────────────────────────────────────────

def _type_oh(name: Optional[str]) -> np.ndarray:
    v = np.zeros(N_TYPES, np.float32)
    if name:
        idx = _TYPE_IDX.get(name.upper())
        if idx is not None:
            v[idx] = 1.0
    return v


def _status_oh(status: Optional[str]) -> np.ndarray:
    v = np.zeros(N_STATUS, np.float32)
    v[_STATUS_IDX.get(status or "", 0)] = 1.0
    return v


def _stats_norm(base_stats: dict) -> np.ndarray:
    """Normalize base stats by 255 (max possible in-game)."""
    return np.array([
        base_stats.get("hp",  0) / 255.0,
        base_stats.get("atk", 0) / 255.0,
        base_stats.get("def", 0) / 255.0,
        base_stats.get("spa", 0) / 255.0,
        base_stats.get("spd", 0) / 255.0,
        base_stats.get("spe", 0) / 255.0,
    ], np.float32)


def _boosts_norm(boosts: dict) -> np.ndarray:
    """Normalize stat boosts from [-6,+6] → [-1,+1]."""
    keys = ["atk", "def", "spa", "spd", "spe", "accuracy", "evasion"]
    return np.array([boosts.get(k, 0) / 6.0 for k in keys], np.float32)


def _encode_active(poke: dict, include_boosts: bool) -> np.ndarray:
    """Encode an active pokemon dict.  Length = 57 (boosts=True) or 50 (False)."""
    types = poke.get("type") or []
    parts = [
        np.array([poke.get("hp_fraction", 0.0)], np.float32),      # 1
        _status_oh(poke.get("status")),                              # 7
        _type_oh(types[0] if types else None),                       # 18
        _type_oh(types[1] if len(types) > 1 else (types[0] if types else None)),  # 18
        _stats_norm(poke.get("base_stats") or {}),                   # 6
    ]
    if include_boosts:
        parts.append(_boosts_norm(poke.get("boosts") or {}))        # 7
    return np.concatenate(parts)


def _encode_move(move: Optional[dict]) -> np.ndarray:
    """Encode a single available-move dict → 25 floats.  All zeros if no move."""
    if move is None:
        return np.zeros(_MOVE_DIM, np.float32)

    cat = (move.get("category") or "").lower()
    cat_oh = np.zeros(3, np.float32)
    cat_oh[{"physical": 0, "special": 1}.get(cat, 2)] = 1.0

    pp     = float(move.get("pp",     0) or 0)
    max_pp = float(move.get("max_pp", 1) or 1)

    eff = move.get("effectiveness")
    eff_v = float(np.log2(max(eff, 1e-6)) / 2.0) if eff else 0.0  # [-2,+2] → [-1,+1]

    return np.concatenate([
        np.array([1.0, move.get("base_power", 0) / 200.0], np.float32),  # valid, power  (2)
        _type_oh(move.get("type")),                                        # type          (18)
        cat_oh,                                                             # category      (3)
        np.array([pp / max_pp, eff_v], np.float32),                       # pp, eff       (2)
    ])  # total = 25


def _encode_bench_slot(slot: Optional[dict]) -> np.ndarray:
    """Encode a bench pokemon dict → 44 floats.  All zeros if slot is empty."""
    if slot is None:
        return np.zeros(_BENCH_DIM, np.float32)
    types = slot.get("type") or []
    fainted = slot.get("fainted", False)
    return np.concatenate([
        np.array([0.0 if fainted else 1.0,          # alive
                  slot.get("hp_fraction", 0.0)],     # hp_frac
                 np.float32),                                            # 2
        _type_oh(types[0] if types else None),                          # 18
        _type_oh(types[1] if len(types) > 1 else (types[0] if types else None)),  # 18
        _stats_norm(slot.get("base_stats") or {}),                      # 6
    ])  # total = 44


# ── Public API ────────────────────────────────────────────────────────────────

def encode_state(state: dict) -> np.ndarray:
    """
    Convert a game_logger state dict → float32 vector of shape (STATE_DIM,) = (671,).

    The dict must contain the keys produced by game_logger.build_state(), including
    the 'bench_pokemon' and 'opponent_bench' fields added for DQN support.
    """
    parts: list[np.ndarray] = []

    # My active pokemon (57)
    parts.append(_encode_active(state.get("my_pokemon") or {}, include_boosts=True))

    # My moves — pad to 4 slots (100)
    moves = list((state.get("available_moves") or []))[:4]
    while len(moves) < 4:
        moves.append(None)
    for m in moves:
        parts.append(_encode_move(m))

    # My bench — pad to 5 slots (220)
    bench = list((state.get("bench_pokemon") or []))[:5]
    while len(bench) < 5:
        bench.append(None)
    for b in bench:
        parts.append(_encode_bench_slot(b))

    # Opponent active (50)
    parts.append(_encode_active(state.get("opponent_pokemon") or {}, include_boosts=False))

    # Opponent bench — pad to 5 slots (220)
    opp_bench = list((state.get("opponent_bench") or []))[:5]
    while len(opp_bench) < 5:
        opp_bench.append(None)
    for b in opp_bench:
        parts.append(_encode_bench_slot(b))

    # Weather one-hot (8)
    weather_v = np.zeros(N_WEATHER, np.float32)
    w = state.get("weather")
    weather_v[_WEATHER_IDX.get((w or "").upper(), 0)] = 1.0
    parts.append(weather_v)

    # Fields binary (16)
    fields_v = np.zeros(N_FIELDS, np.float32)
    for f in (state.get("fields") or []):
        idx = _FIELD_IDX.get(f.upper())
        if idx is not None:
            fields_v[idx] = 1.0
    parts.append(fields_v)

    result = np.concatenate(parts)
    assert result.shape == (STATE_DIM,), f"State dim: expected {STATE_DIM}, got {result.shape[0]}"
    return result


def encode_action_mask(state: dict) -> np.ndarray:
    """
    Boolean mask of shape (ACTION_DIM,) = (9,).
    True  → action is legal this turn.
    False → action is illegal (network output masked to −∞ before argmax).
    """
    mask = np.zeros(ACTION_DIM, bool)
    n_moves    = min(len(state.get("available_moves")    or []), 4)
    n_switches = min(len(state.get("available_switches") or []), 5)
    mask[:n_moves]        = True
    mask[4: 4+n_switches] = True
    return mask


def state_action_idx(state: dict) -> Optional[int]:
    """
    Map the logged 'action'/'action_type' fields back to an action index 0–8.
    Returns None if the action isn't found in the available lists (e.g. random fallback).
    """
    action      = state.get("action")
    action_type = state.get("action_type")
    if action is None:
        return None

    if action_type == "move":
        for i, m in enumerate((state.get("available_moves") or [])[:4]):
            if m and m.get("id") == action:
                return i

    elif action_type == "switch":
        for i, s in enumerate((state.get("available_switches") or [])[:5]):
            if s == action:
                return 4 + i

    return None
