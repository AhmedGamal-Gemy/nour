# nour — Plan

Voice agent that helps with Quran memorization (Hafs). Listens while you recite
from memory, detects mistakes in near-real-time, maintains a competence model of
what you have actually internalized, and challenges you on parallel verses when
you are doing well.

Status: plan approved, not yet implemented.

---

## 1. Competitive context (why this is still worth building)

Tarteel (15M+ users) already ships, since ~2022:

- Word-level memorization mistake detection (wrong / skipped / wrong tashkeel)
- Memorization progress tracking down to word level
- Review scheduling and goals
- "Test Mode" from random positions in your memorization
- Analytics showing which ayahs need work

They also already model the recited-vs-tested distinction: review/memorization
goals only count progress when ayahs are **hidden**, and "Recite" is a separate
goal action from "Memorize"/"Review".

**Conclusion: mistake detection is commodity.** Build it because the alignment
and scoring pipeline underneath is needed by everything downstream — not as the
differentiator.

**Correction (verified):** Tarteel also ships **mutashabihat** — 814 repeated
phrases and similar verses for 1,208 ayahs. It is **100% reader lookup**
(press-and-hold an ayah), never surfaced during or after recitation, and its
similarity is **lexical** (shared wording) rather than semantic. An earlier
draft of this plan claimed nobody offered it; that was wrong.

Separately, at least six products claim phoneme/tajweed feedback — Tilawa.ai,
QariAI, TajweedMate, Quran In Depth, TajweedPage, NUR.AI. **None has published
WER, PER or F1.** The claims are unverified, so the space is not open, but
Phase 8 is a quality-of-execution problem rather than an uncontested
opportunity.

See `research/00-FINDINGS.md` for what is verified versus speculative.

Where Nour wins:

| Area | Tarteel | Nour |
|---|---|---|
| Progress signal | streaks, heatmaps (activity) | retention decay model |
| Test placement | user-chosen | scheduled from weakness |
| Weakness signal | recent errors | decay + hesitation + neighbour anchoring |
| Recitation direction | forward | **continuous run, no restart** |
| On a clean recitation | nothing happens | **mutashabihat challenge** |
| Hesitation | not tracked | first-class signal — drives the prompt ladder |
| Pronunciation | — | phoneme + sifat, via `quran-muaalem` |

A Tarteel user review explicitly requests the hesitation-prompt feature we are
designing. It does not exist yet.

---

## 2. Verified hardware constraints

Measured on this machine, not assumed:

| | |
|---|---|
| GPU | Quadro P2000, 4 GB, **compute capability 6.1 (Pascal)** |
| CPU | Intel i7-8850H, 6 cores / 12 threads, 2.6 GHz |
| ISA | AVX2 — **no AVX-512, no VNNI** |
| RAM | 15.8 GB total |

Consequences:

- `compute_type="int8"` on CUDA **is supported** (Pascal ≥ 6.1 clears the
  `sm_53` kernel floor). `float16` and `int8_float16` are **not**.
- **Pascal has no tensor cores.** Int8 tensor cores start at Turing (7.0), so
  the compute-side speedup is largely absent. For `base`/`small`, CPU and CUDA
  are expected to be close; for `medium`/`large`, CUDA should win. **Must be
  measured — see Phase 0.**
- Realistic model ceiling is `medium`, not `large-v3-turbo`.
- **RAM is the tighter constraint than VRAM.** Only 1.5 GB was free at time of
  planning. Plan for on-demand model load/unload rather than resident models.

---

## 2b. The session — what this actually is

Derived from how the developer practises with his sheikh, and the reason nour
exists. Everything else in this plan serves this loop.

### The loop

