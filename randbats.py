"""
Opponent priors from public random-battle set data.

For gen9randombattle, every species has a small known pool of moves, abilities,
items and a fixed level. We use this to guess an opponent's likely moves (and
ability/level) instead of falling back to a single generic "phantom" threat.

Data source: https://pkmn.github.io/randbats/data/gen9randombattle.json
Shipped in the repo as randbats_gen9.json; re-downloaded if the file is missing.
The data is loaded once at import time so no network call happens mid-battle.
"""

from __future__ import annotations

import json
import os
import urllib.request

_URL = "https://pkmn.github.io/randbats/data/gen9randombattle.json"
_CACHE = os.path.join(os.path.dirname(__file__), "randbats_gen9.json")

# Normalized:  species_id -> {"moves": [ids], "abilities": [ids], "level": int}
_DATA: dict | None = None


def normalize(name: str) -> str:
    """Showdown-style id: lowercase, alphanumerics only ('Body Press'->'bodypress')."""
    return "".join(c for c in (name or "").lower() if c.isalnum())


def _raw_data() -> dict:
    # Prefer the shipped/cached file; download once if absent.
    if os.path.exists(_CACHE):
        try:
            with open(_CACHE) as f:
                return json.load(f)
        except Exception:
            pass
    try:
        with urllib.request.urlopen(_URL, timeout=10) as resp:
            raw = json.loads(resp.read().decode())
        with open(_CACHE, "w") as f:
            json.dump(raw, f)
        return raw
    except Exception:
        return {}


def _load() -> dict:
    global _DATA
    if _DATA is not None:
        return _DATA

    raw = _raw_data()
    data: dict = {}
    for species, entry in raw.items():
        moves: set[str] = set()
        for role in (entry.get("roles") or {}).values():
            moves.update(normalize(m) for m in role.get("moves", []))
        # Older/flat format fallback
        moves.update(normalize(m) for m in entry.get("moves", []))

        data[normalize(species)] = {
            "moves":     sorted(moves),
            "abilities": [normalize(a) for a in entry.get("abilities", [])],
            "level":     entry.get("level"),
        }
    _DATA = data
    return _DATA


def get_set(species: str) -> dict | None:
    """Return {'moves', 'abilities', 'level'} for a species, or None if unknown."""
    return _load().get(normalize(species))


def possible_moves(species: str) -> list[str]:
    """All move ids the species can carry in random battles (union over roles)."""
    entry = get_set(species)
    return entry["moves"] if entry else []


def sole_ability(species: str) -> str | None:
    """The species' ability id if it's the only one it ever rolls, else None."""
    entry = get_set(species)
    if entry and len(entry["abilities"]) == 1:
        return entry["abilities"][0]
    return None


# Load at import so the (one-time) file read / download happens at startup.
_load()
