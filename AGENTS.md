# nour — Agent Instructions

Guidance for coding agents working in this repository.

> **Status: scaffold.** Sections marked `TODO` need real answers before this
> file is useful beyond general hygiene. Delete the `TODO` markers as you fill
> them in.

## What this project is

**TODO — one or two sentences.** What does nour do, and who is it for?

Until this is filled in, agents will guess at the project's purpose from the
code. That's the single highest-value thing to add here.

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

**TODO — a short map of the repo once it exists.**

```
nour/
├── .opencode/     # project agent config (this dir's config)
└── AGENTS.md      # this file
```

## Reference material

**TODO — link the specs, ADRs, or docs that define correct behaviour.** Point
agents at the source of truth so they don't invent requirements.