```
1. AGENDA     App suggests a portion. "Today: Al-Mulk 1–10."
              Suggested from sequence and what is decaying. Overridable —
              name another surah and it follows you there.

2. BEGIN      You start reciting from memory, unprompted.
              No voice plays. No prompt. You begin because you know what
              today is. Maqam: the mic opens and the app is silent.

3. TRACK      The app knows every word that should come and follows you
              through it. It does not speak. It does not react.

4. LADDER     On a stall, it descends three rungs (see Phase 5):
              wait ~1s → first letter → full word
              Each rung costs more. Recovery at a lower rung costs less.

5. CONTINUE   The run never restarts. A correction is a pause, not a reset.
              You carry on from where the ladder left you.

6. SCORE      One run, one score, attached to the segment.
              Clean = 10. Recovered stumble = 9.5. Hint = −0.5, full word
              = −1.0. Repeated failure on the same ayah halves its share.

7. WISDOM     Only if the run was clean: a mutashabihat question, as
              encouragement and a bonus. Never the main event.
```

### What the app is

A listening teacher. It sets the agenda, knows the text, follows silently,
and catches you at the exact word. Not a recorder you check afterwards, and
not a reciter that plays at you.

### What makes this hard

The whole difficulty is **step 4** — knowing a stall from a pause from a
mistake, in real time, on hesitant recitation, without falsely correcting a
correct recitation. That is §4.4, and it is the only genuinely unsolved
engineering problem in the product.

### Deliberately excluded

- **Backward recitation (تراجع)** — not part of this practice. Out.
- **Restart on error** — the run is continuous by design.
- **Audio correction** — the word is spoken, not played by a reciter, by
  default. Reference playback is optional and separate.

## 3. Architecture decision
**Framework: Pipecat** (BSD-2, active, 16k+ stars).

Rationale:

- Has a `FastAPI Websocket` transport — matches the chosen backend stack
- Pipeline-based, so segmentation logic can be taken over without fighting
  the transport layer
- `pipecat-ai` CLI scaffolds projects for AI coding agents, which matches how
  this project will actually be built
- No per-minute cost; self-hostable; audio never leaves the machine

Rejected:

- **LiveKit** — assumes its own WebRTC server, and its turn model is the thing
  Nour must disable. Self-hosted localhost latency objection was withdrawn, but
  the abstraction cost stands.
- **Vapi / Retell / Bland** — phone-call infrastructure (SIP, PSTN, TCPA
  compliance), per-minute billing, no custom STT slot. Wrong category.
- **Raw WebSocket** — ~300–500 lines of plumbing we would own forever, for
  little gain given Pipecat fits the stack.

### Verified: local Quranic Whisper works natively

`pipecat.services.whisper.stt.WhisperSTTService` runs Whisper locally via
Faster Whisper (CTranslate2). No API key.

The model string is passed straight to `faster_whisper.WhisperModel`, which
accepts **any HuggingFace repo id or local path**. The `Model` enum
(`TINY`…`LARGE_V3_TURBO`) is only a convenience. So Quran fine-tuned models
plug in directly:

```python
from pipecat.services.whisper.stt import WhisperSTTService, Model
from pipecat.transcriptions.language import Language

stt = WhisperSTTService(
    settings=WhisperSTTService.Settings(
        model="tarteel-ai/whisper-base-ar-quran",
        language=Language.AR,
    ),
    device="cuda",          # or "cpu" — decide from Phase 0
    compute_type="int8",
)
```

### Division of responsibility

```
Pipecat           → transport, audio framing, pipeline runtime, serialization
Our processor     → buffering, waqf-aware segmentation, silence semantics
WhisperSTTService → local Quranic Whisper (Phase 0 picks the model)
Our code          → forced alignment, scoring, competence model
LLM / TTS         → challenge mode only; never in the recite path
```

---

## 4. Non-negotiable design rules

These are constraints discovered during research. Violating any of them breaks
the product, not just the implementation.

### 4.1 Never bias the decoder for error scoring

`WhisperSTTSettings` exposes `hotwords` and `initial_prompt`. Passing the
expected ayah text there would raise accuracy and **destroy error detection** —
the decoder smooths a wrong word toward the correct one, hiding the exact
mistake being looked for.

The quran-muaalem paper states the principle directly:

> "We chose CTC loss without language model integration because we aim to
> capture what the user actually said, not what they intended to say."

| Purpose | Biasing allowed? |
|---|---|
| Identifying *which* ayah the user is on | ✅ Yes — accuracy is all we want |
| Scoring *errors* within that ayah | ❌ No — constraints must stay external |

