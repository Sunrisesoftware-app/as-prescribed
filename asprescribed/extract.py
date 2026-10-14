"""Extract: the running list of items the therapist prescribes (handoff v3 §4 step 2).

The generator reads the transcript so far and returns the whole updated item list. Deterministic
checks then compare every number and side against the spans the item cites, before any model is
asked to judge it (the faktapankki T1 pattern from somnus: a number the source does not contain is
an objection, not a matter of opinion).
"""
import json
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from pydantic import ValidationError

from .config import Endpoint
from .llm import Completion, chat, extract_json
from .rules import load_catalog
from .schemas import Item, Objection, Span

SYSTEM = (
    "You extract the home exercise program a physiotherapist prescribes during a visit. "
    "You record only what the therapist actually prescribed in the transcript. "
    "You never add, complete, correct or improve anything."
)

INSTRUCTIONS = """Return the complete, updated list of items as one JSON object:
{"items": [{"item_id": "i1", "exercise": "<as the therapist named it>", "exercise_id": "<catalogue id or null>", "side": "left|right|both|none|null", "dose": "<as stated, or null>", "frequency": "<as stated, or null>", "cautions": ["<as stated>"], "source_span_ids": ["s003"], "status": "prescribed|deferred|withdrawn"}]}

Rules:
- Keep the item_id of every item already listed; a new item gets the next free number.
- side, dose and frequency: copy only what the transcript states. If it is not stated, use null. Never fill in a typical value.
- An exercise the therapist postpones ("not yet", "later", "next time") has status "deferred". One the therapist removes or advises against has status "withdrawn". An exercise only the patient mentions is not an item unless the therapist prescribes it.
- cautions: only warnings the therapist states for that exercise (what to do or avoid for safety), in the therapist's words. A reason or an explanation is not a caution.
- source_span_ids: every span that states the exercise, its side, dose, frequency or cautions.
- side is "none" for an exercise without a side (walking), "both" when both sides are prescribed.
- exercise_id: the catalogue id when the exercise is one of them, else null.
Answer with the JSON object only."""

ChatFn = Callable[..., Awaitable[Completion]]


def build_messages(spans: list[Span], items: list[Item]) -> list[dict]:
    catalogue = "\n".join(f"{eid}: {e['en']}" for eid, e in load_catalog().items())
    transcript = "\n".join(f"{s.span_id} | {s.speaker} | {s.text}" for s in spans)
    known = json.dumps([i.model_dump(exclude={"tags"}) for i in items], ensure_ascii=False)
    user = (f"Exercise catalogue (id: name):\n{catalogue}\n\n"
            f"Transcript so far (span_id | speaker | text):\n{transcript}\n\n"
            f"Items extracted so far:\n{known}\n\n{INSTRUCTIONS}")
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]


def parse_items(text: str, span_ids: set[str]) -> tuple[list[Item], list[str]]:
    """Items from the model's answer, plus a note for everything that had to be dropped or fixed.
    A cited span that does not exist is removed from the item; a catalogue id that does not exist
    becomes null. Nothing is invented to fill a gap."""
    data = extract_json(text)
    if not data or not isinstance(data.get("items"), list):
        raise ValueError("no items object in the answer")
    catalog = load_catalog()
    items, notes, seen = [], [], set()
    for raw in data["items"]:
        if not isinstance(raw, dict):
            notes.append("non-object item dropped")
            continue
        for key in ("side", "dose", "frequency", "exercise_id"):
            if raw.get(key) in ("null", "", "None"):
                raw[key] = None
        try:
            item = Item.model_validate(raw)
        except ValidationError as e:
            notes.append(f"item {raw.get('item_id')!r} dropped: {e.error_count()} validation error(s)")
            continue
        if item.item_id in seen:
            notes.append(f"duplicate {item.item_id} dropped")
            continue
        seen.add(item.item_id)
        unknown = [s for s in item.source_span_ids if s not in span_ids]
        if unknown:
            notes.append(f"{item.item_id}: unknown spans {unknown} removed")
            item.source_span_ids = [s for s in item.source_span_ids if s in span_ids]
        if item.exercise_id is not None and item.exercise_id not in catalog:
            notes.append(f"{item.item_id}: unknown catalogue id {item.exercise_id!r} set to null")
            item.exercise_id = None
        items.append(item)
    return items, notes


