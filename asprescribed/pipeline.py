"""One session end to end, in falsification rounds (handoff v3 §2 and §4).

Round k: the falsifier and the deterministic checks object to draft D_k; the generator corrects the
items and translations they object to, giving D_(k+1). The loop stops when no correctable objection
remains, after max_rounds, or when the time budget is spent. What remains is shown to the therapist,
and every line gets exactly one state: conflict > proposal > uncertain translation > supported.
"""
import json
import time
from collections import Counter
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from .config import DATA_DIR, Endpoint
from .extract import ChatFn, check_item, extract, numbers_in, parse_items
from .falsify import check_items, check_translations
from .ingest import load_spans, session_path
from .llm import Completion, chat
from .program import completeness, compose, profile_for, rule_check, tag_item
from .rules import load_catalog
from .schemas import CORRECTABLE, Item, LineState, Objection, PatientLine, Span, resolve_state
from .translate import number_check, translate

CORRECT_SYSTEM = ("You correct a physiotherapy home program so that it says exactly what the therapist prescribed "
                  "in the transcript, and nothing else.")


@dataclass
class RoundLog:
    round: int
    objections: dict[str, int]   # by kind, everything raised this round
    correctable: int             # what the generator was asked to fix
    seconds: float
    raised: list[dict] = field(default_factory=list)  # every objection raised this round


@dataclass
class SessionResult:
    session_id: str
    language: str
    lines: list[PatientLine]
    heard_not_prescribed: list[Item]       # deferred or withdrawn: shown to the therapist, never to the patient
    rounds: list[RoundLog]
    items: list[Item] = field(default_factory=list)  # the final items, all statuses
    notes: list[str] = field(default_factory=list)
    calls: dict[str, list[dict]] = field(default_factory=lambda: {"generator": [], "falsifier": []})
    seconds: float = 0.0

    def summary(self) -> dict:
        states = Counter(line.state.value for line in self.lines)
        return {"session": self.session_id, "states": dict(states), "rounds": len(self.rounds),
                "objections_per_round": [r.correctable for r in self.rounds], "seconds": round(self.seconds, 1)}


def _log(result: SessionResult, role: str, c: Completion, what: str) -> None:
    result.calls[role].append({"what": what, "seconds": round(c.seconds, 2), "tokens": c.completion_tokens,
                               "tokens_per_s": round(c.tokens_per_s, 1) if c.tokens_per_s else None})


async def correct_items(spans: list[Span], items: list[Item], objections: list[Objection], ep: Endpoint, *,
                        chat_fn: ChatFn) -> tuple[list[Item], list[str], Completion]:
    flagged = {o.item_id for o in objections}
    transcript = "\n".join(f"{s.span_id} | {s.speaker} | {s.text}" for s in spans)
    shown = [i.model_dump(exclude={"tags"}) for i in items if i.item_id in flagged]
    objs = [o.model_dump(include={"item_id", "kind", "detail"}) for o in objections]
    user = (f"Transcript (span_id | speaker | text):\n{transcript}\n\nItems:\n{json.dumps(shown, ensure_ascii=False)}\n\n"
            f"A checker raised these objections:\n{json.dumps(objs, ensure_ascii=False)}\n\n"
            "Correct each item so it states only what the therapist said. If the transcript does not state a field, "
            "set it to null; never fill in a typical value. If the therapist postponed the exercise, set status "
            '"deferred"; if the therapist never prescribed it or left it out, set status "withdrawn". If you are sure '
            "an objection is wrong, keep the item as it is. Keep every item_id.\n"
            'Answer with one JSON object only: {"items": [ ...the corrected items, same fields... ]}')
    c = await chat_fn(ep, [{"role": "system", "content": CORRECT_SYSTEM}, {"role": "user", "content": user}],
                      max_tokens=2000, temperature=0.0)
    try:
        fixed, notes = parse_items(c.content, {s.span_id for s in spans})
    except ValueError as e:
        return items, [f"correction unreadable: {e}"], c
    by_id = {i.item_id: i for i in fixed if i.item_id in flagged}
    return [by_id.get(i.item_id, i) for i in items], notes, c