### 4.2 Segment at waqf marks, not arbitrary windows

Uthmani text encodes stopping points, available in the Tanzil / quranlab data we
fetch anyway:

| Mark | Meaning | Treatment |
|---|---|---|
| م | لازم — mandatory stop | Prime prompt point |
| ج | جواز — permissible stop | Likely prompt point |
| س | سكتة — short pause | Candidate |
| — | ayah boundary | Always a prompt point |

Prompting at a waqf mark is *more* natural than interrupting, because the
reciter is obliged to pause there anyway. Never prompt mid-flow.

This also solves long-ayah breathing: Al-Baqarah 2:282 requires mid-ayah
pauses, and those pauses coincide with legitimate stop points.

### 4.3 Recited ≠ tested

- `last_recited_at` — last spoken aloud, sight-assisted
- `last_tested_at` — last produced from memory with text hidden

**Only the second may support a mastery claim.** Someone can recite fluently
from the page and still not know it cold. Retrofitting this distinction later is
painful; build it in from the start.

### 4.4 Design for precision over recall

On religious content, a false positive ("you said that wrong" when you didn't)
is worse than a missed error. It erodes trust and can make someone second-guess
a correct recitation.

Concrete failure mode found in prior art: character-level similarity scoring on
a 2-character word (`من` vs `ما` → ratio 0.5) falls below any sensible threshold,
so the most common short words in the Quran are the ones most likely to be
falsely flagged. Word length must be factored into the score.

### 4.5 Word-level clean does not mean tashkeel correct

Word identity and vowel correctness are **different errors scored by different
mechanisms**, and a pass at one says nothing about the other.

- **Word level** — which word was said. Needs text normalization; tashkeel must
  be stripped because the ASR rarely emits it consistently.
- **Tashkeel / vowel level** — was the vowel right. Cannot be text comparison.
  Must be scored acoustically against the expected phonetic form.

So: **normalize for word matching, and never report a word-level pass as a
correctness verdict.** A recitation can be word-perfect and tashkeel-wrong, and
that is a real hifz mistake that a word-diff structurally cannot see.

Two traps:

- **Post-hoc diacritization does not work.** A diacritizer produces the
  *expected* tashkeel, so it would "correct" a wrong vowel into the right one and
  report clean. That is decoder biasing (§4.1) in another form.
- **Tashkeel-emitting ASR alone does not solve it either.** A model uncertain
  about the fatha on `حَرَم` emits the statistically likelier form, hiding the
  error. It also requires reference-aware scoring, not transcription.

Verified in `research/00-FINDINGS.md`: models that emit tashkeel exist but have
~5–9 downloads against 21,358 for the non-diacritics model, empty model cards,
no published tashkeel metrics, and inaccessible training data. Capability is
demonstrated; readiness is not.

**Consequence: the reference corpus must retain full Uthmani tashkeel, always.**
Layer-1 scoring strips it for comparison only.

---

## 5. Data sources

| Need | Source | Notes |
|---|---|---|
| Uthmani text + waqf marks | Tanzil / `quranlab/quran` on HF | 6,236 ayahs, Hafs ʿan ʿĀṣim, Kufan numbering |
| Tajweed annotations | Quran.com API v4 — `quran_tajweed_annotated.json` | rule class per character span, 6,236 verses |
| Word-by-word breakdown | Quran.com API v4 — `quran_words_api.json` | word text, position, transliteration |
| **Mutashabihat (parallel verses)** | **QurSim** (Sharaf & Atwell, 2012) | **7,679 pairs from Ibn Kathir's Tafsir.** Labels: strong 40%, related 48%, unrelated 11.5% |
| Reference recitation audio | everyayah.com / Quran.com recitations API | per-ayah, multiple reciters incl. Husary |
| Morphology | Quranic Arabic Corpus (`corpus.quran.com`) | ~77k words, GPL — verbatim only |
| **Per-word audio** | **`quranhive/quran_word_by_word_audio`** | **Already cut into single words. `SSS_AAA_WWW.mp3`. ~1.5 GB, CC-BY-4.0 (commercial OK). Reciter undocumented.** |
| **Word → audio mapping** | `quranhive/quran_word_by_word_audio_mapping` | `surah, ayah, word, arb_word, word_id (#67:1:3), wordplay (067_001_003)` |

Mutashabihat is the differentiator and is **already curated by classical
scholars**. Nour curates *from* QurSim rather than generating parallels with an
LLM, which would produce plausible but theologically wrong pairings.

### §5.1 Audio — two voices, not one

The app speaks in two registers, and conflating them is a correctness error.

| Register | Used for | Source |
|---|---|---|
| **The agent's own voice** | Commentary — encouragement, "again from here", "you always stumble on this one" | Browser Arabic TTS. **Unverified — see below.** |
| **The qari's voice** | The correct word itself | Pre-cut recitation audio. Never TTS. |

A text-to-speech voice must never model a Quranic word. It will shorten a madd
or drop a ghunnah with its own idea of the pronunciation, and a learner who
hears it wrong learns it wrong. That is worse than no correction at all. The
word is always a real recitation; the agent only carries the commentary.

**Verified on the target machine:** Windows desktop TTS is **English only**
(David, Zira). `Microsoft Hoda - Arabic (Egypt)` is registered at the OneCore
level, which is what Edge and Chrome use, so browser speech can probably reach
Arabic — but **this is not verified and must be tested in a browser before
anything depends on it.** If no acceptable Arabic voice exists, comments fall
back to on-screen text and only the words are spoken, which still works.

**Reciter choice:** Mahmoud Khalil Al-Husary. Two recitations exist and serve
different jobs —

- **Muallim** (teaching recitation, slower and more deliberate) — corrections
  and new material
- **Murattal** (standard pace) — everyday revision and listening

Both confirmed reachable via everyayah.com and quran.com recitation id 12.
`quran_word_by_word_audio` is a third option whose reciter is unknown; it needs
a listening test before adoption, and if it is not Husary it is not used.

**If no pre-cut word audio fits:** `qurani.io/quran-timing-helper` produces
word-level timings locally using Whisper plus wav2vec2 forced alignment, and
slicing follows directly. That is the fallback, not the first choice.

---

## 6. Model shortlist for Phase 0

| Model | Params | Licence | Notes |
|---|---|---|---|
| `tarteel-ai/whisper-base-ar-quran` | 74M | Apache-2.0 | **Benchmark first.** 5.75% WER, fits 4 GB, CPU+CUDA feasible |
| `tarteel-ai/whisper-tiny-ar-quran` | 39M | Apache-2.0 | 7.05% WER, 151 MB — the floor if base is too slow |
| `yousifgamalo/quran-s-finetuned` | 769M | Apache-2.0 | 1.27M samples; medium may be tight on 4 GB |
| `whisper-large-v3-turbo-ar-quran` | 809M | Apache-2.0 | 1.18% WER, but likely too slow on Pascal — measure |
| `whisper-quran-v1` (wasimlhr) | large-v3 | **CC-BY-NC-4.0** | ❌ **Non-commercial.** Best provenance, unusable if monetising |
| `obadx/muaalem-model-v3_2` | 0.6B | MIT | Phoneme-level, for Phase 8 |
| `whisper.cpp` | — | MIT | Alternative runtime, strong AVX2 CPU |

**Licensing must be verified per model before any monetization.** The mix
matters: the most impressive WER figures come from models that cannot be used
commercially. See `research/04-benchmark.md` for the full table.

---

## 7. Known gaps and risks

### 7.1 No interim transcription from local Whisper

`WhisperSTTService` is a `SegmentedSTTService`: one final transcript after the
user stops speaking. No partial results. Cloud STTs (Deepgram) stream interims;
local Whisper does not.

For Nour this matters — pauses run 1–5 seconds, so up to 5s of silence with no
feedback per hesitation.

Open PR pipecat#5009 proposes `WhisperStreamingSTTService` (tiny interim model
re-transcribing buffered audio every 0.25s, full model on silence). Not merged.
It also carries O(n²) cost as utterance length grows.

