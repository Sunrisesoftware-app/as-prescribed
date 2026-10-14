"""The deterministic middle of the pipeline (handoff v3 §4 steps 3-5): tags, the rule check, and the
English line each patient line translates.

The English line is composed from the item's fields and the approved catalogue sentence, never
written by a model, so the generator's only freedom is the translation. A field the transcript does
not state is written as not stated, and the line becomes a proposal for the therapist to complete.
"""
import json
import re

from .config import DATA_DIR
from .rules import Profile, Rule, check, load_catalog, load_profile
from .schemas import Item, Objection, Span

# Item-level tags the catalogue cannot know: the same exercise with or without the prosthesis.
_EXTRA_TAGS = [(re.compile(r"prosthesis on|with the prosthesis|wearing the prosthesis", re.IGNORECASE), "prosthesis_on")]


def profile_for(session_id: str) -> Profile:
    for p in sorted((DATA_DIR / "profiles").glob("*.json")):
        if json.loads(p.read_text(encoding="utf-8")).get("session_id") == session_id:
            return load_profile(p.stem)
    raise KeyError(f"no profile for session {session_id}")


def cited_text(item: Item, spans: dict[str, Span]) -> str:
    return " ".join(spans[s].text for s in item.source_span_ids if s in spans)


def tag_item(item: Item, spans: dict[str, Span]) -> list[str]:
    entry = load_catalog().get(item.exercise_id or "")
    tags = set(entry["tags"]) if entry else set()
    text = cited_text(item, spans)
    tags |= {tag for pattern, tag in _EXTRA_TAGS if pattern.search(text)}
    return sorted(tags)


def rule_check(item: Item, profile: Profile) -> tuple[list[Objection], list[Rule]]:
    """Blocks as rule_conflict objections, cautions as rules for the line. No model involved."""
    fired = check(profile, set(item.tags), item.side)
    blocks = [Objection(item_id=item.item_id, kind="rule_conflict", source="rules",
                        detail=f"{r.id}: documented restriction found, therapist decides. {r.text}") for r in fired
              if r.effect == "block"]
    return blocks, [r for r in fired if r.effect == "caution"]


def completeness(item: Item) -> list[Objection]:
    entry = load_catalog().get(item.exercise_id or "")
    out = []
    if entry is None:
        out.append(Objection(item_id=item.item_id, kind="no_catalogue_match", source="checks", blocking=False,
                             detail="not a catalogued exercise: its tags, and so the rule check, are unknown"))
    missing = [f for f in ("dose", "frequency") if not getattr(item, f)]
    if entry and entry["side_mode"] == "per_side" and item.side in (None, "none"):
        missing.insert(0, "side")
    if missing:
        out.append(Objection(item_id=item.item_id, kind="incomplete", source="checks",
                             detail=f"not stated in the session: {', '.join(missing)}; the therapist completes it"))
    return out


_SIDE = {"left": "left", "right": "right", "both": "both sides"}


def compose(item: Item, cautions: list[Rule]) -> str:
    entry = load_catalog().get(item.exercise_id or "")
    name = entry["en"] if entry else item.exercise
    side = _SIDE.get(item.side or "", "side not stated" if entry and entry["side_mode"] == "per_side" else "")
    head = f"{name} ({side})." if side else f"{name}."
    how = entry["how"] if entry else ""
    if item.side in ("left", "right"):
        how = how.replace("the named ", f"your {item.side} ")
    elif entry and entry["side_mode"] == "per_side":
        how = how.replace("the named ", "your (side not stated) ")
    dose = canonical(item.dose) if item.dose else "Dose not stated"
    dose = dose[:1].upper() + dose[1:]
    freq = canonical(item.frequency) if item.frequency else "how often not stated"
    parts = [head, how, f"{dose}, {freq}."]
    parts += [_sentence(c) for c in item.cautions]
    parts += [f"From your records: {r.text}" for r in cautions]
    return " ".join(p for p in parts if p).replace("..", ".")


_WORDS = {"once": "1 time", "twice": "2 times", "thrice": "3 times", "one": "1", "two": "2", "three": "3",
          "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
          "eleven": "11", "twelve": "12", "fifteen": "15", "twenty": "20", "thirty": "30", "forty": "40",
          "sixty": "60"}


def canonical(text: str) -> str:
    """Numbers as digits and 'N sets of M' as 'N × M', so a translation can copy them unchanged
    (in Arabic a spelled-out two becomes a dual form, which no digit check can read). The multiplication
    sign, not the letter x: in right-to-left text a Latin x splits '3 x 10' and shows it as 'x 10 3'."""
    out = re.sub(r"[A-Za-z]+", lambda m: m[0] if m[0] == "x" else _WORDS.get(m[0].lower(), m[0]), text)
    out = re.sub(r"(\d+)\s+(?:sets?|rounds?)\s+of\s+(\d+)", r"\1 × \2", out)
    return re.sub(r"(\d+)\s*[xX]\s*(\d+)", r"\1 × \2", out)


def _sentence(text: str) -> str:
    t = text.strip()
    t = t[:1].upper() + t[1:]
    return t if t.endswith((".", "!", "?")) else t + "."
