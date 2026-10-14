"""Translate the composed English lines into the patient's language (generator), and check the numbers
deterministically before any model compares meanings: a number the English line states must appear as
digits in the translation, Arabic-Indic digits included."""
import json
import re

from .config import Endpoint
from .extract import ChatFn, numbers_in
from .llm import Completion, chat, extract_json
from .schemas import Objection

LANG_NAME = {"ar": "Arabic", "uk": "Ukrainian", "en": "English"}

SYSTEM = ("You translate a physiotherapy home program for a patient to read at home. "
          "You translate exactly: you never add, remove, soften or explain anything.")

# Arabic-Indic and Extended Arabic-Indic digits to ASCII.
_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


def digits_in(text: str) -> set[float]:
    return {float(n) for n in re.findall(r"\d+(?:[.,]\d+)?", (text or "").translate(_DIGITS).replace(",", "."))}


def number_check(item_id: str, source_en: str, translated: str, required: set[float]) -> list[Objection]:
    """required: the numbers of the dose and frequency, which must appear as digits. Any other number in
    the English line ('stand on one leg') may stay a word, but a number the English line does not state
    at all is an addition."""
    got = digits_in(translated)
    missing, added = required - got, got - numbers_in(source_en) - required
    if not missing and not added:
        return []
    detail = []
    if missing:
        detail.append("missing " + ", ".join(f"{n:g}" for n in sorted(missing)))
    if added:
        detail.append("added " + ", ".join(f"{n:g}" for n in sorted(added)))
    return [Objection(item_id=item_id, kind="mistranslation", source="checks",
                      detail=f"numbers differ from the English line ({'; '.join(detail)})")]


async def translate(lines: dict[str, str], language: str, ep: Endpoint, *, chat_fn: ChatFn = chat,
                    feedback: dict[str, str] | None = None) -> tuple[dict[str, str], Completion]:
    feedback = feedback or {}
    payload = [{"item_id": k, "text": v, **({"previous_problem": feedback[k]} if k in feedback else {})}
               for k, v in lines.items()]
    user = (f"Translate each line into {LANG_NAME[language]}. Plain words and short sentences. "
            "Write every number with the digits 0-9, including counts such as 'twice' (write 2 times). "
            "Where a line has a previous_problem, the earlier translation had that problem: fix it.\n\n"
            f"Lines:\n{json.dumps(payload, ensure_ascii=False)}\n\n"
            'Answer with one JSON object only: {"lines": [{"item_id": "...", "text": "..."}]}')
    c = await chat_fn(ep, [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
                      max_tokens=3000, temperature=0.0)
    data = extract_json(c.content) or {}
    out = {}
    for row in data.get("lines") or []:
        if isinstance(row, dict) and row.get("item_id") in lines and isinstance(row.get("text"), str):
            out[row["item_id"]] = row["text"].strip()
    return out, c