**Decision needed in Phase 2:** contribute that PR, or implement interim
transcription in our own processor.

### 7.2 Training data skew

The large published WER numbers are measured on fluent *professional*
recitation. Our use case is hesitant memory recitation — pauses, restarts,
self-corrections. The gap is real but narrower than feared: QDAT and
`qdat_bench` contain authentic learner errors recorded over WhatsApp at 11 kHz.

**This is precisely why Phase 0 exists.**

### 7.3 Reference audio during capture

Playing a reference recitation while the mic is open means the mic hears it.
Needs either capture-pause during playback or real echo cancellation. Revisit
when Phase 6 lands.

### 7.4 RAM pressure

1.5 GB free. Models should load and unload on demand, not sit resident.

---

## 8. Phases

### Phase 0 — Evaluation harness *(before any product code)*

**Nothing else starts until this tells us which model to build on.**

**Do not build a scoring harness.** Use `jiwer` for WER/CER and `WhisperX` for
VAD, word timestamps and forced alignment. The only thing written from scratch
is the runner that ties them together over a clip manifest, plus one thing
nobody provides: separating *true errors* from *hesitation artifacts*.

- Record ~30 clips of **imperfect, hesitant recitation** across several surahs.
  Phone voice memos are fine. These are the developer's own — the corpus does
  not exist publicly in this form.
