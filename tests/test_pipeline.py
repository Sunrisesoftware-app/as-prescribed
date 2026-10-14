"""The rounds without a model: a fake LLM answers each kind of call (extract, check, translate,
back-check, correct) by its system prompt, so the loop, the states and the stopping rule are tested
on the real sessions and the approved slots."""
import json
import re

from asprescribed import falsify, translate
from asprescribed.config import Endpoint
from asprescribed.extract import SYSTEM as EXTRACT_SYSTEM
from asprescribed.llm import Completion
from asprescribed.pipeline import CORRECT_SYSTEM, gold_items, run_session
from asprescribed.program import compose
from asprescribed.schemas import LineState

GEN = Endpoint("generator", "http://gen/v1", "gen", None, False, 5.0)
FAL = Endpoint("falsifier", "http://fal/v1", "fal", None, False, 5.0)


class FakeLLM:
    def __init__(self, *, item_objections=None, corrections=None, drop_digit_once=None, meaning_differs=None):
        self.item_objections = item_objections or []   # list per check call: {item_id: [(kind, detail)]}
        self.corrections = corrections or {}            # item_id -> fields to change when asked to correct
        self.drop_digit_once = set(drop_digit_once or [])
        self.meaning_differs = meaning_differs or {}    # item_id -> how many back-checks still differ
        self.calls = []

    async def __call__(self, ep, messages, **kw):
        system, user = messages[0]["content"], messages[-1]["content"]
        self.calls.append((ep.role, system[:30]))
        if system == EXTRACT_SYSTEM:
            body = {"items": []}
        elif system == falsify.SYSTEM:
            per = self.item_objections.pop(0) if self.item_objections else {}
            body = {"checks": [{"item_id": k, "objections": [{"kind": a, "detail": b} for a, b in v]}
                               for k, v in per.items()]}
        elif system == translate.SYSTEM:
            rows = json.loads(re.search(r"Lines:\n(\[.*\])\n", user, re.DOTALL).group(1))
            out = []
            for r in rows:
                # Follows the instruction to write counts as digits, as the real translator is told to.
                text = "TR " + re.sub(r"\b(once|twice|three times)\b",
                                      lambda m: {"once": "1 time", "twice": "2 times", "three times": "3 times"}[m[1]],
                                      r["text"])
                if r["item_id"] in self.drop_digit_once:
                    self.drop_digit_once.discard(r["item_id"])
                    text = re.sub(r"\d+", "", text, count=1)
                out.append({"item_id": r["item_id"], "text": text})
            body = {"lines": out}
        elif system.startswith("You check translations"):
            rows = json.loads(re.search(r"Rows:\n(\[.*\])\n", user, re.DOTALL).group(1))
            out = []
            for r in rows:
                left = self.meaning_differs.get(r["item_id"], 0)
                if left:
                    self.meaning_differs[r["item_id"]] = left - 1
                out.append({"item_id": r["item_id"], "back_translation": r["english_original"],
                            "same_meaning": not left, "differences": "side differs" if left else ""})
            body = {"lines": out}
        elif system == CORRECT_SYSTEM:
            items = json.loads(re.search(r"Items:\n(\[.*\])\n\nA checker", user, re.DOTALL).group(1))
            body = {"items": [{**i, **self.corrections.get(i["item_id"], {})} for i in items]}
        else:
            raise AssertionError(system)
        return Completion(content=json.dumps(body), model=ep.model, completion_tokens=50, seconds=0.01,
                          tokens_per_s=5000.0)


def states(result):
    return {line.item_id: line.state for line in result.lines}


async def test_s1_clean_slots_are_all_supported_in_one_round():
    r = await run_session("S1", GEN, FAL, chat_fn=FakeLLM(), items=gold_items("S1"))
    assert set(states(r).values()) == {LineState.supported}
    assert [x.correctable for x in r.rounds] == [0]
    assert r.language == "ar" and all(line.text.startswith("TR ") for line in r.lines)


