# As Prescribed: notes for the build agent

As Prescribed is an entry to the AMD Developer Hackathon ACT III (lablab.ai), Health and Wellbeing
track. During a physiotherapy visit it turns the session transcript into the patient's home program
in the patient's own language (Arabic, Ukrainian) and **verifies the therapist's prescription**:
fidelity to the transcript, documented restrictions, and the translation. It never diagnoses,
recommends or judges suitability. MIT. Repository `github.com/Sunrisesoftware-app/as-prescribed`
(public). Atlas system `as-prescribed`. All data is synthetic.

**Submission deadline: Sun 18.10.2026 13:00 EEST at the latest**: the lablab live dashboard's
countdown ends 18.10. 10:00 UTC (read 14.10.2026 20:52), while the event page was read earlier as
18:00 EEST; the earlier one binds until the organisers say otherwise. The target is Sat 17.10. After the hackathon the repository is the base for Since AI Turku (6.-8.11.2026).

## Where the truth is

| What | Where |
|---|---|
| Architecture decision | The Atlas model's `decisions[]` (system `as-prescribed`), rendered into [`docs/adr/`](docs/adr/README.md) |
| Product: for whom, what, what never | [`docs/product.md`](docs/product.md) |
| Architecture as prose | [`docs/architecture.md`](docs/architecture.md) |
| Decisions asked as boxes, and their answers | [`docs/DECISIONS.md`](docs/DECISIONS.md): the file is the truth, the conversation is not |
| State and the next session | [`docs/BUILD_INFO.json`](docs/BUILD_INFO.json): `state` and `next_session` |
| Open task | [`docs/BACKLOG.md`](docs/BACKLOG.md): the **only** list, including the owner's own actions |
| Order and gates up to the deadline | [`docs/roadmap.md`](docs/roadmap.md) |
| What was done and measured | [`docs/CHANGELOG.md`](docs/CHANGELOG.md), newest first |
| Lesson paid for | [`docs/LESSONS.md`](docs/LESSONS.md): the root cause as the heading, the rule at the end |
| The evaluation (plan, seal, results, raw runs) | [`eval/`](eval/); the pre-registration and results in Atlas (`AS-PRESCRIBED-EVAL-ENNAKKO`, `-TULOS`) |
| Clinical content (approved by the owner) | [`data/`](data/); the review page is the record of the approval |
| Source documents in Atlas (not the truth) | [`docs/history/`](docs/history/README.md) lists them |
| Working practice | this file |

Nothing goes into two places as a copy; a reference is enough. There is no SEED document: the
ADRs, product.md and architecture.md carry that role (the HomeTeam, ReviewGlass and AvoQ model).

## Golden rules

- **Language.** Code, comments, commit messages and documentation in English; the judges read them.
  Conversation with the owner in Finnish. The UI in English; patient lines in the patient's language.
- **The boundary (adr.ap.001).** The system verifies the therapist's prescription. Never write
  "personalised", "recommends" or "adapted to your injury" in code, copy or the pitch.
- **Synthetic data only (handoff D3).** No real patient, no Premius material. No free-text input in
  the public demo (adr.ap.004); nothing about a session is logged.
- **Safety is deterministic.** Documented restrictions are rules (adr.ap.003), a fired restriction
  stays a conflict whatever a model does later (adr.ap.005), a correction may not change the
  exercise (adr.ap.006), and a falsifier claim a checkable rule can settle is settled by code
  (adr.ap.007). The English line is composed, never written by a model (adr.ap.008).
- **Generator and falsifier are different model families (adr.ap.002).**
- **Clinical content is the owner's.** A new or changed clinical row (catalogue, rule, profile, slot,
  dialogue) goes through the review page before it is used; `data/` notes say what was approved.
- **The evaluation is sealed (adr.ap.009).** `eval/plan-v1.json` matches `eval/SEAL` or nothing runs.
  Run 1 is the reported result. A later run of the same plan carries `--tag` and is always reported
  as made after reading run 1. A new claim needs new sessions and a new sealed plan.
- **Keys never enter git.** `.env` holds them (ignored); `bash scripts/check-secrets.sh` runs
  locally and in CI. The tokenfactory key goes only to tokenfactory URLs and is never printed.

## Working practice

- **Measure before claiming.** A negative result is a result; it is reported as it fell.
- **Proposals as what / why / impact.** The owner decides. Two equally good options: both shown,
  one recommended.
- **Decision boxes** (Atlas artifact `SUNRISE-TYOTAPA-PAATOSLAATIKOT`): four at a time, the current
  state verbatim, two or three options with one recommended, new wording shown verbatim and marked
  as a proposal. Each answer goes into `docs/DECISIONS.md` and the Atlas decision log (typed:
  option set, the recommendation as a distribution, the class, the recommender) before the next
  batch.
- **No codes in conversation with the owner.** A status report in three parts: done, to decide, open.
- **Git.** `main` on GitHub is the only truth. During the hackathon a single agent commits to `main`
  directly with a green local run (`ruff`, `pytest`, the secret scan); CI must stay green. Never
  force-push `main`; destructive git commands are always asked. Commit subject: what changed and
  why; the body records what was measured.
- **CI is the gate** (`.github/workflows/ci.yml`): secret scan, `uv sync --frozen`, `ruff`,
  `pytest`. No `continue-on-error` anywhere.
