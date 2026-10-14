"""Build the clinical review page's rows from the data files (handoff v3 D14).

    uv run python scripts/review_rows.py [out_dir]

Writes one JSON document per section plus meta.json into out_dir (default runs/review). Those
documents seed the review artifact's database; Petri's verdicts are stored there per row id with
the row's hash, so a row changed after review shows as needing a new look.
"""
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

SIDE_FI = {"left": "vasen", "right": "oikea", "both": "molemmat", "none": "ei puolta", "any": "kaikki", None: "PUUTTUU"}
STATE_FI = {"supported": "tuettu", "conflict": "ristiriita", "proposal": "ehdotus",
            "uncertain_translation": "epävarma käännös"}
LANG_FI = {"ar": "arabia", "uk": "ukraina", "en": "englanti"}
SIDE_MODE_FI = {"per_side": "puolikohtainen", "bilateral": "molemmat puolet", "none": "ei puolta"}
UNIT_FI = {"reps": "toistot", "seconds": "sekunnit", "minutes": "minuutit"}


def load(rel: str) -> dict:
    return json.loads((DATA / rel).read_text(encoding="utf-8"))


def row(rid: str, title: str, fields: list[tuple[str, str]], text: str = "", kind: str = "") -> dict:
    body = {"id": rid, "kind": kind, "title": title, "fields": [list(f) for f in fields], "text": text}
    body["hash"] = hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
    return body


