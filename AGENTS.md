# nour — Agent Instructions

Guidance for coding agents working in this repository.

> **Read [`PLAN.md`](./PLAN.md) before touching the audio pipeline.** It holds
> binding design constraints and verified hardware limits. Four rules that break
> the product rather than just the code:
>
> 1. **Never bias the ASR decoder for error scoring.** `hotwords` and
>    `initial_prompt` are correct for identifying *which* ayah is being
>    recited, and forbidden when scoring errors — a biased decoder smooths a
>    wrong word toward the correct one and hides the mistake being looked for.
> 2. **Segment at waqf marks**, not fixed windows and not ayah boundaries alone.
>    The Uthmani text already encodes where the reciter is obliged to pause.
> 3. **Recited is not tested.** Sight-assisted recitation must never support a
>    mastery claim; only free recall does.
> 4. **Precision over recall.** On religious content, falsely telling someone
>    their recitation is wrong is worse than missing an error.
>
> Sections below marked `TODO` still need real answers.

## Standing rule: do not reinvent the wheel

**Search for an existing implementation before writing one.** Three times in
this project's history, code was hand-rolled that already existed:

- The graphify pipeline, when `graphify extract` does the whole thing headless
- OpenCode config migration steps that are documented in the V2 docs
- A planned custom WER/alignment harness, when `jiwer` and `WhisperX` are the
  standard answers

Before building any of these, check:

| Need | Use this |
|---|---|
| WER / CER scoring | `jiwer` |
| Whisper alignment, VAD, word timestamps | `WhisperX` |
| Quran word-level alignment + quality validator | `quraniio/quran-timing-helper` |
| Quran recitation feedback app (MIT) | `foyzulkarim/hifz-tester` — same pipeline as our Phase 0–3 |
| Knowledge graph over the repo | `graphify` (wired, free via kilo gateway) |
| Parallel agents / teams | ensemble `team_*` tools |

**Adopt by default; fork only when the existing thing demonstrably cannot do
it.** Reading someone else's implementation is cheaper than writing yours, and
you inherit their bug reports.

If something genuinely must be built from scratch, say why in the commit
message before starting.

## What this project is

**nour** is a voice agent for Quran memorization (Hafs). It listens while the
user recites from memory, detects mistakes in near-real time, maintains a
competence model of what the user has actually internalized — tracking retention
decay, hesitation, and fluency in both forward and backward recitation — and
challenges the user on parallel verses (mutashabihat) when a recitation is clean.

**The competence model is the product.** Real-time error detection is
commodity: Tarteel already ships it at 15M+ users. Nour's differentiation is
the retention model, the mutashabihat challenge, and treating hesitation as a
first-class signal.

Arabic-only. Single-user web app: FastAPI + Pipecat backend, React frontend.

## Environment

| | |
|---|---|
| OS | Windows |
| Shell | PowerShell |
| Stack | **TODO** — not decided yet |

### Shell rules

- The default shell is PowerShell, **not** bash/cmd. Do not assume `&&`, `export`,
  `curl -d`, heredocs (`<<EOF`), or POSIX-only flags.
- For multi-line scripts, write a script file and run it rather than fighting
  quoting inline.
- Python output: set `$env:PYTHONIOENCODING='utf8'` before running scripts that
  touch non-ASCII content.

### Graphify backend

Graphify's semantic extraction needs an LLM. It is configured through
**User-scope environment variables**, pointing at the kilo gateway:

| Variable | Value |
|---|---|
| `OPENAI_BASE_URL` | `https://api.kilo.ai/api/gateway/v1` |
| `OPENAI_MODEL` | `kilo-auto/free` |
| `OPENAI_API_KEY` | set in the User registry — **never read it, never write it to a file, never commit it** |

They are already permanent (User scope). A `profile.ps1` shim rehydrates them
into shells launched from an already-running parent, so a fresh shell has them
without setup.

**Do not re-export these manually and do not paste the key into commands.** If
`OPENAI_BASE_URL` is empty, the profile has not run — open a new shell.

Note: `kilo-auto/efficient` and above are **paid** and return
`402 Paid Model - Credits Required`. Stay on `kilo-auto/free` unless the user
explicitly asks otherwise.

Cost: graphify runs at **$0** on this setup.

## Conventions

**TODO — fill these in.** Suggested starting points:

- Indentation / formatter (Prettier? Black? Ruff format?)
- Naming: files, components, database tables
- Commit message format (Conventional Commits? something else?)
- Test framework and how to run a single test

## Working agreements

- Read before you edit. Match the surrounding style rather than introducing a
  new one.
- Prefer the smallest change that solves the problem.
- Don't add a dependency without saying why.
- Don't commit secrets, `.env` values, or credentials.
- When a task is ambiguous, ask rather than guessing at scope.

## Verification

**TODO — what counts as done here?** Examples:

- Lint command
- Typecheck command
- Test command
- Build command

Agents should run these before declaring a task complete.

## Layout

```
nour/
├── .opencode/
│   └── opencode.jsonc   project agent config (watcher, permissions)
├── .gitattributes       LF normalization; binaries marked
├── AGENTS.md            this file
└── PLAN.md              architecture, roadmap, design constraints
```

The layout for `backend/`, `frontend/`, `eval/`, `data/` and `docker/` is
specified in `PLAN.md` §9 and does not exist yet.

## Reference material

| Doc | What it defines |
|---|---|
| [`PLAN.md`](./PLAN.md) | Architecture, verified hardware limits, phased roadmap, design constraints |
| `PLAN.md` §4 | The four rules above, in full |
| `PLAN.md` §7 | Known gaps — read before estimating any audio work |
| `PLAN.md` §5 | Data sources: Quran text, waqf marks, tajweed, QurSim, reference audio |
| [`research/00-FINDINGS.md`](./research/00-FINDINGS.md) | **Read before making competitive or pricing claims.** What is verified vs speculative vs unknown, and two recorded corrections |
| `research/04-benchmark.md` | Model comparison table, licences, eval harness design |

Do not invent requirements. If the answer is not in `PLAN.md`, ask.

**Do not assert a competitive gap from memory.** Two claims ("nobody does
mutashabihat", "nobody does phoneme feedback") were wrong before verification.
Check a live product or `research/00-FINDINGS.md` first.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.
