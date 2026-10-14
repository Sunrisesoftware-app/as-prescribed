"""Error-injection evaluation (handoff v3 §6), pre-registered before the first run.

Every run starts from the approved slots of one session (gold_items) with at most one injected error,
so each injection is scored on its own; clean runs measure false alarms. The plan is written to a file
and sealed with its sha256 before any run (the ftuomari pattern from somnus), so it cannot be fitted to
the results afterwards.

Detection is read from ROUND 0 (what the checks and the falsifier raise before any correction); the
final state after the rounds is reported beside it. Deterministic checks and the falsifier are counted
separately, because a number the transcript does not contain is caught without any model.
"""
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from .pipeline import SessionResult, gold_items
from .rules import load_catalog
from .schemas import Item

TYPES = ["wrong_dose_or_frequency", "wrong_side", "invented_item", "dropped_caution", "contraindicated",
         "mistranslation"]

# The objection kinds that count as detecting each type on the injected line.
DETECTS = {
    "wrong_dose_or_frequency": {"wrong_dose", "wrong_frequency", "not_entailed"},
    "wrong_side": {"wrong_side", "not_entailed"},
    "invented_item": {"invented_item", "not_entailed", "wrong_dose", "wrong_frequency", "wrong_side"},
    "dropped_caution": {"dropped_caution", "not_entailed"},
    "contraindicated": {"rule_conflict"},
    "mistranslation": {"mistranslation"},
}
PRIMARY = {"wrong_dose_or_frequency": {"wrong_dose", "wrong_frequency"}, "wrong_side": {"wrong_side"},
           "invented_item": {"invented_item"}, "dropped_caution": {"dropped_caution"},
           "contraindicated": {"rule_conflict"}, "mistranslation": {"mistranslation"}}

# Objections the approved slots are expected to raise; anything else on a clean line is a false alarm.
EXPECTED = {("S2.5", "rule_conflict"), ("S3.4", "incomplete")}
EXPECTED_KINDS_ANYWHERE = {"no_catalogue_match"}  # non-blocking, informational

LANG = {"S1": "ar", "S2": "uk", "S3": "ar"}


def _set(slot, **fields):
    return {"op": "set", "item_id": slot, "fields": fields}


def _add(item_id, exercise_id, side, dose, frequency, spans):
    return {"op": "add", "item_id": item_id, "fields": {"exercise_id": exercise_id, "side": side, "dose": dose,
                                                        "frequency": frequency, "source_span_ids": spans}}


def _tr(item_id, how):
    return {"op": "translation", "item_id": item_id, "how": how}


INJECTIONS = [
    # wrong dose or frequency: three with a number the spans lack (deterministic), three the falsifier must read
    ("A1", "S1", "wrong_dose_or_frequency", _set("S1.1", dose="3 x 15")),
    ("A2", "S1", "wrong_dose_or_frequency", _set("S1.4", frequency="every day")),
    ("A3", "S2", "wrong_dose_or_frequency", _set("S2.3", dose="2 x 12")),
    ("A4", "S2", "wrong_dose_or_frequency", _set("S2.1", frequency="every evening")),
    ("A5", "S3", "wrong_dose_or_frequency", _set("S3.3", frequency="every other day")),
    ("A6", "S3", "wrong_dose_or_frequency", _set("S3.1", dose="5 minutes")),
    # wrong side: two where the cited spans also name the other side, so only the falsifier can tell
    ("B1", "S1", "wrong_side", _set("S1.2", side="left")),
    ("B2", "S1", "wrong_side", _set("S1.5", side="left")),
    ("B3", "S2", "wrong_side", _set("S2.2", side="left")),
    ("B4", "S2", "wrong_side", _set("S2.3", side="right")),
    ("B5", "S3", "wrong_side", _set("S3.2", side="left")),
    # invented exercise: the cited spans hold matching numbers where possible, so the checks pass
    ("C1", "S1", "invented_item", _add("X1", "ex.heel_raise", "both", "3 x 10", "every day", ["s034"])),
    ("C2", "S1", "invented_item", _add("X2", "ex.mini_squat", "both", "2 x 10", "every day", ["s024"])),
    ("C3", "S2", "invented_item", _add("X3", "ex.clamshell", "left", "3 x 12", "every day", ["s016", "s017"])),
    ("C4", "S2", "invented_item", _add("X4", "ex.straight_leg_raise", "left", "3 x 12", "every day", ["s021"])),
    ("C5", "S3", "invented_item", _add("X5", "ex.wall_slide", None, None, None, ["s027"])),
    # dropped caution: every slot with a therapist-stated caution
    ("D1", "S1", "dropped_caution", _set("S1.2", cautions=[])),
    ("D2", "S1", "dropped_caution", _set("S1.3", cautions=[])),
    ("D3", "S1", "dropped_caution", _set("S1.4", cautions=[])),
    ("D4", "S2", "dropped_caution", _set("S2.5", cautions=[])),
    ("D5", "S3", "dropped_caution", _set("S3.2", cautions=[])),
    # contraindicated: an item a documented restriction blocks
    ("E1", "S2", "contraindicated", _add("X6", "ex.step_up", "left", "2 x 10", "every day", ["s021"])),
    ("E2", "S2", "contraindicated", _add("X7", "ex.kneeling_hip_stretch", "left", "3 x 30 seconds", "every day",
                                         ["s025"])),
    ("E3", "S2", "contraindicated", _add("X8", "ex.heel_raise_single", "left", "3 x 12", "every day", ["s021"])),
    ("E4", "S2", "contraindicated", _add("X9", "ex.cat_camel", "none", "2 x 10", "every day", ["s013"])),
    ("E5", "S3", "contraindicated", _add("X10", "ex.sit_up", "none", "2 x 15", "every day", ["s021", "s022"])),
    # mistranslation in round 0: two number changes (deterministic), two side swaps and two dropped final
    # sentences (the falsifier must read the patient language)
    ("F1", "S1", "mistranslation", _tr("S1.1", "change_number")),
    ("F2", "S2", "mistranslation", _tr("S2.4", "change_number")),
    ("F3", "S1", "mistranslation", _tr("S1.3", "swap_side")),
    ("F4", "S2", "mistranslation", _tr("S2.3", "swap_side")),
    ("F5", "S3", "mistranslation", _tr("S3.2", "drop_last_sentence")),
    ("F6", "S1", "mistranslation", _tr("S1.4", "drop_last_sentence")),
]
# Injections no deterministic check can catch: only the falsifier reading the transcript or the patient
# language can. Recall is reported for this subset separately, so the checks do not flatter the model.
FALSIFIER_ONLY = {"A2", "A4", "A5", "B3", "B4", "C2", "C3", "C4", "C5", "D1", "D2", "D3", "D4", "D5",
                  "F3", "F4", "F5", "F6"}

