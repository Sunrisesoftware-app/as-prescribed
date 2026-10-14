"""The falsifier: a model of a different family than the generator (adr.ap.002) looks for what is
wrong, never for what is right. Two checks, typed objections from both:

1. Fidelity: every prescribed item against the whole transcript (entailment, side, dose, frequency,
   dropped cautions, items the therapist never prescribed, postponed or withdrew).
2. Translation: it translates each patient line back into English without seeing the original's
   wording first, then lists every difference in meaning.

It does not judge whether an exercise suits the patient: that is the therapist's decision (adr.ap.001).
"""
import json

from .config import Endpoint
from .extract import ChatFn
from .llm import Completion, chat, extract_json
from .schemas import CORRECTABLE, Item, Objection, Span
from .translate import LANG_NAME

SYSTEM = ("You check a physiotherapy home program against the visit transcript. You are strict and literal: "
          "a detail counts as stated only if the therapist says it in the transcript. "
          "You do not judge whether an exercise is suitable or safe; that is the therapist's decision.")

KINDS = """Objection kinds:
- wrong_dose: the dose differs from what the therapist stated, or the therapist stated none
- wrong_frequency: the frequency differs from what the therapist stated, or the therapist stated none
- wrong_side: the side differs from what the therapist stated
- dropped_caution: the therapist stated a caution for this exercise that the item lacks
- invented_item: the therapist never prescribed this exercise, or postponed it, or left it out
- not_entailed: anything else in the item that the transcript does not state"""


async def check_items(spans: list[Span], items: list[Item], ep: Endpoint, *,
                      chat_fn: ChatFn = chat) -> tuple[list[Objection], Completion]:
    transcript = "\n".join(f"{s.span_id} | {s.speaker} | {s.text}" for s in spans)
    shown = [i.model_dump(include={"item_id", "exercise", "side", "dose", "frequency", "cautions", "source_span_ids"})
             for i in items]
    user = (f"Transcript (span_id | speaker | text):\n{transcript}\n\n"
            f"Home program items:\n{json.dumps(shown, ensure_ascii=False)}\n\n{KINDS}\n\n"
            "Check every item against the whole transcript. Report only real differences; an item that matches "
            "gets an empty list.\n"
            'Answer with one JSON object only: {"checks": [{"item_id": "...", "objections": '
            '[{"kind": "...", "detail": "<what the transcript says instead, citing span ids>"}]}]}')
    c = await chat_fn(ep, [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
                      max_tokens=2500, temperature=0.0)
    data = extract_json(c.content) or {}
    ids = {i.item_id for i in items}
    out = []
    for row in data.get("checks") or []:
        if not isinstance(row, dict) or row.get("item_id") not in ids:
            continue
        for o in row.get("objections") or []:
            if isinstance(o, dict) and o.get("kind") in CORRECTABLE:
                out.append(Objection(item_id=row["item_id"], kind=o["kind"], source="falsifier",
                                     detail=str(o.get("detail") or "")[:500]))
    if not data:
        out.append(Objection(item_id="*", kind="not_entailed", source="falsifier", blocking=False,
                             detail="the falsifier's answer could not be read; nothing was checked this round"))
    return out, c


async def check_translations(source: dict[str, str], translated: dict[str, str], language: str, ep: Endpoint, *,
                             chat_fn: ChatFn = chat) -> tuple[dict[str, str], list[Objection], Completion]:
    """Back-translations by item id, and a mistranslation objection for every line whose meaning differs."""
    rows = [{"item_id": k, LANG_NAME[language].lower(): translated[k], "english_original": source[k]}
            for k in translated]
    user = (f"Each row has a line in {LANG_NAME[language]} and the English original it was translated from.\n"
            f"First translate the {LANG_NAME[language]} line back into English literally, as if you had not seen "
            "the original. Then compare your back-translation with the original and list every difference in "
            "meaning: the exercise, the side, any number, how often, a caution, or anything added or left out. "
            "Differences in wording that keep the meaning are not differences.\n\n"
            f"Rows:\n{json.dumps(rows, ensure_ascii=False)}\n\n"
            'Answer with one JSON object only: {"lines": [{"item_id": "...", "back_translation": "...", '
            '"same_meaning": true, "differences": ""}]}')
    c = await chat_fn(ep, [{"role": "system", "content": "You check translations of patient instructions. "
                                                          "You are strict about meaning and relaxed about wording."},
                           {"role": "user", "content": user}], max_tokens=3000, temperature=0.0)
    data = extract_json(c.content) or {}
    back, out = {}, []
    for row in data.get("lines") or []:
        if not isinstance(row, dict) or row.get("item_id") not in translated:
            continue
        back[row["item_id"]] = str(row.get("back_translation") or "")
        if row.get("same_meaning") is False:
            out.append(Objection(item_id=row["item_id"], kind="mistranslation", source="falsifier",
                                 detail=str(row.get("differences") or "meaning differs")[:500]))
    for k in translated:
        if k not in back:
            out.append(Objection(item_id=k, kind="mistranslation", source="falsifier",
                                 detail="the falsifier did not return a back-translation for this line"))
    return back, out, c