async def run_session(session_id: str, gen: Endpoint, fal: Endpoint, *, chat_fn: ChatFn = chat,
                      max_rounds: int = 3, budget_s: float | None = None,
                      items: list[Item] | None = None,
                      translation_hook: Callable[[str, str], str] | None = None,
                      on_event: Callable[[str, dict], Awaitable[None]] | None = None) -> SessionResult:
    """items: start from these instead of extracting (the evaluation injects item errors this way).
    translation_hook(item_id, text): applied to round 0's translations (the evaluation injects
    mistranslations this way); later rounds re-translate without it.
    on_event(kind, data): awaited at every stage, so a view can show the rounds as they happen."""

    async def emit(kind: str, **data) -> None:
        if on_event:
            await on_event(kind, data)

    t0 = time.perf_counter()
    spans = load_spans(session_path(session_id))
    by_id = {s.span_id: s for s in spans}
    profile = profile_for(session_id)
    language = profile.language
    result = SessionResult(session_id, language, [], [], [])

    if items is None:
        ex = await extract(spans, [], gen, chat_fn=chat_fn)
        for c in ex.completions:
            _log(result, "generator", c, "extract")
        result.notes += ex.notes
        items = ex.items
        await emit("extracted", items=len(items))

    translations: dict[str, str] = {}
    sources: dict[str, str] = {}
    backs: dict[str, str] = {}
    feedback: dict[str, str] = {}
    final: dict[str, list[Objection]] = {}
    rule_ids: dict[str, list[str]] = {}

    for k in range(max_rounds):
        tr = time.perf_counter()
        await emit("round", round=k)
        prescribed = [i for i in items if i.status == "prescribed"]
        raised: list[Objection] = []
        english: dict[str, str] = {}
        for i in prescribed:
            i.tags = tag_item(i, by_id)
            blocks, cautions = rule_check(i, profile)
            rule_ids[i.item_id] = [o.detail.split(":")[0] for o in blocks] + [r.id for r in cautions]
            raised += blocks + completeness(i) + check_item(i, by_id)
            english[i.item_id] = compose(i, cautions)

        if prescribed:
            fobj, c = await check_items(spans, prescribed, fal, chat_fn=chat_fn)
            _log(result, "falsifier", c, f"check items r{k}")
            result.notes += [o.detail for o in fobj if o.item_id == "*"]
            raised += [o for o in fobj if o.item_id != "*"]
            await emit("checked", round=k, objections=len([o for o in fobj if o.item_id != "*"]))

        # Translate only lines that are new, changed, or objected to last round.
        todo = {iid: en for iid, en in english.items()
                if sources.get(iid) != en or iid in feedback or iid not in translations}
        if todo:
            new, c = await translate(todo, language, gen, chat_fn=chat_fn, feedback=feedback)
            _log(result, "generator", c, f"translate r{k}")
            if translation_hook and k == 0:
                new = {iid: translation_hook(iid, text) for iid, text in new.items()}
            translations.update(new)
            await emit("translated", round=k, lines=len(new))
            sources.update({iid: en for iid, en in todo.items() if iid in new})
            missing = [iid for iid in todo if iid not in new]
            raised += [Objection(item_id=iid, kind="mistranslation", source="checks",
                                 detail="the generator returned no translation for this line") for iid in missing]
            checkable = {iid: new[iid] for iid in todo if iid in new}
            by_item = {i.item_id: i for i in prescribed}
            for iid, text in checkable.items():
                required = numbers_in(by_item[iid].dose or "") | numbers_in(by_item[iid].frequency or "")
                raised += number_check(iid, english[iid], text, required)
            if checkable:
                back, tobj, c = await check_translations({i: english[i] for i in checkable}, checkable, language, fal,
                                                         chat_fn=chat_fn)
                _log(result, "falsifier", c, f"check translations r{k}")
                backs.update(back)
                raised += tobj
                await emit("back_checked", round=k, objections=len(tobj))
        # Translation objections from earlier rounds stand for lines not re-translated this round.
        for iid, objs in final.items():
            if iid in english and iid not in todo:
                raised += [o for o in objs if o.kind == "mistranslation"]

        final = {}
        for o in raised:
            final.setdefault(o.item_id, []).append(o)
        item_fix = [o for o in raised if o.kind in CORRECTABLE and o.blocking]
        trans_fix = {o.item_id: o.detail for o in raised if o.kind == "mistranslation"}
        result.rounds.append(RoundLog(k, dict(Counter(o.kind for o in raised)), len(item_fix) + len(trans_fix),
                                      round(time.perf_counter() - tr, 2), [o.model_dump() for o in raised]))
        await emit("round_done", round=k, correctable=len(item_fix) + len(trans_fix))

        out_of_time = budget_s is not None and time.perf_counter() - t0 > budget_s
        if not item_fix and not trans_fix or k == max_rounds - 1 or out_of_time:
            if out_of_time:
                result.notes.append(f"time budget {budget_s:g} s spent after round {k}")
            break
        if item_fix:
            items, notes, c = await correct_items(spans, items, item_fix, gen, chat_fn=chat_fn)
            _log(result, "generator", c, f"correct r{k}")
            result.notes += notes
            await emit("corrected", round=k, items=len({o.item_id for o in item_fix}))
        feedback = trans_fix

    result.items = items
    for i in items:
        if i.status != "prescribed":
            result.heard_not_prescribed.append(i)
            continue
        objs = final.get(i.item_id, [])
        states = {LineState.supported}
        for o in objs:
            if o.kind == "rule_conflict":
                states.add(LineState.conflict)
            elif o.kind == "mistranslation":
                states.add(LineState.uncertain_translation)
            elif o.blocking:
                states.add(LineState.proposal)
        result.lines.append(PatientLine(
            item_id=i.item_id, language=language, text=translations.get(i.item_id, ""),
            source_en=sources.get(i.item_id, ""), back_translation=backs.get(i.item_id),
            span_ids=i.source_span_ids, rule_ids=rule_ids.get(i.item_id, []),
            state=resolve_state(states), objections=objs))
    result.seconds = time.perf_counter() - t0
    return result


def gold_items(session_id: str) -> list[Item]:
    """The approved slots as extracted items: the clean starting point the evaluation injects errors into."""
    slots = json.loads((DATA_DIR / "sessions" / f"{session_id}.slots.json").read_text(encoding="utf-8"))
    key = json.loads((DATA_DIR / "sessions" / f"{session_id}.gold.json").read_text(encoding="utf-8"))
    spans = {g["slot"]: g["span_ids"] for g in key["items"]}
    cat = load_catalog()
    return [Item(item_id=s["slot"], exercise=cat[s["exercise_id"]]["en"], exercise_id=s["exercise_id"],
                 side=s["side"], dose=s["dose"], frequency=s["frequency"], cautions=s["cautions"],
                 source_span_ids=spans[s["slot"]]) for s in slots["prescribed"]]
