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

Do not invent requirements. If the answer is not in `PLAN.md`, ask.