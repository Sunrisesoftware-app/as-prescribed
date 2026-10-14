"""Extract without a model: a fake chat function returns canned answers, so the parsing and the
deterministic checks are tested on their own. The spans are a development fixture, not demo data."""
import json

from asprescribed.config import Endpoint
from asprescribed.extract import check_item, extract, numbers_in, parse_items
from asprescribed.llm import Completion
from asprescribed.schemas import Item, Span

EP = Endpoint("generator", "http://fake/v1", "fake", None, False, 5.0)

SPANS = [
    Span(span_id="s001", speaker="therapist", ts=10, text="Let's start with standing up from a chair, three sets of ten, every day."),
    Span(span_id="s002", speaker="patient", ts=20, text="I also do sit-ups every morning."),
    Span(span_id="s003", speaker="therapist", ts=30, text="Let's leave the sit-ups out for now."),
    Span(span_id="s004", speaker="therapist", ts=40, text="And the band exercise for your right knee, twelve times, every other day."),
    Span(span_id="s005", speaker="therapist", ts=50, text="Wall slides we will add later, not yet."),
]
BY_ID = {s.span_id: s for s in SPANS}


def answer(items: list[dict]) -> str:
    return "<think>reasoning {\"x\": 1}</think>" + json.dumps({"items": items})


def fake_chat(*answers: str):
    queue = list(answers)

    async def chat(ep, messages, **kw):
        return Completion(content=queue.pop(0), model="fake", completion_tokens=10, seconds=0.1, tokens_per_s=100.0)
    return chat


GOOD = [
    {"item_id": "i1", "exercise": "standing up from a chair", "exercise_id": "ex.sit_to_stand", "side": "both",
     "dose": "3 x 10", "frequency": "every day", "cautions": [], "source_span_ids": ["s001"], "status": "prescribed"},
    {"item_id": "i2", "exercise": "sit-ups", "exercise_id": "ex.sit_up", "side": "none", "dose": None,
     "frequency": None, "cautions": [], "source_span_ids": ["s002", "s003"], "status": "withdrawn"},
    {"item_id": "i3", "exercise": "band exercise", "exercise_id": "ex.knee_ext_band", "side": "right",
     "dose": "12", "frequency": "every other day", "cautions": [], "source_span_ids": ["s004"], "status": "prescribed"},
    {"item_id": "i4", "exercise": "wall slides", "exercise_id": "ex.wall_slide", "side": None, "dose": None,
     "frequency": None, "cautions": [], "source_span_ids": ["s005"], "status": "deferred"},
]


def test_numbers_in_reads_digits_and_words():
    assert numbers_in("three sets of ten, twice a day, 30 seconds") == {3, 10, 2, 30}


async def test_clean_answer_has_no_objections():
    r = await extract(SPANS, [], EP, chat_fn=fake_chat(answer(GOOD)))
    assert [i.item_id for i in r.items] == ["i1", "i2", "i3", "i4"]
    assert r.objections == []


async def test_both_sides_without_a_word_for_it_is_flagged():
    # s001 says nothing about sides; the model said "both", which the span does not state
    item = Item(item_id="i1", exercise="x", side="both", dose="3 x 10", source_span_ids=["s001"])
    assert [o.kind for o in check_item(item, BY_ID)] == ["wrong_side"]


async def test_invented_dose_and_wrong_side_are_objections():
    bad = [dict(GOOD[2], dose="3 x 15", side="left")]
    r = await extract(SPANS, [], EP, chat_fn=fake_chat(answer(bad)))
    kinds = sorted(o.kind for o in r.objections)
    assert kinds == ["wrong_dose", "wrong_side"]


async def test_deferred_and_withdrawn_items_are_not_checked_as_prescriptions():
    bad = [dict(GOOD[3], dose="3 x 10")]  # an invented dose on a deferred item is not an objection here
    r = await extract(SPANS, [], EP, chat_fn=fake_chat(answer(bad)))
    assert r.objections == []


def test_unknown_spans_and_catalogue_ids_are_removed_not_invented():
    items, notes = parse_items(answer([dict(GOOD[0], source_span_ids=["s001", "s999"], exercise_id="ex.nope")]),
                               set(BY_ID))
    assert items[0].source_span_ids == ["s001"] and items[0].exercise_id is None
    assert len(notes) == 2


async def test_malformed_answer_is_retried_once_then_previous_items_kept():
    prev = [Item.model_validate(GOOD[0])]
    r = await extract(SPANS, prev, EP, chat_fn=fake_chat("not json", "still not json"))
    assert r.items == prev and len(r.completions) == 2


async def test_malformed_then_good_answer_recovers():
    r = await extract(SPANS, [], EP, chat_fn=fake_chat("oops", answer(GOOD)))
    assert len(r.items) == 4 and len(r.completions) == 2


async def test_item_without_spans_is_not_entailed():
    r = await extract(SPANS, [], EP, chat_fn=fake_chat(answer([dict(GOOD[0], source_span_ids=[])])))
    assert [o.kind for o in r.objections] == ["not_entailed"]