async def test_s2_conflict_halts_the_prosthesis_line_only():
    r = await run_session("S2", GEN, FAL, chat_fn=FakeLLM(), items=gold_items("S2"))
    s = states(r)
    assert s["S2.5"] == LineState.conflict
    assert {k for k, v in s.items() if v != LineState.supported} == {"S2.5"}
    line = next(x for x in r.lines if x.item_id == "S2.5")
    assert line.rule_ids == ["R04", "R09"]


async def test_s3_incomplete_stretch_is_a_proposal_with_the_records_caution():
    r = await run_session("S3", GEN, FAL, chat_fn=FakeLLM(), items=gold_items("S3"))
    assert states(r)["S3.4"] == LineState.proposal
    line = next(x for x in r.lines if x.item_id == "S3.4")
    assert "From your records: Bend from the hips" in line.source_en
    assert "side not stated" in line.source_en and "Dose not stated" in line.source_en


async def test_injected_wrong_dose_is_caught_and_corrected():
    items = gold_items("S1")
    items[1].dose = "3 x 15"                       # S1.2: the transcript says twelve
    fake = FakeLLM(corrections={"S1.2": {"dose": "3 x 12"}})
    r = await run_session("S1", GEN, FAL, chat_fn=fake, items=items)
    assert [x.correctable for x in r.rounds] == [1, 0]
    assert states(r)["S1.2"] == LineState.supported


async def test_objection_the_generator_does_not_fix_ends_as_proposal():
    fake = FakeLLM(item_objections=[{"S1.3": [("wrong_side", "s024 says right")]}] * 3)
    r = await run_session("S1", GEN, FAL, chat_fn=fake, items=gold_items("S1"), max_rounds=3)
    assert len(r.rounds) == 3 and states(r)["S1.3"] == LineState.proposal
    assert any(o.kind == "wrong_side" for o in next(x for x in r.lines if x.item_id == "S1.3").objections)


async def test_dropped_digit_in_translation_is_retranslated():
    fake = FakeLLM(drop_digit_once={"S1.1"})
    r = await run_session("S1", GEN, FAL, chat_fn=fake, items=gold_items("S1"))
    assert [x.correctable for x in r.rounds] == [1, 0]
    assert states(r)["S1.1"] == LineState.supported


async def test_meaning_difference_that_persists_is_uncertain_translation():
    fake = FakeLLM(meaning_differs={"S1.5": 5})
    r = await run_session("S1", GEN, FAL, chat_fn=fake, items=gold_items("S1"), max_rounds=2)
    assert states(r)["S1.5"] == LineState.uncertain_translation


def test_compose_names_the_side_in_the_catalogue_sentence():
    item = gold_items("S1")[2]  # S1.3 step-up, right
    line = compose(item, [])
    assert line.startswith("Step-up (right). Step up onto the bottom stair leading with your right leg")
    assert "2 × 10, every day." in line and "Hold the stair rail." in line


def test_number_check_requires_dose_digits_but_allows_number_words_elsewhere():
    from asprescribed.translate import number_check
    src = "Single-leg stance (left). Stand on one leg next to a counter. 3 x 30 seconds, every day."
    assert number_check("x", src, "TR стати на одну ногу 3 x 30 секунд", {3, 30}) == []
    assert number_check("x", src, "TR ٣ x ٣٠", {3, 30}) == []                      # Arabic-Indic digits
    assert [o.detail for o in number_check("x", src, "TR 3 x 20", {3, 30})] == [
        "numbers differ from the English line (missing 30; added 20)"]


def test_canonical_dose_and_the_arabic_dual():
    from asprescribed.program import canonical
    from asprescribed.translate import digits_in
    assert canonical("Two sets of ten") == "2 × 10"
    assert canonical("3 x 12") == "3 × 12"
    assert canonical("three times thirty seconds") == "3 times 30 seconds"
    assert canonical("twice a day") == "2 times a day"
    assert digits_in("مجموعتان من 10") == {2.0, 10.0}
    assert digits_in("двічі на день") == {2.0}
