# Mutashabihat — meeting prep

Meeting context: scheduled via LinkedIn Messenger with Fatema Bent Muhammad.
The thread is in the conversation history; this doc is the organized version of
what the user wants to say / ask before going in.

## The pitch (one paragraph)

We are building **nour** — a voice AI agent for Quran memorization (Hafs).

It listens while you recite from memory. The most important job: catch mistakes
at the exact word and correct them, in real time.

On top of that: when the recited verse belongs to a mutashabihat (parallel/similar
verses) family, the agent interrupts the recitation and asks about it — the
"clean recitation" bonus.

It also maintains long-term memory: frequent mistakes, strong areas, weak areas.

## The three layers (the brain dump, organized)

### 1. Listen / catch / correct (the core)

- ASR while reciting, word-level granularity, immediate correction.
- This is the product. Mistake detection is commodity elsewhere (Tarteel), but the
  alignment + scoring underneath is what nour builds.

### 2. Mutashabihat interrupt (the differentiator)

- When the recited verse is in the mutashabihat set, interrupt and ask.
- Question: only on clean recitation, or whenever the verse maps to a mutashabihat?
- Design question: how does this compose with the prompt ladder (ladder = correction
  path; mutashabihat = clean-recitation bonus)? Does it ever fire during a
  correction sequence?

### 3. Long-term memory / user profile (the retention model)

- Frequent mistakes, strong / weak areas, hesitation patterns.
- Feeds the competence model and scheduling (decay, revision cursor, fail gate).

## Open design questions the meeting should surface

- How is the mutashabihat data structured, and what granularity (verses?
  questions? similarities? all three)?
- How does user profile feed mutashabihat content (e.g., only challenge users
  weak there)?
- Interruption mechanics: mic muted while agent speaks? After the ayah? During?
- Feedback: visual-only or does the reference clip play automatically?

## Questions for Fatema (prepared)

1. How are you serving the mutashabihat data — database, API, both? Is it accessible
   to someone building something like nour? Any technical/licensing constraints?
2. How was the dataset compiled? Sources (books of mutashabihat, verse endings, her
   sheikh's questions), and what "similar" meant in your methodology.
3. How large is it, and how is it mapped to ayahs/verses?
4. What did the volunteer team learn — and what's next for the project?

## Why we're meeting her

The hard part of mutashabihat is the data; the quiz UX is the easy part. If access to
that data is possible, the "clean recitation → challenge" feature becomes a lookup,
not a build.
