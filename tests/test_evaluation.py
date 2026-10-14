"""The evaluation harness without a model: injections apply, translation mutations change what they
claim to, and observe() reads detections from round 0 and false alarms from the clean lines."""
from test_pipeline import FAL, GEN, FakeLLM

from asprescribed.evaluation import INJECTIONS, injected_items, mutate_translation, observe, plan, score, seal
from asprescribed.pipeline import gold_items, run_session


def run_of(rid):
    return next(r for r in plan()["runs"] if r["run"] == rid)


def test_plan_is_stable_and_complete():
    p = plan()
    assert seal(p) == seal(plan())
    assert len([r for r in p["runs"] if r["injection"]]) == len(INJECTIONS) == 32
    assert {r["type"] for r in p["runs"]} == set(p["types"]) | {"clean"}


def test_every_item_injection_changes_or_adds_exactly_one_item():
    for r in plan()["runs"]:
        inj = r["injection"]
        if not inj or inj["op"] == "translation":
            continue
        gold = {i.item_id: i.model_dump() for i in gold_items(r["session"])}
        got = {i.item_id: i.model_dump() for i in injected_items(r)}
        changed = [k for k in got if gold.get(k) != got[k]]
        assert changed == [inj["item_id"]], r["run"]


def test_translation_mutations():
    assert mutate_translation("change_number", "قف ٣ x ١٠ يوميا") == "قف ٤ x ١٠ يوميا"
    assert mutate_translation("change_number", "3 x 12 щодня") == "4 x 12 щодня"
    assert mutate_translation("swap_side", "على الساق اليمنى") == "على الساق اليسرى"
    assert mutate_translation("swap_side", "Підніміть ліву ногу. Ця вправа проста.") == \
        "Підніміть праву ногу. Ця вправа проста."
    assert mutate_translation("drop_last_sentence", "First. Second. Keep the elbow in.") == "First. Second."
    assert mutate_translation("swap_side", "no side here") is None


async def _observe(rid, **fake):
    r = run_of(rid)
    hook = None
    if r["injection"]["op"] == "translation":
        def hook(iid, text):
            return mutate_translation(r["injection"]["how"], text) or text if iid == r["injection"]["item_id"] else text
    res = await run_session(r["session"], GEN, FAL, chat_fn=FakeLLM(**fake), items=injected_items(r),
                            translation_hook=hook)
    return observe(r, res)


async def test_number_injection_is_caught_by_the_checks_alone():
    obs, clean = await _observe("A1")
    assert obs.detected and obs.by_checks and not obs.by_falsifier and obs.final_state == "proposal"
    assert not any(c["false_alarm"] for c in clean)


async def test_side_injection_the_spans_cannot_settle_needs_the_falsifier():
    obs, _ = await _observe("B3")                        # s012 names the left leg too
    assert not obs.detected
    obs, _ = await _observe("B3", item_objections=[{"S2.2": [("wrong_side", "s013 says right")]}])
    assert obs.detected and obs.by_falsifier and obs.primary_kind


async def test_contraindicated_item_is_caught_by_the_rules():
    obs, _ = await _observe("E1")
    assert obs.detected and obs.by_checks and obs.final_state == "conflict"


async def test_number_mutation_in_translation_is_caught():
    obs, _ = await _observe("F1")
    assert obs.detected and obs.final_state == "supported"   # re-translated in round 1


def test_score_shape():
    obs = [{"run": "A1", "session": "S1", "type": "wrong_dose_or_frequency", "item_id": "S1.1", "injected": True,
            "detected": True, "primary_kind": True, "by_checks": True, "by_falsifier": False, "final_state": "proposal"}]
    clean = [{"run": "A1", "session": "S1", "item_id": "S1.2", "false_alarm": False, "kinds": [], "sources": []}]
    s = score(obs, clean, [{"objections_per_round": [1, 0], "seconds": 10.0, "calls": {"generator": []}}])
    assert s["recall_overall"] == 1.0 and s["false_alarms"]["rate"] == 0.0
    assert s["by_type"]["wrong_dose_or_frequency"]["ar"]["only_checks_caught"] == 1


async def test_falsifier_only_injections_pass_every_deterministic_check():
    """With a falsifier that raises nothing, none of these may be detected: else the subset is mislabelled."""
    from asprescribed.evaluation import FALSIFIER_ONLY
    for rid in sorted(FALSIFIER_ONLY):
        obs, _ = await _observe(rid)
        assert not obs.detected, rid


async def test_deterministic_injections_are_caught_without_a_falsifier():
    from asprescribed.evaluation import FALSIFIER_ONLY
    for rid in [r for r, *_ in INJECTIONS if r not in FALSIFIER_ONLY]:
        obs, _ = await _observe(rid)
        assert obs.detected, rid
