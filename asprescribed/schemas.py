"""The pipeline's data types (handoff v3 §2 and §4).

Every patient line has exactly one state; precedence when several apply:
conflict > proposal > uncertain_translation > supported.
"""
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

Side = Literal["left", "right", "both", "none"]
Language = Literal["ar", "uk", "en"]


class Span(BaseModel):
    """One transcript chunk as it arrives during the visit."""
    span_id: str
    speaker: Literal["therapist", "patient"]
    ts: float = Field(description="seconds from the start of the visit")
    text: str


class Item(BaseModel):
    """One item extracted from the transcript. Only status 'prescribed' reaches the program;
    'deferred' (not yet) and 'withdrawn' (left out) are kept so the therapist sees they were heard."""
    item_id: str
    exercise: str
    exercise_id: str | None = None  # catalogue id when matched
    side: Side | None = None
    dose: str | None = None
    frequency: str | None = None
    cautions: list[str] = []
    source_span_ids: list[str] = []
    tags: list[str] = []
    status: Literal["prescribed", "deferred", "withdrawn"] = "prescribed"


class LineState(str, Enum):
    supported = "supported"
    conflict = "conflict"
    proposal = "proposal"
    uncertain_translation = "uncertain_translation"


PRECEDENCE = [LineState.conflict, LineState.proposal, LineState.uncertain_translation, LineState.supported]


def resolve_state(states: set[LineState]) -> LineState:
    for s in PRECEDENCE:
        if s in states:
            return s
    return LineState.supported


ObjectionKind = Literal[
    "not_entailed",       # nothing in the cited spans says this
    "wrong_dose",
    "wrong_frequency",
    "wrong_side",
    "invented_item",
    "dropped_caution",
    "mistranslation",     # back-translation diverges from the item
    "rule_conflict",      # a documented restriction blocks it (raised by the rule engine, not a model)
]


class Objection(BaseModel):
    item_id: str
    kind: ObjectionKind
    detail: str
    blocking: bool = True
    source: Literal["falsifier", "rules", "checks"] = "falsifier"


class PatientLine(BaseModel):
    item_id: str
    language: Language
    text: str
    back_translation: str | None = None
    state: LineState = LineState.supported
    objections: list[Objection] = []