- Label ground truth per clip.
- Test matrix: `{tarteel-base, tarteel-tiny, medium} x {cpu int8, cuda int8}`,
  plus `whisper.cpp` on CPU.
- Metrics via `jiwer`:
  - WER / CER
  - **p50 and p95 latency per chunk** ← decides CPU vs CUDA
  - per-ayah error attribution
  - **true errors vs hesitation artifacts** — a model may report a substitution
    that is actually a mid-word pause. Without separating these, tuning runs
    against noise. **This is the one novel piece.**
- `quraniio/quran-timing-helper` has a useful idea to copy: a validator that
  flags alignments too poor to trust. Any clip whose alignment quality is
  ambiguous should be excluded rather than scored.
- Output: a comparison table that makes the model + device decision

**Reference implementation to read before writing anything:**
`foyzulkarim/hifz-tester` (MIT) implements the same transcription →
normalise → deterministic-align pipeline this plan describes, in a local
single-user web app. It is the closest prior art to Phases 0–3. Read it before
building; adopt its alignment approach where it fits.

Clip storage: gitignored by default (personal audio). A few sanitised clips are
worth committing as CI regression fixtures — decide explicitly.

### Phase 1 — Data foundation

Fetch and normalize Quran text, waqf marks, tajweed annotations, QurSim, and
reference audio. Version them. Write validation so a bad fetch fails loudly.

### Phase 2 — Audio pipeline

- Pipecat with `FastAPI Websocket` transport
- `WhisperSTTService` with the Phase 0 winner
- **Retune silence thresholds for recitation** — Pipecat's defaults assume
  conversational pauses of 0.1–0.3s; ours are 1–5s
- Waqf-aware segmentation in a custom processor
- Resolve the interim-transcription question (§7.1)
- Feedback over a data channel as text, never TTS during recitation

### Phase 3 — Alignment and scoring

- Forced alignment of the transcript against expected text
- Token F1 + IDF-weighted matching (the approach proven by `whisper-quran-v1`)
- Error classes: substitution / deletion / insertion, at word granularity
- Hesitation detection, with duration and position
- Respect §4.1 — no decoder biasing in this path

### Phase 4 — Competence model *(this is the product)*

Per-ayah, with:

- `state` — unseen → read → learning → shaky → fluent_forward → fluent_both →
  retained → lapsed
- `last_recited_at`, `last_tested_at` (§4.3)
- `consecutive_clean`, decaying `recent_error_rate`, `hesitation_count`
- `rung_reached` — deepest rung the user needed on this ayah, by attempt

Scheduling:

- **Tested at range granularity, stored at ayah granularity.** Nobody recites
  isolated ayahs well; performance is continuous.