- **Dependencies by permission:** "X is needed for Y. Options A, B. Recommend A because Z."
- **The owner's shell is PowerShell 5.1:** commands given to the owner are copy-paste ready, one
  per code block, no `&&`. The agent's shell is Git Bash: Python patches go through a file or the
  Edit tool (a heredoc broke escapes twice on 14.10.2026), and scripts printing Arabic or Ukrainian
  call `sys.stdout.reconfigure(encoding="utf-8")`.
- **The Somnus box** (local mode) is shared and has 16 GB of host RAM. Follow Atlas
  `AS-PRESCRIBED-SOMNUS-BOKSI`: read `atlas_get_konetila` and the card queue first, take the lease
  `hw:somnus/7900xt`, start Gemma with `sudo -n systemctl start llama-theta`, lower the agent cache
  (`/home/sf3d/somnus-diag/llama-agent.env`), one request at a time on `:8091`, and restore after
  every period: stop llama-theta, remove the env file and restart llama-agent, **start Laya**
  (starting llama-theta stops it), release the lease, a line in the somnus thread.
- **Atlas** is read and written through the claude.ai connector (identity `petri`). `.mcp.json` is
  deliberately empty (HomeTeam rule).

## Session start

A start message of "As Prescribed jatkuu" plus any news is enough.

1. **Sync before the first edit:**
   ```bash
   git fetch origin
   ```
   ```bash
   git rev-list --left-right --count origin/main...HEAD
   ```
2. **Read** `docs/BUILD_INFO.json` `next_session` (`read_first`, `scope`, `gate`) and the Atlas
   handover it names (`AS-PRESCRIBED-KETJUNVAIHTO-<n>`).
3. **Atlas:** `atlas_get_workspace("as-prescribed")`; the newest `as-prescribed.STATUS`.
4. **Before using the box:** the rules above.

## Session end

The session is done when the next session can start from a clean desk with the start message
alone. When the owner says "paketoidaan", nothing new is built.

1. **Documents:** `BUILD_INFO.json` (`state`, `next_session`) · `CHANGELOG.md` (what was done and
   what was measured) · `BACKLOG.md` (done rows out, new rows in, the owner's too) ·
   `DECISIONS.md` · `LESSONS.md` if a lesson was paid for.
2. **A new architecture decision enters the Atlas model first:** in the Atlas checkout
   (`E:\projects\sunrisesoftware\quaesitor atlas`) an own worktree off `origin/main`; add the
   `adr.ap.NNN` row (title, context, decision, consequences, status, links to modules or the
   system) in `model/systems/as-prescribed.model.json`, at text level; `pnpm validate:models`,
   `pnpm review --system as-prescribed`, `pnpm model:guard`, `pnpm --filter @atlas/mcp-worker
   bundle`; PR; CI green; merge (the owner merges if the agent's permission check refuses), then
   `pnpm --filter @atlas/mcp-worker run deploy` and `pnpm run deploy` (viewer) from the merged
   main, verified with `atlas_get_system`. Here: `node scripts/adr-from-model.mjs` and commit
   `docs/adr/`.
3. **Atlas:** `as-prescribed.STATUS` (read the newest first), and at the end of a chain the
   handover `AS-PRESCRIBED-KETJUNVAIHTO-<n>`; a line in the project thread.
4. **Memory:** update the project memory if the direction changed.

## Reading a green check

A green exit code can mean nothing was checked. Read the run list and the steps:

```
gh run list --repo Sunrisesoftware-app/as-prescribed --limit 3
```

## Layout

| Path | What |
|---|---|
| `asprescribed/` | The application: config, model client, ingest, extract, program (compose), rules, translate, falsify, pipeline (rounds), evaluation, web API (`main.py`, `web.py`), `static/` (the desk and the patient sheet) |
| `data/` | Approved synthetic content: vocabulary, catalogue, rules, profiles, session slots, dialogues and answer keys; `recorded/` holds the recorded demo runs |
| `eval/` | The sealed plan, its seal, results and raw runs |
| `scripts/` | `models.py`, `run_session.py`, `eval.py`, `record.py`, `review_rows.py`, `write_transcripts.py`, `adr-from-model.mjs`, `check-secrets.sh` |
| `tests/` | Pytest; a fake LLM answers by system prompt, so the pipeline is tested without a model |
| `docs/` | The documentation above |

## Lessons that became rules

Full stories in [`docs/LESSONS.md`](docs/LESSONS.md). The short forms:

- **A check that cannot run must not read as a pass** (15.10.2026): an exercise outside the catalogue
  has no tags for the rule engine, so its line is a proposal, never supported (DECISIONS row 24).

- **A correction loop can undo a safety halt** (14.10.2026): a fired restriction is sticky and never
  corrected by a model (adr.ap.005).
- **A same-family falsifier passes its own family's errors** (14.10.2026): keep the falsifier in
  another family (adr.ap.002).
- **Right-to-left text and number words break number checks** (14.10.2026): doses as "N × M" with
  digits; the Arabic dual counts as two; one is not required as a digit.
- **Viewer approval is not the model** (14.10.2026): an Atlas proposal needs `rationale` inside the
  payload, and apply-approved applies every approved row; a new system is written as a model file
  and merged by PR.
