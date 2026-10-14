// Mirror the Atlas model's decisions into docs/adr/ as one file per ADR.
//
// The model is the source of truth (Atlas system `as-prescribed`, `decisions[]`); these files are a
// rendering of it in the family's ADR layout, so the decisions can be read in the repository
// without Atlas. Regenerate after every model change (CLAUDE.md, "Session end"):
//
//   node scripts/adr-from-model.mjs [path/to/as-prescribed.model.json]
//
// Default path: the ATLAS_DIR environment variable, else the `quaesitor atlas` checkout found
// by walking up the directory tree (works from a worktree too). A hand edit under docs/adr/
// is lost on the next run: edit the model, then regenerate. Same script as in HomeTeam,
// ReviewGlass and AvoQ.

import { readFileSync, writeFileSync, mkdirSync, readdirSync, unlinkSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const SYSTEM = "as-prescribed";
const PREFIX = /^adr\.ap\./;
const here = dirname(fileURLToPath(import.meta.url));
const rel = join("model", "systems", `${SYSTEM}.model.json`);

function findModel() {
  if (process.argv[2]) return process.argv[2];
  if (process.env.ATLAS_DIR) return join(process.env.ATLAS_DIR, rel);
  for (let dir = here; dirname(dir) !== dir; dir = dirname(dir)) {
    const candidate = join(dir, "quaesitor atlas", rel);
    if (existsSync(candidate)) return candidate;
  }
  throw new Error("Atlas model not found: pass the path as an argument or set ATLAS_DIR");
}

const modelPath = findModel();
const outDir = join(here, "..", "docs", "adr");
const model = JSON.parse(readFileSync(modelPath, "utf8"));
const names = new Map([
  ...model.systems.map((s) => [s.id, s.name]),
  ...model.modules.map((m) => [m.id, m.name]),
]);
mkdirSync(outDir, { recursive: true });

// Start clean so a renumbered or removed decision cannot leave a stale file behind.
for (const f of readdirSync(outDir)) if (/^\d{3,4}-.*\.md$/.test(f)) unlinkSync(join(outDir, f));

const slug = (s) =>
  s
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 48);

const index = [];
for (const d of model.decisions) {
  const n = d.id.replace(PREFIX, "").padStart(4, "0");
  const file = `${n}-${slug(d.title)}.md`;
  const links = (d.links ?? [])
    .map((l) => (names.has(l) ? `\`${l}\` (${names.get(l)})` : `\`${l}\``))
    .join(", ");
  const status = (d.status ?? "proposed").replace(/^\w/, (c) => c.toUpperCase());
  const body = `# ADR-${n}: ${d.title}

**Status:** ${status}
**Atlas id:** \`${d.id}\`
**Links:** ${links || "(none)"}

> Rendered from the Atlas model (system \`${SYSTEM}\`). The model is the source of
> truth; edit it there and run \`node scripts/adr-from-model.mjs\`.

---

## Context

${d.context}

## Decision

${d.decision}

## Consequences

${d.consequences ?? "(none recorded)"}
`;
  writeFileSync(join(outDir, file), body);
  index.push(`- [ADR-${n}](${file}): ${d.title} *(${d.status})*`);
}

writeFileSync(
  join(outDir, "README.md"),
  `# Architecture decision records

One file per decision, rendered from the Atlas model's \`decisions[]\` for system
\`${SYSTEM}\`. The model is the source of truth; these files exist so the decisions are
readable in the repository without Atlas. Regenerate with:

\`\`\`bash
node scripts/adr-from-model.mjs
\`\`\`

A new decision is added to the model (a PR against the Atlas repository, see CLAUDE.md
"Session end"), not here. A hand edit here is lost on the next run.

${index.join("\n")}
`,
);
console.log(`${model.decisions.length} ADRs -> ${outDir} (model: ${modelPath})`);