- On a weak ayah, pull in **neighbours ±2** — classical mnemonic anchoring,
  encoded into scheduling.
- Retention decay drives the review queue.

#### What the competence model drives

The competence model is not a passive record. It is the **input to every
downstream decision**, which is why it is the product rather than a feature:

- **← Phase 3 (scoring).** Alignment and scoring produce the evidence. Every
  error class, hesitation event, and rung reached writes into a per-ayah
  competence record. Without scoring there is nothing to model.
- **→ Phase 5 (prompt ladder).** Not a policy — the ladder is fixed, only the
  wait durations are tunable. The competence history supplies the starting
  durations per user rather than them being global constants.
- **→ Phase 6 (feedback).** Competence state decides **whether** feedback is
  warranted and how urgently. A lapsed ayah gets immediate intervention; an
  already-fluent ayah does not need correction noise.
- **→ Phase 5½ (scoring).** The halving rule reads competence history: whether
  this ayah has failed before determines whether a new failure halves it.
- **→ Phase 7 (mutashabihat challenge).** Challenge selection is gated on
  competence state. Probe what is strong to deepen it, consolidate what is
  shaky. **Never challenge something the user cannot yet recite** — that is
  demoralising, not pedagogic.

Downstream phases read competence state rather than making independent
judgements. If a later phase needs to decide something, it asks the competence
model first.

### Phase 5 — The prompt ladder

**Not a learned policy.** A fixed three-rung ladder with one tunable: how long
silence may run at each rung. Established with the developer from how his sheikh
actually corrects him, replacing an earlier `P(failure | hesitation)` design that
was over-built.

```
you stumble
   ↓
RUNG 0: app waits ~1s          ← you may find it yourself (no cost)
   ↓
RUNG 1: first letter(s) spoken ← usually enough    → −0.5
   ↓
RUNG 2: the full word spoken   ← genuinely lost    → −1.0
   ↓
you carry on either way — NO RESTART
```

Costs are equal, but rung 1 costs half because it *worked*: the memory was there
and only needed the door opened.

Details:

- All feedback is **spoken** (voice interaction throughout). The mic pauses while
  the app speaks — no voice-over-voice, and no AEC needed.
- Rung durations are user-tunable. Start at ~1s, adjust against real practice.
- **Never rung below a correct recitation.** Only after a demonstrated stall.
- Wait at least a natural pause — never interrupt mid-word (see §4.2).

Why not a learned policy: the ladder is fixed by how correction actually works.
The only open variable is timing, and that is one number the user can tune.
Learning it was solving a problem that does not exist.

### Phase 6 — Feedback delivery

How the ladder reaches the user, and what is recorded.

- Spoken rungs, mic muted during speech, resumed on completion
- Waqf-aware: only prompt where the reciter was always going to pause (§4.2)
- Reference recitation playback is **optional and separate** — the default
  correction is the word itself, not a reciter's voice
- Feedback history, browsable
- Per-intervention records feed the competence model (§Phase 4)

### Phase 5½ — Scoring

A session is **one continuous run** through the suggested portion. Corrections
are pauses, not resets — the run never restarts.

| Event | Cost |
|---|---|
| Recovered unaided | −0.5 |
| Rung 1 hint, then correct | −0.5 |
| Rung 2 full word | −1.0 |
| Same ayah failing again | its contribution halves |

- The score attaches to the **segment** ("Al-Mulk 1–10 = 7/10"), not the ayah.
- A recovered stumble is a 9.5, not a 10 — small cost, not fatal.
- Repeated failure on the same ayah is the real signal: one miss is forgiven,
  three in a row says the junction is not solid.
- The halving rule is the only decay-like mechanic in scoring; §Phase 4 handles
  the rest over time.

### Phase 7 — Mutashabihat challenge *(the differentiator)*

Consumes the competence model (§Phase 4) to decide *what* to ask. Selection is
gated on competence state: deepen what is strong, consolidate what is shaky,
and never probe something the user cannot yet recite.

- QurSim-backed parallel-verse selection
- Challenge generation when a recitation is clean
- Never interrupt; surface at a natural stop

