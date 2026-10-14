# Graph Report - nour  (2026-10-14)

## Corpus Check
- 3 files · ~14,000 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 92 nodes · 114 edges · 10 communities
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 3 edges (avg confidence: 0.78)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Competence Model
- Cursors & Scheduling
- Audio Pipeline & Architecture
- The Two Voices
- Phase Roadmap
- Competitors & Prior Art
- The Session Loop
- Community 7
- Strategy & People
- Research Findings

## God Nodes (most connected - your core abstractions)
1. `Competence model` - 12 edges
2. `The seven-step loop` - 8 edges
3. `2b The session` - 6 edges
4. `4 Ladder - three rungs` - 6 edges
5. `6 Score - one run, one segment score` - 6 edges
6. `Architecture: Pipecat + local Whisper` - 5 edges
7. `WhisperSTTService` - 5 edges
8. `The qari's voice` - 5 edges
9. `Phase 1 - Data foundation` - 5 edges
10. `Phase 5 - The prompt ladder` - 5 edges

## Surprising Connections (you probably didn't know these)
- `What survives as defensible` --conceptually_related_to--> `QurSim mutashabihat (7,649 pairs)`  [EXTRACTED]
  research/00-FINDINGS.md → PLAN.md
- `What survives as defensible` --conceptually_related_to--> `Competence model`  [EXTRACTED]
  research/00-FINDINGS.md → PLAN.md
- `5 Continue - never restart` --conceptually_related_to--> `AGENTS: do not reinvent the wheel`  [INFERRED]
  PLAN.md → AGENTS.md
- `foyzulkarim/hifz-tester (MIT)` --references--> `AGENTS: do not reinvent the wheel`  [EXTRACTED]
  PLAN.md → AGENTS.md

## Hyperedges (group relationships)
- **Two voices: agent and qari** — aud_agent_voice, aud_qari_voice, aud_husary_muallim, aud_word_dataset [EXTRACTED 1.00]
- **Five non-negotiable design rules** — rule_decoder_bias, rule_waqf, rule_recited_tested, rule_precision, rule_tashkeel [EXTRACTED 1.00]
- **The three-rung prompt ladder** — lad_wait, lad_hint, lad_word [EXTRACTED 1.00]
- **The seven-step session loop** — sess_agenda, sess_begin, sess_track, sess_ladder, sess_continue, sess_score, sess_wisdom [EXTRACTED 1.00]
- **The three session segments** — seg_near_old, seg_long_term, seg_new [EXTRACTED 1.00]
- **Two cursors and the gap** — cur_memorize, cur_revision, cur_gap, cur_override, cur_fail_gate [EXTRACTED 1.00]

## Communities (10 total, 0 thin omitted)

### Community 0 - "Competence Model"
Cohesion: 0.20
Nodes (14): What survives as defensible, Ladder is fixed, not learned, Competence model, Neighbour anchoring (+/-2), Phase 5.5 - Scoring, Phase 2 - Audio pipeline, Phase 3 - Alignment and scoring, Phase 4 - Competence model (+6 more)

### Community 1 - "Cursors & Scheduling"
Cohesion: 0.21
Nodes (11): Fail gate - no new material, The gap (measure, do not choose), Memorize cursor, Revision cursor, Nour, 2b The session, Tasmeea partner (listening teacher), 4.3 Recited is not tested (+3 more)

### Community 2 - "Audio Pipeline & Architecture"
Cohesion: 0.18
Nodes (12): Architecture: Pipecat + local Whisper, Desktop-first, VPS later, Faster Whisper / CTranslate2, Hardware: Pascal CC6.1, no tensor cores, int8 compute type, No interim transcription, LiveKit (rejected), Pipecat (+4 more)

### Community 3 - "The Two Voices"
Cohesion: 0.25
Nodes (11): The agent's own voice, Browser Arabic voice - unverified, Husary Muallim (corrections), Husary Murattal (revision), The qari's voice, quran-timing-helper (fallback), quranhive per-word audio, Rung 1 - first letters (-0.5) (+3 more)

### Community 4 - "Phase Roadmap"
Cohesion: 0.18
Nodes (11): Model licensing (CC-BY-NC), Phase 0 - Evaluation harness, Phase 1 - Data foundation, quranlab/quran, Quran-Lab/quranic-asr-benchmark, Tajweed annotations, Tanzil, Uthmani text with tashkeel (+3 more)

### Community 5 - "Competitors & Prior Art"
Cohesion: 0.25
Nodes (8): Never TTS a Quranic word, Tilawa/QariAI/TajweedMate et al, Tarteel (15M users), Tarteel mutashabihat - lookup only, obadx/muaalem-model-v3_2, Phase 8 - Tajweed, 4.5 Word-clean is not tashkeel-correct, Why new material is sighted

### Community 6 - "The Session Loop"
Cohesion: 0.25
Nodes (8): foyzulkarim/hifz-tester (MIT), The seven-step loop, AGENTS: do not reinvent the wheel, 1 Agenda - suggested portion, 2 Begin - unprompted, from memory, 5 Continue - never restart, 3 Track - silent, knows the text, 7 Wisdom - mutashabihat if clean

### Community 7 - "Community 7"
Cohesion: 0.29
Nodes (7): Selection is mechanical, Decay-overrun override, Clean run = 10, Repeat failure halves the ayah, Score attaches to the segment, Recovered stumble = 9.5, 6 Score - one run, one segment score

### Community 8 - "Strategy & People"
Cohesion: 0.40
Nodes (5): Non-native academy exploration, 9b People and sequencing strategy, Track 1 - teacher clip review, 4.4 Precision over recall, Short-word false positives

### Community 9 - "Research Findings"
Cohesion: 0.50
Nodes (3): graphify wiring, Recorded corrections, Unknown - no public data exists

## Knowledge Gaps
- **30 isolated node(s):** `1 Agenda - suggested portion`, `2 Begin - unprompted, from memory`, `3 Track - silent, knows the text`, `7 Wisdom - mutashabihat if clean`, `Ladder is fixed, not learned` (+25 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 31 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `The seven-step loop` connect `The Session Loop` to `Cursors & Scheduling`, `The Two Voices`, `Community 7`?**
  _High betweenness centrality (0.371) - this node is a cross-community bridge._
- **What connects `1 Agenda - suggested portion`, `2 Begin - unprompted, from memory`, `3 Track - silent, knows the text` to the rest of the system?**
  _30 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Why does `4 Ladder - three rungs` connect `The Two Voices` to `Phase Roadmap`, `The Session Loop`?**
  _High betweenness centrality (0.285) - this node is a cross-community bridge._
- **Why does `Competence model` connect `Competence Model` to `Cursors & Scheduling`, `Community 7`?**
  _High betweenness centrality (0.246) - this node is a cross-community bridge._