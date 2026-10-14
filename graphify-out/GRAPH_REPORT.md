# Graph Report - nour  (2026-10-14)

## Corpus Check
- 5 files · ~10,119 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 3, .jsonc 1)

## Summary
- 108 nodes · 131 edges · 11 communities
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 3 edges (avg confidence: 0.78)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `10a979af`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Competence model
- 2b The session
- Architecture: Pipecat + local Whisper
- 4 Ladder - three rungs
- Phase 1 - Data foundation
- Phase 8 - Tajweed
- graph-first.js
- The seven-step loop
- 9b People and sequencing strategy
- research/00-FINDINGS.md
- nour — product map (visual)

## God Nodes (most connected - your core abstractions)
1. `Competence model` - 12 edges
2. `The seven-step loop` - 8 edges
3. `2b The session` - 6 edges
4. `4 Ladder - three rungs` - 6 edges
5. `6 Score - one run, one segment score` - 6 edges
6. `nour — product map (visual)` - 5 edges
7. `Phase 1 - Data foundation` - 5 edges
8. `Phase 5 - The prompt ladder` - 5 edges
9. `Architecture: Pipecat + local Whisper` - 5 edges
10. `WhisperSTTService` - 5 edges

## Surprising Connections (you probably didn't know these)
- `What survives as defensible` --conceptually_related_to--> `Competence model`  [EXTRACTED]
  research/00-FINDINGS.md → PLAN.md
- `What survives as defensible` --conceptually_related_to--> `QurSim mutashabihat (7,649 pairs)`  [EXTRACTED]
  research/00-FINDINGS.md → PLAN.md
- `5 Continue - never restart` --conceptually_related_to--> `AGENTS: do not reinvent the wheel`  [INFERRED]
  PLAN.md → AGENTS.md
- `foyzulkarim/hifz-tester (MIT)` --references--> `AGENTS: do not reinvent the wheel`  [EXTRACTED]
  PLAN.md → AGENTS.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Two voices: agent and qari** — aud_agent_voice, aud_qari_voice, aud_husary_muallim, aud_word_dataset [EXTRACTED 1.00]
- **Five non-negotiable design rules** — rule_decoder_bias, rule_waqf, rule_recited_tested, rule_precision, rule_tashkeel [EXTRACTED 1.00]
- **The three-rung prompt ladder** — lad_wait, lad_hint, lad_word [EXTRACTED 1.00]
- **The seven-step session loop** — sess_agenda, sess_begin, sess_track, sess_ladder, sess_continue, sess_score, sess_wisdom [EXTRACTED 1.00]
- **The three session segments** — seg_near_old, seg_long_term, seg_new [EXTRACTED 1.00]
- **Two cursors and the gap** — cur_memorize, cur_revision, cur_gap, cur_override, cur_fail_gate [EXTRACTED 1.00]

## Communities (11 total, 0 thin omitted)

### Community 0 - "Competence model"
Cohesion: 0.24
Nodes (12): What survives as defensible, Ladder is fixed, not learned, Competence model, Neighbour anchoring (+/-2), Phase 5.5 - Scoring, Phase 4 - Competence model, Phase 5 - The prompt ladder, Phase 6 - Feedback delivery (+4 more)

### Community 1 - "2b The session"
Cohesion: 0.18
Nodes (13): Fail gate - no new material, The gap (measure, do not choose), Selection is mechanical, Memorize cursor, Decay-overrun override, Revision cursor, Nour, 2b The session (+5 more)

### Community 2 - "Architecture: Pipecat + local Whisper"
Cohesion: 0.14
Nodes (15): foyzulkarim/hifz-tester (MIT), Architecture: Pipecat + local Whisper, Desktop-first, VPS later, Faster Whisper / CTranslate2, Hardware: Pascal CC6.1, no tensor cores, int8 compute type, No interim transcription, LiveKit (rejected) (+7 more)

### Community 3 - "4 Ladder - three rungs"
Cohesion: 0.23
Nodes (12): The agent's own voice, Browser Arabic voice - unverified, Husary Muallim (corrections), Husary Murattal (revision), Never TTS a Quranic word, The qari's voice, quran-timing-helper (fallback), quranhive per-word audio (+4 more)

### Community 4 - "Phase 1 - Data foundation"
Cohesion: 0.17
Nodes (13): Model licensing (CC-BY-NC), Phase 0 - Evaluation harness, Phase 1 - Data foundation, Phase 2 - Audio pipeline, Phase 3 - Alignment and scoring, quranlab/quran, Quran-Lab/quranic-asr-benchmark, Tajweed annotations (+5 more)

### Community 5 - "Phase 8 - Tajweed"
Cohesion: 0.29
Nodes (7): Tilawa/QariAI/TajweedMate et al, Tarteel (15M users), Tarteel mutashabihat - lookup only, obadx/muaalem-model-v3_2, Phase 8 - Tajweed, 4.5 Word-clean is not tashkeel-correct, Why new material is sighted

### Community 6 - "graph-first.js"
Cohesion: 0.27
Nodes (7): EXEMPT_READ, hasGraph(), INDEXED_READ, inputText(), location, setup(), shouldDeny()

### Community 7 - "The seven-step loop"
Cohesion: 0.20
Nodes (10): The seven-step loop, Clean run = 10, Repeat failure halves the ayah, Score attaches to the segment, Recovered stumble = 9.5, 1 Agenda - suggested portion, 2 Begin - unprompted, from memory, 6 Score - one run, one segment score (+2 more)

### Community 8 - "9b People and sequencing strategy"
Cohesion: 0.40
Nodes (5): Non-native academy exploration, 9b People and sequencing strategy, Track 1 - teacher clip review, 4.4 Precision over recall, Short-word false positives

### Community 9 - "research/00-FINDINGS.md"
Cohesion: 0.50
Nodes (3): graphify wiring, Recorded corrections, Unknown - no public data exists

### Community 10 - "nour — product map (visual)"
Cohesion: 0.33
Nodes (5): 1. The session loop, 2. The prompt ladder, 3. The three segments and the two cursors, nour — product map (visual), Reading guide

## Knowledge Gaps
- **30 isolated node(s):** `Ladder is fixed, not learned`, `Neighbour anchoring (+/-2)`, `Retention decay`, `rung_reached field`, `Tajweed annotations` (+25 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 41 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `The seven-step loop` connect `The seven-step loop` to `2b The session`, `Architecture: Pipecat + local Whisper`, `4 Ladder - three rungs`?**
  _High betweenness centrality (0.268) - this node is a cross-community bridge._
- **What connects `Ladder is fixed, not learned`, `Neighbour anchoring (+/-2)`, `Retention decay` to the rest of the system?**
  _30 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Architecture: Pipecat + local Whisper` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._
- **Why does `4 Ladder - three rungs` connect `4 Ladder - three rungs` to `Phase 1 - Data foundation`, `The seven-step loop`?**
  _High betweenness centrality (0.206) - this node is a cross-community bridge._
- **Why does `Competence model` connect `Competence model` to `2b The session`?**
  _High betweenness centrality (0.178) - this node is a cross-community bridge._