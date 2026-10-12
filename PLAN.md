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

**Conclusion: mistake detection is commodity. Do not build Nour's identity on it.**

Where Nour wins:

| Area | Tarteel | Nour |
|---|---|---|
| Progress signal | streaks, heatmaps (activity) | retention decay model |
| Test placement | user-chosen | scheduled from weakness |
| Weakness signal | recent errors | decay + hesitation + neighbour anchoring |
| Recitation direction | forward | forward **and** backward (تراجع) |
| On a clean recitation | nothing happens | **mutashabihat challenge** |
| Hesitation | not tracked | first-class signal |
| Pronunciation | — | madd / ghunnah measurement (later) |

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

Mutashabihat is the differentiator and is **already curated by classical
scholars**. Nour curates *from* QurSim rather than generating parallels with an
LLM, which would produce plausible but theologically wrong pairings.

---

## 6. Model shortlist for Phase 0

| Model | Params | Notes |
|---|---|---|
| `tarteel-ai/whisper-base-ar-quran` | 74M | small, fast, CPU-viable |
| `whisper-quran-v1` (wasimlhr) | large-v3 | 5.35% WER, real-time verse tracking; too big here |
| `whisper-large-v3-turbo-ar-quran` | 809M | 1.18% WER; **likely too slow on Pascal**, but measure |
| `yousifgamalo/quran-s-finetuned` | medium | 1.27M samples, Apache-2.0 |
| `whisper.cpp` | — | alternative runtime, strong AVX2 CPU performance |

**Licensing must be verified per model before any monetization** — some
Quranic models carry `cc-by-nc-4.0`, which blocks commercial use. `openai/whisper`
itself is MIT.

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

- Record ~30 clips of **imperfect, hesitant recitation** across several surahs
- Label ground truth per clip
- Test matrix: {base, small, medium} × {cpu int8, cuda int8} + `whisper.cpp`
- Metrics:
  - WER / CER
  - **p50 and p95 latency per chunk** ← decides CPU vs CUDA
  - per-ayah error attribution
  - **true errors vs hesitation artifacts** — a model may report a substitution
    that is actually a mid-word pause. Without separating these, tuning runs
    against noise.
- Output: a comparison table that makes the model + device decision

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
- `recall_direction` — forward / backward

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
  error class, hesitation event, and hesitation outcome writes into a per-ayah
  competence record. Without scoring there is nothing to model.
- **→ Phase 5 (hesitation policy).** `P(failure | hesitation, context)` is
  *computed from the competence history* — it is not a static per-user setting.
  The hesitation events recorded against each ayah are exactly the samples the
  policy is estimated from.
- **→ Phase 6 (feedback).** Competence state decides **whether** feedback is
  warranted and how urgently. A lapsed ayah gets immediate intervention; an
  already-fluent ayah does not need correction noise. The hesitation policy
  decides *when* to speak; competence state decides *whether it matters*.
- **→ Phase 7 (mutashabihat challenge).** Challenge selection is gated on
  competence state. Probe what is strong to deepen it, consolidate what is
  shaky. **Never challenge something the user cannot yet recite** — that is
  demoralising, not pedagogic.

Downstream phases read competence state rather than making independent
judgements. If a later phase needs to decide something, it asks the competence
model first.

### Phase 5 — Adaptive hesitation policy

Per-user learned policy, not a hardcoded rule. Its evidence is the competence
model's hesitation history (§Phase 4) — this phase estimates a policy over that
history rather than keeping a separate record of its own.

- Log every hesitation: duration, position, outcome (recalled within Ns / failed)
- Maintain `P(failure | hesitation, context)` per user
- Prompt when it crosses a threshold

Guardrails:

- **Cold start is optimistic** — silent, generous timeout. Eager prompting in
  early sessions would feel hostile and teach distrust.
- **Pool globally, smooth per-passage.** Strong global prior, local nudges. 20
  hesitation samples per ayah is not a signal.
- **Never prompt when they are reciting correctly** — only after a demonstrated
  failure.

### Phase 6 — Feedback and reference playback

Competence state gates what gets feedback (§Phase 4); the hesitation policy
gates when (§Phase 5). This phase decides *how*.

- Prompt at mandatory / permitted waqf marks, ayah boundaries, or breath pauses
- Play reference recitation from the point of failure; user-selectable reciter
  (preference here is strong and personal)
- Resolve the AEC / capture-pause question (§7.3)
- Feedback history, browsable

### Phase 7 — Mutashabihat challenge *(the differentiator)*

Consumes the competence model (§Phase 4) to decide *what* to ask. Selection is
gated on competence state: deepen what is strong, consolidate what is shaky,
and never probe something the user cannot yet recite.

- QurSim-backed parallel-verse selection
- Challenge generation when a recitation is clean
- Never interrupt; surface at a natural stop

### Phase 8 — Tajweed *(later)*

`quran-muaalem` (arXiv 2509.00094, ICML 2026) is open source and is effectively
a research preview of this phase: 848h annotated, 848–890h corpus, Quran
Phonetic Script with 11 levels, **75.8% Tajweed F1** on real learner errors.

Madd length is directly measurable — time the vowel, compare to the required
2/4/6 counts. No model training required.

Verify its license before building on it.

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

---

## 12. Status

- [x] Competitive research
- [x] Hardware verified
- [x] Pipecat local-Whisper capability verified
- [x] Silence semantics defined (waqf-aware)
- [x] Hesitation policy defined (adaptive)
- [x] Data sources identified
- [ ] Eval clips recorded
- [ ] Phase 0 complete
- [ ] Phase 1 onward