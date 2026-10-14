from asprescribed.config import endpoint
from asprescribed.llm import extract_json
from asprescribed.schemas import LineState, resolve_state


def test_extract_json_strips_thinking_and_fences():
    assert extract_json('<think>{"x": 0}</think>```json\n{"a": {"b": [1, 2]}}\n```') == {"a": {"b": [1, 2]}}


def test_extract_json_cut_short_reasoning():
    # --reasoning-budget leaves a closing </think> with no opener (somnus, measured 7.8.2026)
    assert extract_json('reasoning {"draft": 1} ... </think> {"answer": 2}') == {"answer": 2}


def test_extract_json_repeated_answer_falls_back_to_first():
    assert extract_json('{"a": 1}\n{"a": 2}') == {"a": 1}


def test_extract_json_none():
    assert extract_json("no json here") is None


def test_precedence():
    assert resolve_state({LineState.supported, LineState.conflict, LineState.proposal}) == LineState.conflict
    assert resolve_state({LineState.uncertain_translation, LineState.proposal}) == LineState.proposal
    assert resolve_state(set()) == LineState.supported


def test_tokenfactory_key_only_for_tokenfactory_urls(monkeypatch):
    monkeypatch.setenv("TOKENFACTORY_BASE_URL", "https://tf.example/v1")
    monkeypatch.setenv("TOKENFACTORY_API_KEY", "test-value-not-a-key")
    monkeypatch.setenv("GENERATOR_BASE_URL", "https://tf.example/v1")
    monkeypatch.setenv("FALSIFIER_BASE_URL", "http://somnus:8091/v1")
    monkeypatch.delenv("GENERATOR_API_KEY", raising=False)
    monkeypatch.delenv("FALSIFIER_API_KEY", raising=False)
    assert endpoint("generator").api_key == "test-value-not-a-key"
    assert endpoint("falsifier").api_key is None
    assert "test-value-not-a-key" not in repr(endpoint("generator"))
