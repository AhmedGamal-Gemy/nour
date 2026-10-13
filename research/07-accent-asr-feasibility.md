# Accent ASR Feasibility Assessment for Non-Native Quranic Recitation

**Date**: 2026-10-13  
**Author**: accent-asr (teammate, nour-pivot)  
**Task**: Assess technical feasibility of ASR on L1-accented Quranic recitation

## Executive Summary

**Decisive Verdict: Feasible with significant caveats - but NOT trivially feasible.**

The key finding is that **the approach matters more than the accent**. If the system performs forced alignment against known expected phonemes/text (which is the case here - the user recites a specific ayah from memory), the accent problem is substantially mitigated compared to open-ended ASR transcription. However, several critical blockers remain:

- **Data scarcity**: Large, commercially-usable datasets of non-native (non-Arabic L1) speakers reciting Quran with annotated pronunciation errors are not readily available. Existing Quranic ASR datasets are overwhelmingly native Arabic reciters.
- **Hardware constraints**: The target hardware (Quadro P2000 4GB VRAM, Pascal, no tensor cores; i7-8850H AVX2-only) is marginal for running modern phoneme-level models like wav2vec2-BERT based systems (e.g., quran-muaalem at ~0.6B params) in near-real-time without aggressive optimization/quantization.
- **Precision requirement**: The religious context demands high precision (avoiding false positives that incorrectly mark correct recitation as wrong). Current phoneme-level mispronunciation detection systems still struggle with precision/recall tradeoffs (e.g., IqraEval systems showing high recall but low precision in earlier editions).
- **Learner vs non-native distinction**: Most "learner" Quranic datasets/corpora refer to learners in general (often Arabic-speaking learners of tajweed), not specifically non-Arabic L1 speakers with strong L1 interference (English/French/Dutch/Spanish speakers lacking Arabic phonemes like ع/ح/ق/ط/ص).

**Recommended path forward**: A forced-alignment + phoneme-level goodness-of-pronunciation approach (not open transcription) is the right technical direction. The quran-muaalem/QPS approach is promising. However, before committing to full implementation, the team must validate on actual non-native accented samples and benchmark on the target hardware.

## 1. The Forced-Alignment vs Transcription Question (Critical)

This is the most important distinction and should drive the entire design.

### Why forced alignment changes everything

- **Open ASR transcription**: Model must decode the most probable word sequence from acoustics alone. Heavy accents can push acoustics toward L1 phonetic categories, causing substitution errors and high WER. This is why "models trained on native Arabic reciters fail on accented speech".
- **Forced alignment against known reference**: The expected text/ayah is known in advance. We align the observed audio frames to the expected phoneme sequence (using CTC-based forced alignment, or WFST-based alignment with an acoustic model). The system detects deviations: substitutions, insertions, deletions of phonemes relative to the canonical pronunciation. This is the standard approach for CAPT (Computer-Assisted Pronunciation Training) and mispronunciation detection (e.g., GOP scoring, ASR-based MDD).
- **Constrained search space**: Rather than searching over all possible Arabic words/sequences, the hypothesis space is fixed to the known utterance. This is far more robust to accent-induced acoustic variation.

### Evidence supporting this approach

