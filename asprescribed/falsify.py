"""The falsifier: a model of a different family than the generator (adr.ap.002) looks for what is
wrong, never for what is right. Two checks, typed objections from both:

1. Fidelity: every prescribed item against the whole transcript (entailment, side, dose, frequency,
   dropped cautions, items the therapist never prescribed, postponed or withdrew).
2. Translation: it translates each patient line back into English without seeing the original's
   wording first, then lists every difference in meaning.

It does not judge whether an exercise suits the patient: that is the therapist's decision (adr.ap.001).
"""
import json
import re

from .config import Endpoint
from .extract import ChatFn
from .llm import Completion, chat, extract_json
from .program import canonical
from .schemas import CORRECTABLE, Item, Objection, Span
from .translate import LANG_NAME

SYSTEM = ("You check a physiotherapy home program against the visit transcript. You are strict and literal: "
          "a detail counts as stated only if the therapist says it in the transcript. "
          "You do not judge whether an exercise is suitable or safe; that is the therapist's decision.")

KINDS = """Objection kinds:
- wrong_dose: the dose differs from what the therapist stated, or the therapist stated none
- wrong_frequency: the frequency differs from what the therapist stated, or the therapist stated none
- wrong_side: the side differs from what the therapist stated
- invented_item: the therapist never prescribed this exercise, or postponed it, or left it out
- not_entailed: anything else in the item that the transcript does not state

How to read the items: a dose written "N × M" means N sets of M, and a number written as a word or as digits
is the same number ("three sets of twelve" is "3 × 12"). Compare how often word for word: "every day",
"every other day", "every evening" and "5 days a week" are all different.

Not objections: an item does not have to repeat how to do the exercise, where to put the band or why it
helps; leaving out such explanations is fine. Report only what the item states wrongly.

Cautions: for every item, also copy word for word each warning the therapist gave about that exercise (what
to do or avoid for safety) into therapist_cautions, or an empty list. Do not judge them; just copy them."""


_STOP = {"the", "and", "you", "your", "when", "with", "this", "that", "for", "always", "just", "does", "can",
          "will", "are", "not", "dont", "don", "please", "make", "sure", "then", "while", "into", "from"}


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", (text or "").lower()) if len(w) > 2 and w not in _STOP}


def _covered(quote: str, text: str, share: float) -> bool:
    q = _words(quote)
    return bool(q) and len(q & _words(text)) / len(q) >= share


def caution_objections(item: Item, quotes: list[str], spans: list[Span]) -> list[Objection]:
    """A caution the falsifier quotes that the item lacks. The comparison is code, not the model's opinion:
    a quote the therapist never said is ignored, and a quote the item's cautions already cover is fine."""
    therapist = " ".join(s.text for s in spans if s.speaker == "therapist")
    mine = " ".join(item.cautions)
    out = []
    for q in quotes:
        if isinstance(q, str) and _covered(q, therapist, 0.8) and not _covered(q, mine, 0.6):
            out.append(Objection(item_id=item.item_id, kind="dropped_caution", source="falsifier",
                                 detail=f"the therapist said: {q.strip()[:300]}"))
    return out


async def check_items(spans: list[Span], items: list[Item], ep: Endpoint, *,
                      chat_fn: ChatFn = chat) -> tuple[list[Objection], Completion]:
    transcript = "\n".join(f"{s.span_id} | {s.speaker} | {s.text}" for s in spans)
    shown = [{**i.model_dump(include={"item_id", "exercise", "side", "cautions", "source_span_ids"}),
              "dose": canonical(i.dose) if i.dose else None,
              "frequency": canonical(i.frequency) if i.frequency else None} for i in items]
    user = (f"Transcript (span_id | speaker | text):\n{transcript}\n\n"
            f"Home program items:\n{json.dumps(shown, ensure_ascii=False)}\n\n{KINDS}\n\n"
            "Check every item against the whole transcript. Report only real differences; an item that matches "
            "gets an empty list.\n"
            'Answer with one JSON object only: {"checks": [{"item_id": "...", "objections": '
            '[{"kind": "...", "detail": "<what the transcript says instead, citing span ids>"}], '
            '"therapist_cautions": ["<exact words>"]}]}')
    c = await chat_fn(ep, [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
                      max_tokens=2500, temperature=0.0)
    data = extract_json(c.content) or {}
    by_id = {i.item_id: i for i in items}
    out = []
    for row in data.get("checks") or []:
        if not isinstance(row, dict) or row.get("item_id") not in by_id:
            continue
        out += caution_objections(by_id[row["item_id"]], row.get("therapist_cautions") or [], spans)
        for o in row.get("objections") or []:
            if isinstance(o, dict) and o.get("kind") in CORRECTABLE - {"dropped_caution"}:
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
