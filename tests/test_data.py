"""The clinical drafts hold together mechanically before any human reads them: every tag exists,
every rule names a known condition and tag, every slot names a catalogued exercise, and the
rule engine produces exactly the state each slot expects."""
import json

import pytest

from asprescribed.config import DATA_DIR
from asprescribed.rules import check, item_tags, load_catalog, load_profile, load_rules

VOCAB = {t["id"] for t in json.loads((DATA_DIR / "vocabulary.json").read_text(encoding="utf-8"))["tags"]}
RULES_DOC = json.loads((DATA_DIR / "rules.json").read_text(encoding="utf-8"))
CONDITIONS = {c["id"] for c in RULES_DOC["conditions"]}
SESSIONS = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((DATA_DIR / "sessions").glob("*.slots.json"))]


def test_catalogue_tags_exist():
    for ex in load_catalog().values():
        assert set(ex["tags"]) <= VOCAB, ex["id"]
        assert ex["side_mode"] in {"per_side", "bilateral", "none"}


def test_rules_reference_known_conditions_and_tags():
    ids = [r.id for r in load_rules()]
    assert len(ids) == len(set(ids))
    for r in load_rules():
        assert r.condition in CONDITIONS, r.id
        assert r.tag in VOCAB, r.id
        assert r.effect in {"block", "caution"}
        assert r.side in {"left", "right", "any"}


@pytest.mark.parametrize("pid", ["P1", "P2", "P3"])
def test_profiles_use_known_conditions(pid):
    assert set(load_profile(pid).conditions) <= CONDITIONS


def _slots():
    for s in SESSIONS:
        for slot in s["prescribed"]:
            yield s, slot


@pytest.mark.parametrize("session,slot", list(_slots()), ids=lambda v: v.get("slot", "") if isinstance(v, dict) else "")
def test_slot_state_matches_rule_engine(session, slot):
    assert slot["exercise_id"] in load_catalog()
    assert set(slot["extra_tags"]) <= VOCAB
    fired = check(load_profile(session["profile_id"]), item_tags(slot["exercise_id"], slot["extra_tags"]), slot["side"])
    blocked = any(r.effect == "block" for r in fired)
    if slot["expected_state"] == "conflict":
        assert blocked, slot["slot"]
    else:
        assert not blocked, f"{slot['slot']} blocked by {[r.id for r in fired]}"


def test_traps_name_catalogued_exercises():
    for s in SESSIONS:
        for t in s["traps"]:
            assert t["exercise_id"] in load_catalog()


def test_sit_up_trap_would_conflict_for_p3():
    fired = check(load_profile("P3"), item_tags("ex.sit_up"), "none")
    assert [r.id for r in fired if r.effect == "block"] == ["R10"]