_NUMBER_WORDS = {
    "once": 1, "twice": 2, "thrice": 3, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "half": 0.5,
}


def numbers_in(text: str) -> set[float]:
    """Every number a text states, as digits or as an English number word."""
    found = {float(n) for n in re.findall(r"\d+(?:\.\d+)?", text or "")}
    found |= {float(_NUMBER_WORDS[w]) for w in re.findall(r"[a-z]+", (text or "").lower()) if w in _NUMBER_WORDS}
    return found


def check_item(item: Item, spans: dict[str, Span]) -> list[Objection]:
    """Deterministic checks against the cited spans only."""
    cited = " ".join(spans[s].text for s in item.source_span_ids if s in spans)
    out: list[Objection] = []
    if not item.source_span_ids:
        out.append(Objection(item_id=item.item_id, kind="not_entailed", source="checks",
                             detail="the item cites no transcript span"))
        return out
    source_numbers = numbers_in(cited)
    for fld, kind in (("dose", "wrong_dose"), ("frequency", "wrong_frequency")):
        missing = numbers_in(getattr(item, fld) or "") - source_numbers
        if missing:
            nums = ", ".join(f"{n:g}" for n in sorted(missing))
            out.append(Objection(item_id=item.item_id, kind=kind, source="checks",
                                 detail=f"{fld} states {nums}, which the cited spans do not"))
    words = set(re.findall(r"[a-z]+", cited.lower()))
    if item.side in ("left", "right") and item.side not in words:
        out.append(Objection(item_id=item.item_id, kind="wrong_side", source="checks",
                             detail=f"side {item.side} is not stated in the cited spans"))
    # A bilateral catalogue exercise (sit-to-stand) is done on both sides by nature, so it needs no word for it.
    bilateral = load_catalog().get(item.exercise_id or "", {}).get("side_mode") == "bilateral"
    if item.side == "both" and not bilateral and not words & {"both", "each", "sides", "legs", "arms", "hands"}:
        out.append(Objection(item_id=item.item_id, kind="wrong_side", source="checks",
                             detail="both sides are not stated in the cited spans"))
    return out


@dataclass
class ExtractResult:
    items: list[Item]
    objections: list[Objection]
    notes: list[str] = field(default_factory=list)
    completions: list[Completion] = field(default_factory=list)


async def extract(spans: list[Span], items: list[Item], ep: Endpoint, *, chat_fn: ChatFn = chat,
                  max_tokens: int = 2000) -> ExtractResult:
    """One extraction round over the transcript so far. A malformed answer is retried once; a second
    failure keeps the previous items, so a bad round never empties the program."""
    messages = build_messages(spans, items)
    span_ids = {s.span_id for s in spans}
    completions, notes = [], []
    for attempt in range(2):
        c = await chat_fn(ep, messages, max_tokens=max_tokens, temperature=0.0)
        completions.append(c)
        try:
            new_items, notes = parse_items(c.content, span_ids)
            break
        except ValueError as e:
            notes = [f"attempt {attempt + 1}: {e}"]
            messages = [*messages, {"role": "assistant", "content": c.content},
                        {"role": "user", "content": "Answer with the JSON object only, in the format given."}]
    else:
        return ExtractResult(items=items, objections=[], notes=[*notes, "kept the previous items"],
                             completions=completions)
    by_id = {s.span_id: s for s in spans}
    objections = [o for i in new_items if i.status == "prescribed" for o in check_item(i, by_id)]
    return ExtractResult(items=new_items, objections=objections, notes=notes, completions=completions)
