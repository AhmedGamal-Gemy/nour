# Graph Report - nour  (2026-10-12)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 30 nodes · 24 edges · 9 communities (5 shown, 4 thin omitted)
- Extraction: 54% EXTRACTED · 46% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.85)
- Token cost: 1,699 input · 2,378 output

## Graph Freshness
- Built from commit: `7a370c17`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Quran AI Tools
- Quran Text Resources
- Speech Transcription Tools
- Hardware Resource Constraints
- Voice AI Platforms
- Agent Documentation Tools
- Quran Tajweed Resources
- Precision Metrics
- Recitation Assessment

## God Nodes (most connected - your core abstractions)
1. `Nour` - 7 edges
2. `WhisperSTTService` - 5 edges
3. `Pipecat` - 4 edges
4. `Uthmani Text` - 3 edges
5. `Mutashabihat Challenge` - 2 edges
6. `Segment at Waqf Marks` - 2 edges
7. `Hardware Constraints` - 2 edges
8. `Phase 0 - Evaluation Harness` - 2 edges
9. `Quranic Whisper Models` - 2 edges
10. `Competence Model` - 1 edges

## Surprising Connections (you probably didn't know these)
- `Nour` --references--> `Pipecat`  [EXTRACTED]
  PLAN.md → PLAN.md  _Bridges community 0 → community 4_
- `Pipecat` --references--> `WhisperSTTService`  [EXTRACTED]
  PLAN.md → PLAN.md  _Bridges community 2 → community 4_
- `WhisperSTTService` --references--> `Quranic Whisper Models`  [EXTRACTED]
  PLAN.md → PLAN.md  _Bridges community 2 → community 3_

## Hyperedges (group relationships)
- **Core Design Rules** — plan_decoder_bias_rule, plan_waqf_segmentation_rule, plan_recited_not_tested_rule, plan_precision_over_recall_rule [EXTRACTED 1.00]
- **Quran Data Sources** — plan_tanzil, plan_quranlab, plan_tajweed, plan_qursim, plan_uthmani_text [EXTRACTED 1.00]
- **Nour Architecture Stack** — plan_nour, plan_pipecat, plan_fastapi, plan_react, plan_whispersttservice, plan_faster_whisper [INFERRED 0.90]

## Communities (9 total, 4 thin omitted)

### Community 0 - "Quran AI Tools"
Cohesion: 0.25
Nodes (8): Competence Model, FastAPI, Hesitation Signal, Mutashabihat Challenge, Nour, QurSim, React, Tarteel

### Community 1 - "Quran Text Resources"
Cohesion: 0.40
Nodes (5): quranlab/quran, Tanzil, Uthmani Text, Waqf Marks, Segment at Waqf Marks

### Community 2 - "Speech Transcription Tools"
Cohesion: 0.50
Nodes (4): Never Bias Decoder for Error Scoring, Faster Whisper, No Interim Transcription, WhisperSTTService

### Community 3 - "Hardware Resource Constraints"
Cohesion: 0.50
Nodes (4): Hardware Constraints, Phase 0 - Evaluation Harness, Quranic Whisper Models, RAM Pressure

### Community 4 - "Voice AI Platforms"
Cohesion: 0.67
Nodes (3): LiveKit, Pipecat, Vapi / Retell / Bland

## Knowledge Gaps
- **20 isolated node(s):** `Competence Model`, `FastAPI`, `Hesitation Signal`, `QurSim`, `React` (+15 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 21 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Nour` connect `Quran AI Tools` to `Voice AI Platforms`?**
  _High betweenness centrality (0.239) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `WhisperSTTService` (e.g. with `Never Bias Decoder for Error Scoring` and `No Interim Transcription`) actually correct?**
  _`WhisperSTTService` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Competence Model`, `FastAPI`, `Hesitation Signal` to the rest of the system?**
  _20 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Why does `Pipecat` connect `Voice AI Platforms` to `Quran AI Tools`, `Speech Transcription Tools`?**
  _High betweenness centrality (0.239) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Pipecat` (e.g. with `LiveKit` and `Vapi / Retell / Bland`) actually correct?**
  _`Pipecat` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Why does `WhisperSTTService` connect `Speech Transcription Tools` to `Hardware Resource Constraints`, `Voice AI Platforms`?**
  _High betweenness centrality (0.227) - this node is a cross-community bridge._