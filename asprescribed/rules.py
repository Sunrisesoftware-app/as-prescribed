"""Deterministic rule engine over data/rules.json (handoff v3 §4 step 4).

A rule fires when the profile has its condition, the item carries its tag, and the sides meet.
No model decides a conflict: a block means 'documented restriction found, therapist decides'.
"""
import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from .config import DATA_DIR


@dataclass(frozen=True)
class Rule:
    id: str
    condition: str
    tag: str
    side: str  # left | right | any
    effect: str  # block | caution
    text: str


@dataclass(frozen=True)
class Profile:
    profile_id: str
    session_id: str
    language: str
    conditions: tuple[str, ...]
    summary: str


@cache
def load_rules(path: Path = DATA_DIR / "rules.json") -> tuple[Rule, ...]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return tuple(Rule(**{k: r[k] for k in ("id", "condition", "tag", "side", "effect", "text")})
                 for r in data["rules"])


@cache
def load_catalog(path: Path = DATA_DIR / "catalog.json") -> dict[str, dict]:
    return {e["id"]: e for e in json.loads(path.read_text(encoding="utf-8"))["exercises"]}


def load_profile(profile_id: str) -> Profile:
    d = json.loads((DATA_DIR / "profiles" / f"{profile_id}.json").read_text(encoding="utf-8"))
    return Profile(d["profile_id"], d["session_id"], d["language"], tuple(d["conditions"]), d["summary"])


def item_tags(exercise_id: str | None, extra: list[str] | tuple[str, ...] = ()) -> set[str]:
    base = set(load_catalog()[exercise_id]["tags"]) if exercise_id else set()
    return base | set(extra)


def _sides_meet(rule_side: str, item_side: str | None) -> bool:
    if rule_side == "any":
        return True
    if item_side in (None, "none"):
        # A side-specific restriction on an item whose side is unknown: fire, so it reaches a human.
        return True
    return item_side == rule_side or item_side == "both"


def check(profile: Profile, tags: set[str], side: str | None) -> list[Rule]:
    """Every rule that fires for one item, blocks first."""
    fired = [r for r in load_rules()
             if r.condition in profile.conditions and r.tag in tags and _sides_meet(r.side, side)]
    return sorted(fired, key=lambda r: (r.effect != "block", r.id))