### Phase 8 — Tajweed *(later)*

`quran-muaalem` (arXiv 2509.00094, ICML 2026) is open source and is effectively
a research preview of this phase: 848h annotated, Quran Phonetic Script with 11
levels, **75.8% Tajweed F1** on real learner errors. The model
`obadx/muaalem-model-v3_2` is 0.6B params on an **MIT** licence, so it is
commercially usable where `whisper-quran-v1` is not.

**But this is a crowded space, not an open one.** At least six products already
claim makharij, ghunnah, madd and qalqalah detection. None has published
validated metrics. So the question is not "can we do tajweed" but "can we do it
measurably better than products whose quality is unknown" — which is an
argument for holding to the precision bar in §4.4, not a reason to skip the
phase.

Madd length is directly measurable — time the vowel, compare to the required
2/4/6 counts. No model training required.

---

## 9. Repo structure

```
nour/
├── backend/
│   ├── app/                    FastAPI + Pipecat pipeline
│   ├── nour/
│   │   ├── alignment/          forced alignment, token matching
│   │   ├── scoring/            error classification, hesitation
│   │   ├── competence/         state machine, retention, scheduling
│   │   ├── feedback/           prompt policy, reference playback
│   │   └── content/            qursim, tajweed, Quran text access
│   └── tests/
├── frontend/                   Vite + React + TS
├── data/                       versioned corpora
├── models/                     downloaded weights (gitignored)
├── eval/
│   ├── clips/                  recordings (gitignored)
│   ├── ground_truth/
│   └── run_eval.py
├── scripts/
├── docker/
└── .github/workflows/
```

Stack: FastAPI + Pipecat (Python) · Vite + React + TypeScript. React chosen
because agent code-generation quality matters more than framework elegance, and
the audio work is raw Web Audio either way.

---

## 9b. People and sequencing strategy

Decisions taken during research, recorded so they are not re-litigated.

### The sequencing principle

**Build the tool; let the tool generate what it needs.** Four separate
proposals were all variations of *build the institution first*:

| Proposal | Why deferred |
|---|---|
| Dataset collection initiative | Months of coordination, consent and annotation standards, with no product to show. The product *is* the collection mechanism — every user reciting into it generates the exact data, already labelled because the ayah is known. |
| Fine-tuning before alignment | Only public data is professional/fluent recitation, so fine-tuning on it reproduces Tarteel's 2021 model. Fine-tune only where alignment *demonstrably* fails, measured on the benchmark. |
| Academy partnership | Segmentation answered later, if at all. |
| Paid crowd data collection | Solves the pivot's problem, not the product's. Users generate it for free once the tool exists. |

All four are real options. None is needed before a working tool exists. The
tool is what makes them cheap.

### Data strategy

- **Phase 0:** the developer's own ~30 hesitant clips as a personal regression
  set, plus `Quran-Lab/quranic-asr-benchmark` (600 leakage-free clips, including
  200 real phone-mic recitations) as the objective instrument. Live leaderboard at
  `huggingface.co/spaces/Muno459/quranic-asr-leaderboard`.
- **Long term:** the flywheel. Real users, consent given, ground truth already
  known. This is the only recitation data the project would ever own — the
  benchmark is research-licensed and cannot ship.
- **Paid pilot:** gated, Phase 6 at the earliest, and only if the academy
  channel (§12) survives. 20–30 clips from real non-native learners via academy
  contacts, $200–500. A probe, not a dataset initiative.

### People — two tracks, different urgency

**Track 1 — immediate, this month.** Find *any* competent Quran teacher for a
30-minute clip review. Does not need to be technical. This is the highest-value
unresolved risk in the project: §4.4 precision. Nobody but a person who corrects
Quran for a living can say *"you flagged this but it is actually acceptable."*

The ask, verbatim:

> *"I'm building a tool that listens to Quran recitation and flags mistakes — for
> myself first. I want to check my error detection against human judgement before
> I trust it. Could you look at 20 recordings of me reciting, tell me where I
> actually made mistakes, and where I didn't but the tool would have flagged
> them?"*