- **quran-muaalem** ([arXiv 2509.00094](https://arxiv.org/abs/2509.00094), [project page](https://obadx.github.io/quran-muaalem/en/)) explicitly uses "reference-aware analysis" - compares predicted phonemes with a reference phonetic script from their `quran-transcript` toolkit. They report Tajweed F1 of 75.8% on "learner errors". Multi-level CTC decodes phonemes/attributes; alignment to reference enables error detection.
- **IqraEval shared tasks** ([ArabicNLP 2025](https://aclanthology.org/2025.arabicnlp-sharedtasks.61/), [Interspeech 2026](https://arxiv.org/html/2603.29087)) frame the task as "mispronunciation detection and diagnosis" given speech segment and corresponding reference transcript - i.e. reference-aware. This is forced-alignment style assessment, not open transcription.
- **GOP/phoneme-based CAPT literature**: Goodness of Pronunciation scores compute posterior probabilities of expected phonemes vs alternatives; these are reference-driven and less sensitive to open-vocabulary decoding failures.

**Verdict on this question**: Yes, forced alignment against known expected phonemes sidesteps the core "open ASR fails on accent" problem. However, it does *not* eliminate it entirely - the acoustic model still needs to produce reasonable posteriors for non-canonical L1-influenced pronunciations. If the acoustic model has never seen certain L1 phonetic realizations of Arabic phonemes, alignment quality degrades.

## 2. Existing Work on Accented/Non-Native Quranic ASR and Phoneme Assessment

### Quran Muaalem (most directly relevant)

- **What**: End-to-end pronunciation error detection/correction for Quran learners using multi-level CTC + custom Quran Phonetic Script (QPS) encoding tajweed rules (11-level: phoneme + sifat/articulation). Reference-aware analysis against canonical phonetic script.
- **Data**: 848 hours audio, 286K annotated utterances; qdat_bench benchmark with 159 samples of real recitation errors ([dataset](https://huggingface.co/datasets/obadx/qdat_bench)).
- **Results**: 0.21% PER on test set, 1.94% PER on qdat_bench; 75.8% Tajweed F1 on learner errors ([paper](https://arxiv.org/abs/2509.00094), v2 2026).
- **Models**: `obadx/muaalem-model-v3_2` (0.6B params, based on facebook/w2v-bert-2.0), MIT license ([HF model](https://huggingface.co/obadx/muaalem-model-v3_2)). Also mini variants available.
- **Limitations stated/observed**: Targets "learners" broadly. No explicit breakdown of L1 backgrounds (Arabic vs non-Arabic). qdat_bench is small (159 samples). The paper focuses on tajweed error detection - coverage of specific L1-driven substitutions is not detailed.

### IqraEval Shared Tasks (ArabicNLP 2025, Interspeech 2026)

- **Focus**: Phoneme-level mispronunciation detection for Quranic recitation (reference-aware). 
- **ArabicNLP 2025 results**: Top systems showed high recall but low precision. For example, Whisper-large-v3 adapted to speech-to-phoneme achieved F1=0.3224, recall=0.7624, precision=0.2045 ([paper](https://aclanthology.org/2025.arabicnlp-sharedtasks.64.pdf)) - many false positives.
- **Interspeech 2026**: Substantial improvement - best F1~0.72 ([arXiv summary](https://arxiv.org/html/2603.29087v2)), 13/19 teams beat baseline. Still precision-recall tradeoff persists for some systems.
- **Relevance**: Demonstrates the task is solvable with improving SOTA; precision remains challenging - critical given the "falsely telling someone wrong is worse than missing error" constraint from PLAN.md.

### QuranMB Benchmarks

- **QuranMB.v1/v2** appear in IqraEval literature as benchmarks for Arabic pronunciation assessment ([related work](https://arxiv.org/html/2506.07722v2)). These provide standardized evaluation frameworks for mispronunciation detection in Quranic recitation.

### Other Quranic ASR models

- **Whisper fine-tuned on Quran**: e.g. `MaddoggProduction/whisper-large-v3-turbo-quran-lora-dataset-mix` ([HF](https://huggingface.co/MaddoggProduction/whisper-l-v3-turbo-quran-lora-dataset-mix)), `yousifgamalo/quran-s-finetuned` ([HF](https://huggingface.co/yousifgamalo/quran-s-finetuned)). These are mostly for open transcription/diacritized transcription of Quranic recitation. Trained predominantly on professional/native reciters (MP3Quran, tarteel-ai datasets). WER numbers reported on test sets of similar reciters (e.g. ~0.116 WER on their test sets) - but performance on L1-accented non-native speech is not documented.

## 3. Data Availability for Non-Native Quranic Recitation

This is the crux of the problem.

| Source | Type | Non-native? | Quranic? | Size | License/Access | Notes |
|---|---|---|---|---|---|---|
| [Arabic Learner Corpus (LDC2015S10)](https://catalog.ldc.upenn.edu/LDC2015S10) | Written+spoken MSA from Arabic learners | Yes (learners from 67 nationalities, 66 L1s) | No - general MSA, not Quranic recitation | 282k words, ~3h22m audio | LDC license - typically requires membership/subscription; commercial use may be restricted/not free | Good for general Arabic learner pronunciation, but not Quran-specific. Tajweed rules not annotated. |
| [IqraEval/Iqra_train datasets](https://huggingface.co/IqraEval) | Quranic recitation with phoneme annotations for mispronunciation detection | Unclear from public descriptions | Yes (Quranic) | ~79h+ (training) | Shared task datasets - check specific license on HF; often research use. Commercial license not explicitly stated in visible text. | Collected for mispronunciation detection; demographic breakdown (L1/native status) not prominent in public descriptions. |
| [quran-muaalem training data (obadx/muaalem-annotated-v3)](https://huggingface.co/datasets/obadx/muaalem-annotated-v3) | Quranic recitations with phonetic/sifat annotations | Unclear | Yes | 287k utterances (~848h total as per paper) | HF dataset by obadx - license not explicitly visible in the preview; paper states "open-source release" of work. Need to verify dataset license terms. | "Learner" focus per paper, but L1 composition unknown. |
| [qdat_bench](https://huggingface.co/datasets/obadx/qdat_bench) | Quranic recitation errors (benchmark) | Small (159 samples). Demographics include age/gender; L1 not shown. | Yes | 159 samples | HF dataset - license not specified in preview text shown. | Real recitation errors; useful for evaluation but insufficient for training. |
| [MP3Quran, tarteel-ai/everyayah, Quran-Recitations](https://huggingface.co/datasets) | Professional Quranic recitations | Predominantly native Arabic reciters | Yes | Large (thousands of hours across reciters) | Varies - some public domain/various licenses; need careful verification for commercial use | Great for ASR pretraining on canonical recitation, but not representative of non-native accented speech. |
| [CMU SLAM/GlobalPhone Arabic](https://catalog.ldc.upenn.edu/) | General MSA corpora | Native/L1 Arabic speakers typically | No | Varies | LDC - licensed, often not free for commercial | Not Quranic; not learner-focused. |

### Key observations on data

1. **No obvious large-scale public dataset of non-Arabic L1 Quranic reciters.** The search did not surface a dataset like "non-native Quran recitation" with clear licensing on HF/Kaggle. This is a significant gap.
2. **"Learner" ≠ "non-Arabic L1 accented"**. Many Quranic learning contexts involve Arabic speakers learning tajweed. L1 interference is different (e.g. Egyptian Arabic dialect influence vs English speaker struggling with ع/ح/ق). The risk specified is specifically L1 interference from non-Arabic languages.
3. **Licensing uncertainty**: Many relevant datasets (IqraEval, quran-muaalem datasets) lack explicit commercial license statements in the public previews. LDC corpora require paid licenses. For "budget is zero - local inference only" and potential commercial product, license clarity is essential.
4. **Small evaluation sets only**: qdat_bench (159) is tiny. IqraEval has test sets, but training data composition is unclear.

**Conclusion on data**: There is insufficient publicly accessible, commercially-usable data of non-Arabic L1 accented Quranic recitation to train an open transcription model from scratch. However, for a forced-alignment/phoneme-assessment approach, three mitigations are plausible (see section 6).

## 4. Commercial/Academic Systems for Non-Native Arabic Pronunciation Assessment

- **General Arabic CAPT**: Systems like [CMU's Arabic language learning tools](https://www.cmu.edu/dietrich/lcal/academics/courses/arabic-studies/index.html) and various academic systems exist. The Arabic Learner Corpus (LDC2015S10) was created to support such work.
- **Quran-specific**: Tarteel.ai offers real-time feedback and is used at scale (15M+ users per task description), but their approach/model details are not fully public. Other apps (e.g. Quranic learning apps) exist - many use word-level matching rather than phoneme-level accent-sensitive assessment.
- **IqraEval systems**: Academic systems from the shared tasks (Whisper/Wav2Vec2-based phoneme MDD). These are research prototypes; not obvious commercial products targeting non-native accented Quran recitation specifically.
- **quran-muaalem**: Open-source research system targeting learners. Not a commercial product as described, but the approach is public.

**How they work**: Common patterns are (1) forced alignment of audio to expected phoneme sequence, (2) GOP scoring or CTC-based confidence, (3) ASR-based MDD comparing canonical vs predicted phonemes, (4) sometimes using extended phoneme sets to capture common errors. The quran-muaalem approach uses QPS (custom phonetic script encoding tajweed rules) and multi-level CTC with reference-aware analysis - this is a sophisticated form of forced alignment+assessment.

## 5. Hardware Feasibility Assessment

**Target hardware**: Quadro P2000 4GB VRAM, compute capability 6.1 Pascal, no tensor cores. Intel i7-8850H (6 cores, AVX2 only, no AVX-512/VNNI). ~1.5GB free RAM. Budget zero, local inference only.

### Model requirements (quran-muaalem v3_2)

- **Model**: `obadx/muaalem-model-v3_2` based on `facebook/w2v-bert-2.0` ([HF card](https://huggingface.co/obadx/muaalem-model-v3_2)).
- **Size**: 0.6B parameters, stored as F32 safetensors (model size ~2.4GB). There is also `muaalem-model-v3-mini` variant which is smaller.
- **Architecture**: Wav2Vec2-BERT style encoder + multi-level CTC heads. Requires 16kHz audio input.
- **Dependencies**: PyTorch/Transformers - can run on CPU or CUDA.

### VRAM analysis

- **Weights (F32)**: ~2.4GB for v3_2 (0.6B * 4 bytes). v3_mini will be smaller, but exact size not shown in previews.
- **Activations**: For Wav2Vec2-style models processing ~10-30s segments, activation memory can be hundreds of MB to ~1GB depending on batch size and sequence length. With batch size 1 (streaming/online), activations are more manageable (~200-800MB).
- **Total estimate**: F32 inference with batch size 1 likely needs 2.8-3.2GB VRAM minimum for v3_2. This **exceeds** 4GB? 2.4+0.8=3.2GB fits in 4GB with headroom, but is tight. Also other overhead (CUDA context, PyTorch). On Pascal cards with 4GB, running F32 can work but leaves little room. Aggressive memory pressure can cause slowdowns.
- **Quantization is essential**: GGUF (GGML) with INT8 or INT4 would reduce weights to ~0.6-1.2GB. The quran-muaalem repo has TorchScript exports (`muaalem-v3_2-torchscript*` on HF) and also mentions deployment options. If converted to GGUF via llama.cpp/whisper.cpp style tooling adapted for wav2vec2, VRAM drops significantly. But this requires conversion work - not "off the shelf" without effort.

### CPU/latency analysis (AVX2 only, no AVX-512/VNNI)

- **Wav2Vec2-BERT is compute-heavy**: Self-attention over long sequences + convolutional feature encoder. On older 6-core i7-8850H (AVX2, ~3.6GHz boost), CPU inference of 0.6B F32 model is likely slow for real-time. Real-time factor (RTF) of >1 means slower than audio duration.
- **Near-real-time requirement**: For live feedback during recitation, you need low latency (ideally <300-500ms end-to-end for word/phoneme-level feedback). Achieving this on AVX2-only CPU with this model size is challenging without optimizations (int8 CPU inference, model distillation to smaller size like mini variant).
- **Pascal GPU**: Pascal (6.1) has no tensor cores; FP32 performance is decent but not modern. Still likely faster than CPU. With 4GB limit, need quantized weights.

### Practical feasibility

| Scenario | VRAM | Latency (speculation) | Feasible? |
|---|---|---|---|
| v3_2 F32 on GPU | ~3.2GB total (tight) | Maybe 2-5x RTF (too slow for fluid real-time) or borderline | Marginal - probably not smooth for continuous feedback |
| v3_2 INT8 GGUF on GPU | ~1.5-2GB | Better, maybe 1-2x RTF | Possibly feasible with optimization |
| v3_mini (smaller) on GPU (quantized) | <2GB | Closer to real-time | More realistic |
| CPU-only AVX2 (any quantization) | RAM ok (~1.5GB free but model+buffers need more; system RAM likely sufficient if <2GB model) | Likely >2-5x RTF | Probably too slow for interactive use |
| CTranslate2/ONNX Runtime with CPU int8 + optimizations | RAM ok | Varies; better with VNNI/AVX512 - but no AVX512 here | Unclear; needs benchmarking |

**Speculation labeled**: These are estimates based on typical wav2vec2 performance characteristics. The quran-muaalem repo shows Gradio demo ([spaces](https://huggingface.co/spaces) using the model exist), but hardware specs of those demos not public. No published RTF numbers for this exact model on Pascal hardware found in the reviewed sources.

**Bottom line on hardware**: Not infeasible in principle, but **very tight for the stated hardware**. To run locally with acceptable latency, you would almost certainly need model quantization (INT8/INT4) and likely use the mini variant. CPU-only is unlikely to meet near-real-time requirements. This is a genuine engineering constraint, not a hard blocker if optimized, but not "just run the model" either.

## 6. Is This a Moat or a Blocker?

**Verdict: It's a moat in principle, but the data aspect is a *pragmatic* blocker for the specific non-Arabic L1 pivot with zero budget.**

### Why it could be a moat

- **Few solutions target non-native accented Quranic recitation specifically**: Most Quranic ASR focuses on transcription of canonical/native recitation. Phoneme-level accent-sensitive assessment for non-Arabic learners is underexplored compared to general ASR.
- **Tajweed + L1 interference is a niche intersection**: Combining religious phonetic rules (tajweed) with L1-specific pronunciation errors requires domain knowledge + data. This is defensible if executed well.
- **Reference-aware forced alignment approach is the right direction**: As reasoned in section 1, this sidesteps the open-transcription accent problem. The quran-muaalem work shows this is viable for "learners" in general.
- **Precision requirement creates defensibility**: Getting both high precision (avoid false wrong-calls) and good recall on accented speech is hard. If solved well for the target languages (English/French/Dutch/Spanish L1 speakers), that's differentiating.

### Why it could be a blocker

- **Data is the fundamental constraint**: To robustly handle specific L1 interference patterns (e.g. English speakers substituting/simplifying ع/ح/ق/ط/ص, vowel epenthesis), you need training/evaluation data from those speakers. Without such data, you cannot validate that forced alignment generalizes across accents, nor can you fine-tune to improve robustness.
- **Commercial licensing uncertainty**: Even if data exists academically (LDC), commercial terms may be prohibitive. Public HF datasets lack clear commercial licenses in many cases.
- **Validation risk**: Building on "learner" data that is predominantly Arabic-L1 learners means you may be overfitting to those error patterns and underperforming on non-Arabic L1 accents. This is the exact risk stated.
- **Hardware is marginal**: On the specified hardware, achieving acceptable real-time latency requires quantization and optimization work. Not impossible, but adds friction.

**Conclusion**: More of a **data-driven feasibility risk** than a fundamental theoretical blocker. If you can collect/curate even a small validation set of non-Arabic L1 reciters (e.g. 10-50 speakers across target languages), you can test the forced-alignment approach with existing models (quran-muaalem) and get empirical evidence. Without that validation data, it's a high-risk pivot.

## 7. Mitigation Options (Ranked)

Given the data/hardware constraints, consider these approaches in order of feasibility:

| Rank | Option | Effort | Impact | Notes |
|---|---|---|---|---|
| 1 | **Use forced alignment + existing phoneme model (quran-muaalem)** | Low | High | This directly addresses the core distinction. Start by evaluating `obadx/muaalem-model-v3_2` (or mini) with forced alignment to canonical phonemes. Test on non-native samples as soon as possible. This doesn't require new training data if the existing model generalizes. |
| 2 | **Quantize and optimize for target hardware** | Medium | High | Convert to GGUF/INT8 via CTranslate2 or similar. Try `muaalem-model-v3-mini` first. Profile latency/VRAM on similar hardware or estimate. This addresses the hardware constraint without collecting large datasets. |
| 3 | **Collect small validation set first (self-recording from target community)** | Medium | High (de-risks) | Before scaling, record 5-20 minutes of recitations from non-Arabic L1 speakers (English/French/Dutch/Spanish) across common ayat. This is the only way to empirically test the accent hypothesis. Can be done with minimal cost/community outreach. |
| 4 | **Fine-tune on general learner-Arabic data (if license permits)** | High | Medium-High | If quran-muaalem generalizes poorly to non-Arabic accents, fine-tune on Arabic Learner Corpus (if commercially licensable) or other learner data adapted to Quranic phonetics. But mapping MSA learner errors to tajweed-specific phoneme space is non-trivial. Licensing may be expensive/time-consuming. |
| 5 | **Crowdsourcing** | High | High | Scale data collection via community (mosques, Islamic schools teaching non-Arabic speakers). Good long-term, but slow, needs consent/IRB considerations, and licensing/terms. Not viable for immediate feasibility test. |
| 6 | **Pure G2P-based expected-phoneme pipeline (no accented training data)** | Medium | Medium | Build canonical phoneme sequence from ayah text (with tajweed rules) using G2P + tajweed phonetic rules (like quran-transcript). Then do forced alignment with a general acoustic model and score deviations via GOP. This avoids training on accented data entirely - the "expected" is canonical. The weakness is if the acoustic model can't align well to accented realizations, GOP scores become unreliable. Still worth exploring as a comparison baseline. |

### On G2P-based forced alignment (key point)

The developer's intuition is correct: **forced alignment against known expected phonemes is very different from open transcription**. You don't need transcribed accented data to build the alignment system; you need:
1. Canonical phoneme sequence for each target ayah (can be generated via G2P + tajweed rules - quran-transcript from quran-muaalem does this)
2. An acoustic model that can produce frame-level posteriors for phonemes (even if trained on native speech, constrained alignment can still work if accents don't completely break the acoustic match)
3. An alignment algorithm (CTC forced alignment, or HMM-GMM/DNN-HMM forced aligner)

This is why this approach sidesteps much of the accent-data problem. The acoustic model trained on native reciters may still align reasonably well for many accented pronunciations; errors will show up as higher alignment costs or lower posterior probabilities for expected phonemes. The question is whether the sensitivity is sufficient to detect real mistakes vs accent variation.

**This is the most promising direction and justifies the pivot's technical hypothesis *if* validated empirically.**

## 8. What Would Kill This Hypothesis

Watch for these red lines:

1. **Empirical failure on non-Arabic accented data**: Test quran-muaalem's forced alignment/reference-aware analysis on even 5-10 non-native speakers across target L1s. If it consistently fails to distinguish accent from actual tajweed errors (low precision), or misses real errors (low recall) beyond acceptable thresholds, the hypothesis is dead.
2. **Inability to achieve required precision**: Given religious sensitivity, false positive rate must be very low. If phoneme-level models can't achieve precision > ~0.8-0.9 while maintaining useful recall on accented speech, the product is not viable as specified.
3. **Hardware performance below usable threshold**: If after quantization (INT8/INT4) and using mini variant, end-to-end latency exceeds ~500-800ms on the target hardware, the real-time feedback experience degrades too much. This is more of a product constraint than theoretical.
4. **Licensing blocks commercialization**: If the only viable models/datasets require restrictive licenses preventing commercial use, the zero-budget local-only constraint might still be ok, but long-term viability is killed. Need to verify MIT license on quran-muaalem models holds and dataset licenses are permissive.
5. **L1 coverage is too broad**: Handling English/French/Dutch/Spanish L1s simultaneously might require per-L1 adaptation. If each needs substantial data, scope becomes unmanageable.

## 9. Final Recommendation

**Proceed, but de-risk with empirical validation first.**

1. **Adopt forced-alignment approach** (not open transcription). The quran-muaalem architecture is well-aligned with this need.
2. **Immediately test on non-native samples**: Record/acquire a small test set (even 3-5 speakers per target L1) reciting known ayat. Run quran-muaalem's reference-aware analysis and manually review precision/recall on accent-induced vs error-induced deviations.
3. **Optimize for hardware now**: Quantize to INT8/INT4 and benchmark RTF/VRAM on hardware matching the spec (or closest available). Try `muaalem-model-v3-mini` as first candidate.
4. **Verify licenses**: Confirm commercial usability of quran-muaalem models (MIT) and any datasets you might need for fine-tuning.
5. **Set go/no-go criteria**: e.g. precision >= 0.85, recall >= 0.7 on non-native test set; end-to-end latency < 400ms on GPU-accelerated path.

**The accent problem is tractable via forced alignment, but not validated. The data scarcity is real for *training* on non-Arabic accents, but may be avoidable if existing learner-trained models generalize sufficiently. The hardware is marginal but solvable with quantization.**

## References (URLs)

- Quran Muaalem paper (arXiv): https://arxiv.org/abs/2509.00094
- Quran Muaalem project page: https://obadx.github.io/quran-muaalem/en/
- Quran Muaalem model (HF): https://huggingface.co/obadx/muaalem-model-v3_2
- qdat_bench dataset (HF): https://huggingface.co/datasets/obadx/qdat_bench
- IqraEval ArabicNLP 2025 paper: https://aclanthology.org/2025.arabicnlp-sharedtasks.61/
- IqraEval ANPLers system (2025): https://aclanthology.org/2025.arabicnlp-sharedtasks.64.pdf
- IqraEval Interspeech 2026 summary: https://arxiv.org/html/2603.29087v2
- Arabic Learner Corpus (LDC2015S10): https://catalog.ldc.upenn.edu/LDC2015S10
- QuranMB related work: https://arxiv.org/html/2506.07722v2
- Quranic ASR models (examples): https://huggingface.co/MaddoggProduction/whisper-l-v3-turbo-quran-lora-dataset-mix
