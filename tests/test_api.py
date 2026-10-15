"""The views' API with a fake LLM: session data, the streamed live replay and the prescription run
with an injected error, as server-sent events."""
import asyncio
import json

import pytest
from fastapi.testclient import TestClient
from test_pipeline import FakeLLM

from asprescribed import web
from asprescribed.extract import SYSTEM as EXTRACT_SYSTEM
from asprescribed.llm import Completion
from asprescribed.main import app
from asprescribed.pipeline import gold_items


class ExtractingFake(FakeLLM):
    """Extract answers with the approved slots (as i1, i2, ...), everything else as FakeLLM."""

    def __init__(self, session, **kw):
        super().__init__(**kw)
        self.items = [dict(i.model_dump(exclude={"tags"}), item_id=f"i{n}") for n, i in
                      enumerate(gold_items(session), start=1)]

    async def __call__(self, ep, messages, **kw):
        if messages[0]["content"] == EXTRACT_SYSTEM:
            return Completion(content=json.dumps({"items": self.items}), model="fake", completion_tokens=10,
                              seconds=0.01, tokens_per_s=1000.0)
        return await super().__call__(ep, messages, **kw)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("GENERATOR_BASE_URL", "http://gen/v1")
    monkeypatch.setenv("GENERATOR_MODEL", "gen")
    monkeypatch.setenv("FALSIFIER_BASE_URL", "http://fal/v1")
    monkeypatch.setenv("FALSIFIER_MODEL", "fal")
    monkeypatch.setenv("AP_CACHE_S", "0")
    web._cache.clear()
    with TestClient(app) as c:
        yield c
    app.state.chat_fn = None
    del app.state.chat_fn


def events(text: str) -> list[tuple[str, dict]]:
    out = []
    for block in text.split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines() if ": " in line and not line.startswith(":"))
        if "event" in lines:
            out.append((lines["event"], json.loads(lines["data"])))
    return out


def test_pages_and_sessions(client):
    assert client.get("/").status_code == 200 and "As Prescribed" in client.get("/").text
    assert client.get("/patient").status_code == 200 and "Machine-written" in client.get("/patient").text
    ids = [s["id"] for s in client.get("/api/sessions").json()]
    assert ids == ["S1", "S2", "S3"]
    s2 = client.get("/api/sessions/S2").json()
    assert s2["language"] == "uk" and len(s2["transcript"]) == 34
    assert {i["id"] for i in s2["injections"]} >= {"B3", "E1", "F2"}
    assert client.get("/api/sessions/S9").status_code == 404
    assert client.get("/api/sessions/..%2Fx").status_code in (400, 404)


def test_live_replay_streams_spans_drafts_and_a_result(client):
    app.state.chat_fn = ExtractingFake("S2")
    r = client.get("/api/sessions/S2/run", params={"mode": "live", "speed": 1000})
    ev = events(r.text)
    kinds = [k for k, _ in ev]
    assert kinds.count("span") == 34 and "items" in kinds and kinds[-1] == "end"
    result = next(d for k, d in ev if k == "result")
    states = {line["item_id"]: line["state"] for line in result["lines"]}
    assert states["i5"] == "conflict" and result["latency_after_last_chunk_s"] >= 0


def test_prescription_run_with_an_injection_reports_the_catch(client):
    app.state.chat_fn = FakeLLM()
    ev = events(client.get("/api/sessions/S2/run", params={"injection": "E1"}).text)
    inj = next(d for k, d in ev if k == "result")["injection"]
    assert inj["id"] == "E1" and inj["observation"]["detected"] and inj["observation"]["final_state"] == "conflict"


def test_replay_mode_serves_the_recorded_run_and_names_its_gpus(client, monkeypatch):
    monkeypatch.delenv("AP_REPLAY", raising=False)
    assert client.get("/api/demo").json()["replay"] is False
    monkeypatch.setenv("AP_REPLAY", "1")
    demo = client.get("/api/demo").json()
    assert demo["replay"] and demo["recording"]["generator"]["gpu"] == "AMD Radeon AI PRO R9700"
    assert demo["recording"]["falsifier"]["gpu"] == "AMD Radeon RX 7900 XT"
    result = next(d for k, d in events(client.get("/api/sessions/S2/run").text) if k == "result")
    assert result["recorded"] and result["replay"] and result["recording"] == demo["recording"]
    assert [line["state"] for line in result["lines"]].count("conflict") == 1


def test_a_cloud_run_is_compared_with_the_clinic_recording(client, monkeypatch):
    monkeypatch.setenv("AP_MODE", "public")
    monkeypatch.setenv("TOKENFACTORY_BASE_URL", "http://gen")
    cloud = "AMD Radeon Cloud (Token Factory)"
    assert client.get("/api/demo").json()["live"] == {"where": cloud, "generator": "gen", "falsifier": "fal"}
    app.state.chat_fn = FakeLLM()
    result = next(d for k, d in events(client.get("/api/sessions/S2/run").text) if k == "result")
    assert result["models"]["where"] == cloud and not result.get("recorded")
    c = result["clinic"]
    assert c["recording"]["falsifier"]["gpu"] == "AMD Radeon RX 7900 XT"
    assert c["recorded_states"] == {"supported": 4, "conflict": 1} and isinstance(c["same_states"], bool)
    c = next(d for k, d in events(client.get("/api/sessions/S2/run", params={"injection": "E1"}).text)
             if k == "result")["clinic"]
    assert c["caught"] and c["recorded_caught"]
    monkeypatch.setenv("AP_MODE", "local")  # a run on the clinic's own cards is not compared with itself
    result = next(d for k, d in events(client.get("/api/sessions/S2/run").text) if k == "result")
    assert result["clinic"] is None and result["models"]["where"] is None


class SlowFake(FakeLLM):
    async def __call__(self, ep, messages, **kw):
        await asyncio.sleep(0.3)
        return await super().__call__(ep, messages, **kw)


def test_a_cloud_run_over_its_budget_serves_the_clinic_recording(client, monkeypatch):
    monkeypatch.setenv("AP_LIVE_BUDGET_S", "0.2")
    app.state.chat_fn = SlowFake()
    result = next(d for k, d in events(client.get("/api/sessions/S2/run").text) if k == "result")
    assert result["recorded"] and result["fallback"] == "slow" and result["budget_s"] == 0.2
    assert result["recording"]["generator"]["gpu"] == "AMD Radeon AI PRO R9700"


def test_every_recorded_run_was_made_on_the_models_its_label_names():
    rec = web.recording()
    runs = [p for p in web.RECORDED.glob("*.json") if p.name != "recording.json"]
    assert len(runs) == 38
    for p in runs:
        m = json.loads(p.read_text(encoding="utf-8"))["models"]
        assert (m["mode"], m["generator"], m["falsifier"]) == \
            ("local", rec["generator"]["model"], rec["falsifier"]["model"]), p.name


def test_injection_is_refused_in_live_mode_and_unknown_injection_fails(client):
    assert client.get("/api/sessions/S1/run", params={"mode": "live", "injection": "A1"}).status_code == 400
    app.state.chat_fn = FakeLLM()
    ev = events(client.get("/api/sessions/S1/run", params={"injection": "E1"}).text)
    assert ev[0][0] == "failure"
