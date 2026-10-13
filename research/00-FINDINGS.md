# nour — Research Findings

Synthesis of seven research reports in `research/`. Read this first; the
individual reports are the evidence trail.

*Compiled 2026-10-13. Sources inline in the reports; no figures below are
restated without attribution there.*

---

## TL;DR

Your original segment — **Arabic-native hifz students** — is the right one.
A pivot to non-Arabic-speaking students in Western academies was investigated
and is **not recommended as a pivot**, but remains a live *exploration* because
the developer has direct access to specialised academies that no research
report could account for.

Two of my earlier competitive claims were wrong. Both corrections are recorded
below rather than quietly dropped.

---

## 1. Verified

| Finding | Source |
|---|---|
| Tarteel has 15M+ users, ~$7.50/month annual premium, $156/yr family | `01-market.md`, `02-competitors.md`, tarteel.ai/en/pricing |
| Tarteel ships word-level mistake detection, memorization tracking, goals, and Test Mode (random position) | `01`, `02` |
| Tarteel already models **recited ≠ tested** — review/memorization goals count progress only when ayahs are hidden | `01` |
| **Tarteel has mutashabihat**: 814 repeated phrases, similar verses for 1,208 ayahs. It is **100% reader lookup** (press-and-hold an ayah), never surfaced during recitation | `02`, verified directly against Tarteel's own support article |
| Tarteel's "similar verses" is **lexical** — shared wording | verified directly |
| **Six live products claim phoneme/tajweed feedback**: Tilawa.ai, QariAI, TajweedMate, Quran In Depth, TajweedPage, NUR.AI | Perplexity research; Tilawa/QariAI/TajweedMate verified live by the developer |
| Quran tutors run **$2–100/hr, avg ~$10/hr** (Preply); iTalki community tutors $4–20/hr | Perplexity research |
| `wasimlhr/whisper-quran-v1` is **CC-BY-NC-4.0 — non-commercial** | `04-benchmark.md` |
| `tarteel-ai/whisper-base-ar-quran` and `-tiny-` are **Apache-2.0**; `yousifgamalo/quran-s-finetuned` Apache-2.0 | `04-benchmark.md` |
| `obadx/muaalem-model-v3_2` — 0.6B params, **MIT**, phoneme-level, 75.8% Tajweed F1 on learner errors | `04`, `07` |
| CTranslate2 `int8` works on CUDA ≥ 6.1; `float16` requires ≥ 7.0. Pascal has **no tensor cores** | `04`, `07` — independently confirmed |
| Western academies predominantly teach **reading, tajweed, short-surah memorisation**; full hifz is a separate, selective track | Perplexity, from published syllabi (Al-Ansaar UK, Hendon, MTI UK, Madina Academy) |
| Dedicated Western hifz programs **do exist** with real scale: Scarborough MA (CA) 360 graduates 2023, Al Madinah Centre (CA) 200 students, Muslim Society Inc (US), Marwah Academy (US), ICB (CA) | Perplexity follow-up |
| Arabic-only UI is a **documented liability** for non-native learners — a Google Play reviewer on Quran Tutor: *"The directions of correcting mistakes are all in Arabic, which is very much inconvenient for non Arabic speaker like me"* | Perplexity research |

---

## 2. Speculative — do not treat as validated

| Claim | Status |
|---|---|
| **5–20M globally active Quran memorizers (SAM)** | **Unsourced.** Proposed in `01-market.md` at confidence "Low". Perplexity independently flagged it as "not demonstrably supported by a public primary source". **Assume, not fact.** |
| SOM of 50k–500k | Estimate, no basis. Do not use. |
| Western non-Arabic hifz students "**<15,000**" | Proposed in the pivot research with **3 URLs** — too thin to rely on. The follow-up found larger real programs, so this is likely too pessimistic, but there is still **no census**. |
| Tarteel revenue (~$27.6K weekly, KSA) | Third-party Sensor Tower figure, not verified directly. |

---

## 3. Unknown — no public data exists