def main(out_dir: Path) -> None:
    vocab = {t["id"]: t for t in load("vocabulary.json")["tags"]}
    catalog = {e["id"]: e for e in load("catalog.json")["exercises"]}
    rules_doc = load("rules.json")
    conditions = {c["id"]: c for c in rules_doc["conditions"]}
    profiles = [load(f"profiles/{p}.json") for p in ("P1", "P2", "P3")]
    sessions = [load(f"sessions/{s}.slots.json") for s in ("S1", "S2", "S3")]

    def ex_name(eid: str) -> str:
        e = catalog[eid]
        return f"{e['fi']} ({e['en']})"

    sections = []

    sections.append({"key": "profiles", "order": 1, "title": "Profiilit",
                     "intro": "Synteettiset potilaat. Tarkista, että tilat ja yhteenveto ovat realistisia ja asiallisia.",
                     "rows": [row(p["profile_id"], f"{p['profile_id']} · {LANG_FI[p['language']]} · {p['age_band']} v",
                                  [("Sessio", p["session_id"]),
                                   ("Tilat", "; ".join(conditions[c]["fi"] for c in p["conditions"]))],
                                  p["summary"], "profile") for p in profiles]})

    sections.append({"key": "conditions", "order": 2, "title": "Dokumentoidut tilat",
                     "intro": "Profiilien tilat, joihin rajoitussäännöt kytkeytyvät.",
                     "rows": [row(c["id"], c["fi"], [("Englanniksi", c["en"])], "", "condition")
                              for c in rules_doc["conditions"]]})

    sections.append({"key": "rules", "order": 3, "title": "Rajoitussäännöt",
                     "intro": "Tila × liiketunniste → estä tai varoita. Este pysäyttää ohjelman ja terapeutti päättää; "
                              "varoitus kulkee potilaan riville. Teksti näkyy sellaisenaan.",
                     "rows": [row(r["id"], f"{conditions[r['condition']]['fi']} × {vocab[r['tag']]['fi']}",
                                  [("Vaikutus", "ESTÄ" if r["effect"] == "block" else "VAROITUS"),
                                   ("Puoli", SIDE_FI[r["side"]]),
                                   ("Tunniste", r["tag"])],
                                  r["text"], r["effect"]) for r in rules_doc["rules"]]})

    session_rows = []
    for s in sessions:
        session_rows.append(row(s["session_id"],
                                f"Sessio {s['session_id']} · {LANG_FI[s['patient_language']]} · {s['visit_minutes']} min",
                                [("Profiili", s["profile_id"]), ("Transkriptio", LANG_FI[s["transcript_language"]])],
                                s["demonstrates"], "session"))
        for sl in s["prescribed"]:
            fields = [("Puoli", SIDE_FI[sl["side"]]), ("Annos", sl["dose"] or "PUUTTUU"),
                      ("Toistuvuus", sl["frequency"] or "PUUTTUU"),
                      ("Odotettu tila", STATE_FI[sl["expected_state"]])]
            if sl["cautions"]:
                fields.append(("Terapeutin varotoimi", " ".join(sl["cautions"])))
            if sl["extra_tags"]:
                fields.append(("Lisätunnisteet", ", ".join(vocab[t]["fi"] for t in sl["extra_tags"])))
            if sl["stated"] != "explicit":
                fields.append(("Miten sanotaan", sl["stated"]))
            session_rows.append(row(sl["slot"], ex_name(sl["exercise_id"]), fields, sl.get("note", ""), "slot"))
        for t in s["traps"]:
            session_rows.append(row(t["slot"], f"ANSA: {ex_name(t['exercise_id'])}",
                                    [("Miten mainitaan", t["how_mentioned"])], t["expected"], "trap"))
    sections.append({"key": "sessions", "order": 4, "title": "Sessiot ja määräykset",
                     "intro": "Jokainen määräys on kohta, jonka ympärille dialogi kirjoitetaan hyväksynnän jälkeen. "
                              "Ansat ovat mainintoja, joita malli helposti lisää ohjelmaan.",
                     "rows": session_rows})

    dialogue_rows = []
    for s in sessions:
        sid = s["session_id"]
        raw = (DATA / "sessions" / f"{sid}.transcript.jsonl").read_text(encoding="utf-8")
        lines = [json.loads(x) for x in raw.splitlines() if x.strip()]
        key = json.loads((DATA / "sessions" / f"{sid}.gold.json").read_text(encoding="utf-8"))
        cites: dict[str, list[str]] = {}
        for g in key["items"]:
            for span in g["span_ids"]:
                cites.setdefault(span, []).append(g["slot"])

        def line(x: dict, cites: dict[str, list[str]] = cites) -> str:
            who = "T" if x["speaker"] == "therapist" else "P"
            tag = f"   [{', '.join(cites[x['span_id']])}]" if x["span_id"] in cites else ""
            return f"{x['span_id'][1:]} {who}: {x['text']}{tag}"

        body = "\n".join(line(x) for x in lines)
        dialogue_rows.append(row(f"{sid}.dialogue", f"Dialogi {sid} · {len(lines)} repliikkiä · {lines[-1]['ts'] // 60} min",
                                 [("Merkinnät", "T = terapeutti, P = potilas; [S1.2] = repliikki, joka sanoo määräyksen")],
                                 body, "dialogue"))
    sections.append({"key": "dialogues", "order": 5, "title": "Dialogit",
                     "intro": "Englanninkieliset vastaanottodialogit hyväksyttyjen määräysten ympärillä. Hakasulkeissa vastausavain: "
                              "mikä repliikki sanoo minkäkin määräyksen. Tarkista, että dialogi kuulostaa vastaanotolta.",
                     "rows": dialogue_rows})

    sections.append({"key": "exercises", "order": 6, "title": "Liikekatalogi",
                     "intro": "Yleiset kotiharjoitteet tunnisteineen. Ohjelause näkyy potilaalle (käännettynä).",
                     "rows": [row(e["id"], f"{e['fi']} ({e['en']})",
                                  [("Tunnisteet", ", ".join(vocab[t]["fi"] for t in e["tags"])),
                                   ("Puolisuus", SIDE_MODE_FI[e["side_mode"]]),
                                   ("Annosyksikkö", UNIT_FI[e["dose_unit"]])],
                                  e["how"], "exercise") for e in catalog.values()]})

    sections.append({"key": "tags", "order": 7, "title": "Liike- ja kuormitussanasto",
                     "intro": "Kiinteä sanasto, johon säännöt osuvat. Pienet asiat viimeiseksi.",
                     "rows": [row(t["id"], t["fi"], [("Ryhmä", t["group"])], t["en"], "tag")
                              for t in vocab.values()]})

    out_dir.mkdir(parents=True, exist_ok=True)
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                            text=True, check=False).stdout.strip()
    total = sum(len(s["rows"]) for s in sections)
    for s in sections:
        (out_dir / f"{s['key']}.json").write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = {"draft": "v1", "commit": commit, "rows": total,
            "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")}
    (out_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    print(f"{total} rows in {len(sections)} sections -> {out_dir}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "runs" / "review")
