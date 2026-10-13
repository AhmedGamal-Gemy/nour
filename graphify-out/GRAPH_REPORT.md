# Graph Report - nour  (2026-10-13)

## Corpus Check
- 3 files · ~12,000 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 67 nodes · 80 edges · 9 communities (8 shown, 1 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Audio Pipeline
- Competence Model
- Research Findings
- Quranic Content
- Strategy & People
- Design Rules & Precision
- Phase Roadmap
- Community 7
- Community 8

## God Nodes (most connected - your core abstractions)
1. `Competence model` - 9 edges
2. `Phase 0 - Evaluation harness` - 7 edges
3. `Phase 1 - Data foundation` - 6 edges
4. `9b People and sequencing strategy` - 6 edges
5. `Architecture: Pipecat + local Whisper` - 5 edges
6. `Uthmani text with tashkeel` - 5 edges
7. `Phase 6 - Feedback and reference playback` - 5 edges
8. `WhisperSTTService` - 4 edges
9. `4.5 Word-clean is not tashkeel-correct` - 4 edges
10. `Adaptive hesitation policy` - 4 edges

## Surprising Connections (you probably didn't know these)
- `What survives as defensible` --conceptually_related_to--> `Competence model`  [EXTRACTED]
  research/00-FINDINGS.md → PLAN.md
- `Tashkeel-emitting ASR is unready` --conceptually_related_to--> `4.5 Word-clean is not tashkeel-correct`  [EXTRACTED]
  research/00-FINDINGS.md → PLAN.md
- `What survives as defensible` --conceptually_related_to--> `QurSim mutashabihat (7,679 pairs)`  [EXTRACTED]
  research/00-FINDINGS.md → PLAN.md
- `Recorded corrections` --conceptually_related_to--> `obadx/muaalem-model-v3_2`  [EXTRACTED]
  research/00-FINDINGS.md → PLAN.md
- `Strategy: build the tool first` --references--> `9b People and sequencing strategy`  [EXTRACTED]
  AGENTS.md → PLAN.md

## Hyperedges (group relationships)
- **Audio pipeline stack** — plan_pipecat, plan_whispersttservice, plan_faster_whisper, plan_int8, plan_hardware [EXTRACTED 1.00]
- **What the competence model drives** — plan_competence, plan_retention, plan_hesitation, plan_backward, plan_neighbours, plan_hesitation_policy [EXTRACTED 1.00]
- **Five non-negotiable design rules** — rule_decoder_bias, rule_waqf, rule_recited_tested, rule_precision, rule_tashkeel [EXTRACTED 1.00]

## Communities (9 total, 1 thin omitted)

### Community 0 - "Audio Pipeline"
Cohesion: 0.14
Nodes (13): Do not reinvent the wheel, Architecture: Pipecat + local Whisper, Faster Whisper / CTranslate2, Hardware: Pascal CC6.1, no tensor cores, foyzulkarim/hifz-tester (MIT), int8 compute type, No interim transcription from local Whisper, LiveKit (+5 more)

### Community 1 - "Competence Model"
Cohesion: 0.25
Nodes (11): Backward recitation (taraji'), Competence model, Hesitation as first-class signal, Adaptive hesitation policy, Neighbour anchoring (+/-2 ayah), Phase 4 - Competence model, Phase 5 - Adaptive hesitation policy, Phase 6 - Feedback and reference playback (+3 more)

### Community 2 - "Research Findings"
Cohesion: 0.22
Nodes (9): graphify wiring, Recorded corrections, Speculative claims (unsourced SAM), Tashkeel-emitting ASR is unready, Unknown - no public data exists, Verified claims, obadx/muaalem-model-v3_2, Tajweed annotations (+1 more)

### Community 3 - "Quranic Content"
Cohesion: 0.33
Nodes (7): What survives as defensible, Phase 1 - Data foundation, Phase 7 - Mutashabihat challenge, Phase 8 - Tajweed, QurSim mutashabihat (7,679 pairs), Tilawa/QariAI/TajweedMate et al, Tarteel (15M users)

### Community 4 - "Strategy & People"
Cohesion: 0.40
Nodes (6): Strategy: build the tool first, Non-native academy exploration, Fine-tune only on eval evidence, Paid pilot (gated, Phase 6), 9b People and sequencing strategy, Track 2 - technical + religious collaborator

### Community 5 - "Design Rules & Precision"
Cohesion: 0.40
Nodes (6): Forced alignment + Token F1/IDF, Phase 3 - Alignment and scoring, Short-word false-positive bug, Track 1 - teacher clip review, 4.1 Never bias the decoder for error scoring, 4.4 Precision over recall

### Community 6 - "Phase Roadmap"
Cohesion: 0.33
Nodes (6): p50/p95 latency per chunk, Model licensing and CC-BY-NC-4.0, Phase 0 - Evaluation harness, Quran-Lab/quranic-asr-benchmark, tarteel-ai/whisper-base-ar-quran, tarteel-ai/whisper-tiny-ar-quran

### Community 7 - "Community 7"
Cohesion: 0.33
Nodes (6): Phase 2 - Audio pipeline, quranlab/quran, Tanzil, Uthmani text with tashkeel, Waqf marks (lazim/jaiz/saktah), 4.2 Segment at waqf marks

## Knowledge Gaps
- **24 isolated node(s):** `Stack: FastAPI + React`, `Pipecat`, `RAM pressure (1.5GB free)`, `p50/p95 latency per chunk`, `No interim transcription from local Whisper` (+19 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 25 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Phase 1 - Data foundation` connect `Quranic Content` to `Competence Model`, `Research Findings`, `Phase Roadmap`, `Community 7`?**
  _High betweenness centrality (0.290) - this node is a cross-community bridge._
- **What connects `Stack: FastAPI + React`, `Pipecat`, `RAM pressure (1.5GB free)` to the rest of the system?**
  _24 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Audio Pipeline` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._
- **Why does `Phase 0 - Evaluation harness` connect `Phase Roadmap` to `Quranic Content`, `Strategy & People`?**
  _High betweenness centrality (0.222) - this node is a cross-community bridge._
- **Why does `Competence model` connect `Competence Model` to `Quranic Content`?**
  _High betweenness centrality (0.148) - this node is a cross-community bridge._