CLEAN_RUNS = [("K1", "S1"), ("K2", "S2"), ("K3", "S3"), ("K4", "S1"), ("K5", "S2"), ("K6", "S3"),
              ("K7", "S1"), ("K8", "S2"), ("K9", "S3")]


def plan() -> dict:
    runs = [{"run": rid, "session": s, "type": t, "injection": inj} for rid, s, t, inj in INJECTIONS]
    runs += [{"run": rid, "session": s, "type": "clean", "injection": None} for rid, s in CLEAN_RUNS]
    return {"version": 1, "runs": runs, "types": TYPES, "detects": {k: sorted(v) for k, v in DETECTS.items()},
            "expected": sorted(EXPECTED), "falsifier_only": sorted(FALSIFIER_ONLY)}


def seal(p: dict) -> str:
    return hashlib.sha256(json.dumps(p, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def injected_items(run: dict) -> list[Item]:
    items = gold_items(run["session"])
    inj = run["injection"]
    if not inj or inj["op"] == "translation":
        return items
    if inj["op"] == "set":
        target = next(i for i in items if i.item_id == inj["item_id"])
        for k, v in inj["fields"].items():
            setattr(target, k, v)
        return items
    f = inj["fields"]
    items.append(Item(item_id=inj["item_id"], exercise=load_catalog()[f["exercise_id"]]["en"], **f))
    return items


# Side words for the swap injection. Arabic: right/left in the forms a translation uses; Ukrainian:
# the adjective stems with their endings, matched as whole words so "вправа" (exercise) is untouched.
_AR = [("اليمنى", "اليسرى"), ("اليمين", "اليسار"), ("الأيمن", "الأيسر"), ("يمنى", "يسرى"), ("يمين", "يسار")]
_UK = re.compile(r"(?<![\w])(прав|лів)(ий|а|у|е|ою|ій|ої|ого|ому|им|ими|і|их)(?![\w])")


def mutate_translation(how: str, text: str) -> str | None:
    """The mutated text, or None when the mutation found nothing to change (recorded, not scored)."""
    if how == "change_number":
        m = re.search(r"[0-9٠-٩۰-۹]+", text)
        if not m:
            return None
        old = m.group(0)
        trans = str.maketrans("0123456789٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "1234567891١٢٣٤٥٦٧٨٩١۱۲۳۴۵۶۷۸۹۱")
        return text[:m.start()] + old.translate(trans) + text[m.end():]
    if how == "swap_side":
        for a, b in _AR:
            if a in text or b in text:
                return text.replace(a, "\0").replace(b, a).replace("\0", b)
        if _UK.search(text):
            return _UK.sub(lambda m: ("лів" if m[1] == "прав" else "прав") + m[2], text)
        return None
    if how == "drop_last_sentence":
        parts = [p for p in re.split(r"(?<=[.!?؟۔])\s+", text.strip()) if p]
        return " ".join(parts[:-1]) if len(parts) > 1 else None
    raise ValueError(how)


@dataclass
class Observation:
    run: str
    session: str
    type: str
    item_id: str | None
    injected: bool          # False when a translation mutation found nothing to change
    detected: bool
    primary_kind: bool
    by_checks: bool
    by_falsifier: bool
    final_state: str | None


def observe(run: dict, result: SessionResult, injected: bool = True) -> tuple[Observation | None, list[dict]]:
    """The injection's observation, and one false-alarm record per clean line of the run."""
    r0 = result.rounds[0].raised if result.rounds else []
    inj = run["injection"]
    target = inj["item_id"] if inj else None
    final = {line.item_id: line.state.value for line in result.lines}
    obs = None
    if inj:
        mine = [o for o in r0 if o["item_id"] == target and o["blocking"] and o["kind"] in DETECTS[run["type"]]]
        obs = Observation(run["run"], run["session"], run["type"], target, injected, bool(mine),
                          any(o["kind"] in PRIMARY[run["type"]] for o in mine),
                          any(o["source"] in ("checks", "rules") for o in mine),
                          any(o["source"] == "falsifier" for o in mine),
                          final.get(target, "removed"))
    clean = []
    for line in result.lines:
        if line.item_id == target:
            continue
        unexpected = [o for o in r0 if o["item_id"] == line.item_id and o["blocking"]
                      and (line.item_id, o["kind"]) not in EXPECTED and o["kind"] not in EXPECTED_KINDS_ANYWHERE]
        clean.append({"run": run["run"], "session": run["session"], "item_id": line.item_id,
                      "false_alarm": bool(unexpected), "kinds": sorted({o["kind"] for o in unexpected}),
                      "sources": sorted({o["source"] for o in unexpected})})
    return obs, clean


def _rate(xs: list[bool]) -> float | None:
    return round(sum(xs) / len(xs), 3) if xs else None


def score(observations: list[dict], clean: list[dict], runs: list[dict]) -> dict:
    by_type: dict[str, dict] = {}
    for t in TYPES:
        rows = [o for o in observations if o["type"] == t and o["injected"]]
        for lang in ("ar", "uk", "all"):
            sub = rows if lang == "all" else [o for o in rows if LANG[o["session"]] == lang]
            if not sub:
                continue
            by_type.setdefault(t, {})[lang] = {
                "n": len(sub), "recall": round(sum(o["detected"] for o in sub) / len(sub), 3),
                "primary_kind": round(sum(o["primary_kind"] for o in sub) / len(sub), 3),
                "falsifier_caught": sum(o["by_falsifier"] for o in sub),
                "only_checks_caught": sum(o["by_checks"] and not o["by_falsifier"] for o in sub)}
        by_type.setdefault(t, {})["final_states"] = dict(Counter(o["final_state"] for o in rows))
    all_inj = [o for o in observations if o["injected"]]
    lines_fa = list(clean)
    distinct: dict[tuple, list[bool]] = defaultdict(list)
    for c in lines_fa:
        distinct[(c["session"], c["item_id"])].append(c["false_alarm"])
    per_round = defaultdict(list)
    for r in runs:
        for k, n in enumerate(r["objections_per_round"]):
            per_round[k].append(n)
    secs = [r["seconds"] for r in runs]
    tps = defaultdict(list)
    for r in runs:
        for role, calls in r["calls"].items():
            tps[role] += [c["tokens_per_s"] for c in calls if c.get("tokens_per_s")]
    return {
        "injections": {"planned": len(observations), "applied": len(all_inj),
                       "not_applied": [o["run"] for o in observations if not o["injected"]]},
        "recall_overall": round(sum(o["detected"] for o in all_inj) / len(all_inj), 3) if all_inj else None,
        "recall_falsifier_only": _rate([o["detected"] for o in all_inj if o["run"] in FALSIFIER_ONLY]),
        "recall_deterministic": _rate([o["detected"] for o in all_inj if o["run"] not in FALSIFIER_ONLY]),
        "by_type": by_type,
        "false_alarms": {"line_observations": len(lines_fa),
                         "rate": round(sum(c["false_alarm"] for c in lines_fa) / len(lines_fa), 3) if lines_fa else None,
                         "distinct_lines_ever_flagged": sum(any(v) for v in distinct.values()),
                         "distinct_lines": len(distinct),
                         "kinds": dict(Counter(k for c in lines_fa for k in c["kinds"]))},
        "objections_per_round_mean": {k: round(sum(v) / len(v), 2) for k, v in sorted(per_round.items())},
        "seconds": {"median": sorted(secs)[len(secs) // 2] if secs else None, "max": max(secs) if secs else None},
        "tokens_per_s_median": {role: sorted(v)[len(v) // 2] for role, v in tps.items() if v},
    }


def write_plan(path: Path) -> str:
    p = plan()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(p, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return seal(p)