- **No census of active Quran memorizers** anywhere in the world. Public claims range from 3–4M to 200M; the 200M figure is widely repeated and widely disputed.
- **No census of hifz enrolment in Western academies**, and no split between full-time / after-school / casual, or between native and non-native students.
- **No published WER, PER or F1 for any commercial tajweed product.** Tilawa.ai, QariAI and TajweedMate *claim* makharij/ghunnah/madd/qalqalah detection; **nobody has validated whether it works.** Marketing claims are not technical evidence.
- Whether the `kilo-auto/free` router is reliable enough for reproducible semantic extraction (it produced 30 → 23 → 17 nodes across identical runs; the shrink guard caught it).

---

## 4. Corrections

Recorded deliberately so the error pattern does not repeat.

**Mistake 1 — "nobody does mutashabihat."** Wrong. Tarteel has 814 repeated
phrases and similar verses for 1,208 ayahs. My framing had a kernel of truth —
theirs is lookup-only and never proactive — but I stated an absolute I had not
verified.

**Mistake 2 — "Phoneme-level feedback is unwedged; nobody does it, for
anyone."** Wrong, and stated confidently. Six live products claim exactly this.
Verified three of them by fetching the pages directly.

**The pattern:** I asserted competitive gaps from reading academic papers
rather than from the market, and got it wrong twice. Competitive claims need
verification against live products before they enter a plan.

**A third, narrower one:** during the ensemble-plugin tuning I read
`kilo-auto/balanced` as free. It costs $0.325/$1.95 per million tokens. A 402
from the live API confirmed it. **Verify cost claims against the API, not the
model name.**

---

## 5. Open exploration — the academy channel

Not a pivot recommendation. A cheap experiment with a defined kill criterion.

**What changed:** the research concluded the segment was unreachable for a solo
builder. The developer has direct access to specialised academies, which no
report could know. Reachability is therefore *answered*; the other objections
are not.

**What still stands against it:**

1. Western academies teach reading/tajweed with text visible; nour assumes
   recite-from-memory. Product mismatch for the majority of their students.
2. Segment size is unquantified and probably small.
3. Arabic-only UI is a documented liability for exactly this segment.
4. **It contradicts "mainly for me"** — for a native speaker, phoneme feedback
   is useless; the product would be different for the two audiences.

**Do this first — five conversations, these questions:**

1. Of your students, what split is reading/tajweed vs memorisation?
2. For memorisation students — do you teach backward recitation?
3. What is hardest to correct remotely between lessons?
4. Do students know they got something wrong? How?
5. If something flagged *which specific sound* was wrong, with an articulation
   cue — useful?
6. Would you use it? Who pays — you, or the parents?

**Kill criterion: if fewer than 2 of 5 say phonetic-level feedback would save
them real time, drop it.**

---

## 6. What survives as defensible

| Claim | Status |
|---|---|
| **Proactive** mutashabihat — surfacing parallel-verse challenges unprompted when a recitation is clean | Genuinely open. Tarteel is lookup-only. QurSim (7,679 pairs, Ibn Kathir) is 6× larger than Tarteel's set and is *semantic*, where Tarteel's is *lexical*. Complementary, not competing. |
| **Competence model** as the core — retention decay, hesitation as a first-class signal, forward *and* backward recitation | Open, though Tarteel has heatmaps and SRS apps exist. The defensible claim is hesitation-driven retention, not "spaced repetition". |
| Precision over recall on religious content | Unchanged, and reinforced: a false "you said that wrong" is corrosive. |

---

## 7. Reports in this directory

| File | Topic | Sources |
|---|---|---|
| `01-market.md` | Market size, demand, segments, WTP | 22 URLs |
| `02-competitors.md` | Ten-competitor teardown, feature matrix, review mining | 96 URLs |
| `03-business.md` | Business Model Canvas, monetization, unit economics, risks | 29 URLs |
| `04-benchmark.md` | Which model first, eval harness design, datasets, latency | 69 URLs |
| `05-non-native-market.md` | **Thin — 3 URLs**, websearch unavailable to the author | 3 URLs |
| `06-non-native-competitors.md` | **Thin — 6 URLs**, websearch unavailable to the author | 6 URLs |
| `07-accent-asr-feasibility.md` | Accented Quranic ASR feasibility | 31 URLs |

`05` and `06` reached **opposite conclusions** on the pivot — one "not viable",
one "niche is open". Both are under-sourced and were run without working web
search. Treat their conclusions as hypotheses, not findings.