Expected outputs: the developer's own error calibration, a false-positive list,
and a relationship. No commitments either way.

**Track 2 — parallel, not gating.** Someone who is *both* technically capable and
religiously credible is a genuine asset, and rarer: they can judge a tajweed
error and an engineering tradeoff in the same conversation, and they would have
standing in the academy community that the developer does not. Egypt is a
favourable place for this — large technical population with deep memorisation
culture.

**But do not make Track 2 a prerequisite.** It would block Track 1, which is
cheap and needed now, on a search that could take a year. The precision problem
does not care whether the reviewer can write code.

If a Track 2 person appears, start them exactly where a Track 1 teacher would
start: reviewing clips. See how it feels before it becomes a commitment — and
note that co-founding is a different project from *"mainly for me."*

### Honest framing

There is no uncontested gap. Every differentiation claim tested during research
was either wrong or narrower than stated. What is true: many people have built
pieces, nobody has shipped the competence model, and the reason is structural —
hard problem, low willingness to pay — which is precisely the shape a solo
builder with a real personal use case can work in without venture funding.

Aim for *a tool that is genuinely useful and happens to be possible now that the
pieces are free*, not for a defensible moat.

---

## 10. Process

Solo developer, agent-driven (OpenCode + ensemble teams), production-grade.

### Ensemble configuration

**`mergeOnCleanup` must be `false`** (currently `true` in the global
`ensemble.json`). Auto-merging teammate branches on cleanup means agent changes
land in the working tree unreviewed. On a solo project the developer is the only
reviewer — that is the entire safety mechanism.

Use ensemble for work with clean boundaries: research spikes, parallel
exploration, tests, docs, migration scripts. Review the diff before
`team_merge`.

### Branch and PR discipline

A PR on a solo project is not collaboration — it is a **self-review checkpoint
with automated gates**. That is its value.

- Feature branches, PR to main, never direct commits to main
- CI gates: lint, typecheck, test, Docker build, migration check
- Audio fixtures: a handful of committed reference clips for regression tests

### Environments

- Local: Docker Compose, hot reload
- Production: containerised, SQLite (v1) → Postgres when multi-user arrives

---

## 11. Open questions

1. Where do eval clips live, and which are committed as fixtures?
2. Is feedback visual-only, or does the reference clip play automatically?
3. Reference reciter default — Husary is ubiquitous but preference is personal.
4. Is the tajweed model license compatible with eventual monetization?
5. Which Quranic reciter audio licenses permit commercial use?
6. **Market sizing is unvalidated.** The 5–20M SAM estimate is unsourced and
   was flagged as speculation by two independent reviews. No global census of
   active memorizers exists. Do not build a forecast on it.
7. **Arabic-only UI is a documented liability** for non-native learners.
   Correct for the current target segment, but it forecloses a known option.

---

## 12. Open exploration — non-native academies

Investigated and **not recommended as a pivot**, but not closed either.

Western academies predominantly teach reading, tajweed and short-surah
memorisation with text visible; full hifz is a separate, selective track.
Dedicated programs exist with real scale, but **no census exists** for the
segment, so it cannot be sized.

**What changes the picture:** the developer has direct access to specialised
academies. Reachability — one of the four main objections — is answered.

**Kill criterion: five academy conversations. If fewer than 2 of 5 say
phonetic-level feedback would save them real time, drop it.** The six questions
to ask are listed in `research/00-FINDINGS.md` §5.

**Note this contradicts "mainly for me."** A native speaker does not need
phoneme feedback; a non-native speaker does not need retention decay. They are
different products, and pursuing this means building for others first.

---

## 13. Status

- [x] Competitive research
- [x] Hardware verified
- [x] Pipecat local-Whisper capability verified
- [x] Silence semantics defined (waqf-aware)
- [x] Hesitation policy defined (adaptive)
- [x] Data sources identified
- [x] Market / competitor / business / benchmark research
- [x] Non-native pivot investigated
- [ ] Five academy conversations (kill criterion above)
- [ ] Eval clips recorded
- [ ] Phase 0 complete
- [ ] Phase 1 onward