"""The written dialogues say exactly what the approved slots say: every number in a slot's dose and
frequency and its side appear in the spans the answer key cites, and S3.4 stays vague on purpose."""
import json

import pytest

from asprescribed.config import DATA_DIR
from asprescribed.extract import numbers_in
from asprescribed.ingest import load_spans

SESSIONS = ["S1", "S2", "S3"]


def _load(sid):
    spans = {s.span_id: s for s in load_spans(DATA_DIR / "sessions" / f"{sid}.transcript.jsonl")}
    gold = json.loads((DATA_DIR / "sessions" / f"{sid}.gold.json").read_text(encoding="utf-8"))
    slots = json.loads((DATA_DIR / "sessions" / f"{sid}.slots.json").read_text(encoding="utf-8"))
    by_slot = {s["slot"]: s for s in slots["prescribed"]} | {t["slot"]: t for t in slots["traps"]}
    return spans, gold, by_slot


CASES = [(sid, g["slot"]) for sid in SESSIONS for g in _load(sid)[1]["items"]]


@pytest.mark.parametrize("sid", SESSIONS)
def test_key_covers_every_slot_and_trap(sid):
    _, gold, by_slot = _load(sid)
    assert {g["slot"] for g in gold["items"]} == set(by_slot)


@pytest.mark.parametrize("sid,slot", CASES)
def test_cited_spans_state_the_slot(sid, slot):
    spans, gold, by_slot = _load(sid)
    g = next(i for i in gold["items"] if i["slot"] == slot)
    assert all(s in spans for s in g["span_ids"])
    assert any(spans[s].speaker == "therapist" for s in g["span_ids"])
    text = " ".join(spans[s].text for s in g["span_ids"])
    s = by_slot[slot]
    if g["status"] != "prescribed":
        return
    for fld in ("dose", "frequency"):
        assert numbers_in(s[fld] or "") <= numbers_in(text), f"{slot} {fld}"
    if s["side"] in ("left", "right"):
        assert s["side"] in text.lower(), slot
    for caution in s["cautions"]:
        assert caution.rstrip(".").lower()[:25] in text.lower(), f"{slot} caution"


def test_s3_4_stays_vague():
    spans, gold, _ = _load("S3")
    g = next(i for i in gold["items"] if i["slot"] == "S3.4")
    text = " ".join(spans[s].text for s in g["span_ids"]).lower()
    assert numbers_in(text) == set()
    assert "left" not in text and "right" not in text
