# Technical Benchmarking Plan for nour ASR (Hesitant Quranic Recitation)

> **RECOMMENDATION #1 (TOP PRIORITY): Benchmark tarteel-ai/whisper-base-ar-quran FIRST**

**Why:** On the target hardware (Quadro P2000 4GB VRAM, Pascal, CUDA 6.1; Intel i7-8850H AVX2-only; ~1.5GB free RAM; $0 budget, fully local), `tarteel-ai/whisper-base-ar-quran` is the most defensible starting point. It is a fine-tuned Whisper-base (74M params) with Apache-2.0 license, smallest memory footprint among usable Quranic models (fits comfortably in 4GB VRAM even with overhead), was trained for Quranic Arabic (WER 5.75% self-reported on its eval set), is widely used/ported (Pipecat WhisperSTTService/faster-whisper/Transformers compatible), and is most likely to run acceptably on Pascal (int8) for CPU+GPU hybrid or CPU fallback. Critically, it’s small enough that latency is tractable on AVX2-only CPU; larger models (large-v3 variants) risk being too slow for near-real-time on Pascal with modest VRAM.

This recommendation is provisional pending evaluation on **hesitant, amateur (memory-recall)** recitations (see methodology below), as nearly all published WERs are on fluent/professional recitations.

---

## 1) Candidate Models (Full List)

Compare all Quranic/Arabic ASR models worth testing, plus plain Whisper baselines. Sources: HuggingFace model cards, arXiv, Quran Lab, community leaderboards.

| Model | HF Repo ID | Base | Params | Size (disk) | Reported WER | Training Data | License | Last Update | Downloads (mo) | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| Whisper base (plain baseline) | [openai/whisper-base](https://huggingface.co/openai/whisper-base) | Whisper base | ~74M | ~291MB | Varies by domain | General multilingual | [MIT](https://github.com/openai/whisper/blob/main/LICENSE) | Recent | High | Baseline; not Quran-finetuned |
| Whisper small (plain baseline) | [openai/whisper-small](https://huggingface.co/openai/whisper-small) | Whisper small | ~244M | ~967MB | Varies | General | [MIT](https://github.com/openai/whisper/blob/main/LICENSE) | Recent | High | Baseline; larger memory/latency |
| Quran-finetuned base (Tarteel) | [tarteel-ai/whisper-base-ar-quran](https://huggingface.co/tarteel-ai/whisper-base-ar-quran) | Whisper base | 74M | ~292MB | 5.75% (eval) ([card](https://huggingface.co/tarteel-ai/whisper-base-ar-quran)) | Quranic recitations (Tarteel) | [Apache-2.0](https://huggingface.co/tarteel-ai/whisper-base-ar-quran) | 2021-22 era (commits from ~3y ago) | High | **Top pick to start.** Fits 4GB easily; CPU+GPU feasible. |
| Quran-finetuned tiny (Tarteel) | [tarteel-ai/whisper-tiny-ar-quran](https://huggingface.co/tarteel-ai/whisper-tiny-ar-quran) | Whisper tiny | ~39M | ~151MB | 7.05% (eval) ([card](https://huggingface.co/tarteel-ai/whisper-tiny-ar-quran)) | Quranic (Tarteel) | [Apache-2.0](https://huggingface.co/tarteel-ai/whisper-tiny-ar-quran) | Old | Moderate | Fastest, lowest VRAM; may trade accuracy for speed on hesitant recitations. Test. |
| Quran-S finetuned (yousifgamalo) | [yousifgamalo/quran-s-finetuned](https://huggingface.co/yousifgamalo/quran-s-finetuned) | Whisper medium | ~769M | ~1.5GB+ | 0.1162 WER (test, professional) ([card](https://huggingface.co/yousifgamalo/quran-s-finetuned)) | MP3Quran + Tarteel (cleaned) | [Apache-2.0](https://huggingface.co/yousifgamalo/quran-s-finetuned) | 2024 | Low-Mod | Medium-sized; likely tight on 4GB VRAM in practice (overhead). CPU slower on AVX2. |
| Whisper-Quran v1 (wasimlhr) | [wasimlhr/whisper-quran-v1](https://huggingface.co/wasimlhr/whisper-quran-v1) | Whisper large-v3 | 1.55B | ~3GB+ (fp16 weights) | 5.35% best / 5.74% released ([card](https://huggingface.co/wasimlhr/whisper-quran-v1)) | Buraaq/quran-md-ayahs (5 reciters×6236 ayahs) | [CC-BY-NC-4.0](https://huggingface.co/wasimlhr/whisper-quran-v1) | 2026 | Growing | Strong WER on fluent; large memory (fp16 ~3GB, int8 helps but still ~1.6GB weights+overhead); likely slow on Pascal CPU+GPU. License NC may constrain some uses - verify fit. |
| Whisper-quran (raghadOmar) | [raghadOmar/whisper-quran](https://huggingface.co/raghadOmar/whisper-quran) | Whisper base (finetuned from tarteel base) | 74M | ~292MB | 10.34% (self-reported) ([card](https://huggingface.co/raghadOmar/whisper-quran)) | Zolfa dataset | [Apache-2.0](https://huggingface.co/raghadOmar/whisper-quran) | 2024 | Low | Base-sized; higher reported WER than tarteel base - worth testing as alternative. |
| Whisper-large-v3-turbo-ar-quran (naazimsnh02) | [naazimsnh02/whisper-large-v3-turbo-ar-quran](https://huggingface.co/naazimsnh02/whisper-large-v3-turbo-ar-quran) | Whisper large-v3-turbo | 809M | ~1.6GB (fp16) | 1.18% WER test, 0.86% val ([GH](https://github.com/Naazimsnh02/whisper-large-v3-turbo-ar-quran), [HF context](https://huggingface.co/openai/whisper-large-v3-turbo)) | tarteel-ai/everyayah (167k+ samples) | Apache-2.0 (model) | 2025 | Low | Very low reported WER on fluent; turbo has fewer decoder layers (faster than full large-v3) but still ~800M params - memory+latency on Pascal needs validation. |
| Arabic dialect FT (dev-ahmedhany, CT2 int8 artifact) | [dev-ahmedhany/whisper-large-v3-turbo-arabic-ft-ct2-int8](https://huggingface.co/dev-ahmedhany/whisper-large-v3-turbo-arabic-ft-ct2-int8) | Whisper large-v3-turbo | 809M | ~820MB (CT2 int8) | Mixed results by dialect (paper summary) | Dialect-balanced mix | [Apache-2.0](https://huggingface.co/dev-ahmedhany/whisper-large-v3-turbo-arabic-ft-ct2-int8) | 2026 | Low | CT2 int8 quantized artifact is compact; useful for CPU/CT2 testing. |

Notes on sizes/params: Whisper base 74M, small 244M, medium 769M, large-v3 1550M, large-v3-turbo 809M (reduced decoder). Disk sizes ~291MB, 967MB, 1.5GB, 3GB+, 1.6GB respectively (fp16). Int8 reduces weights ~4x.

---

## 2) Evaluation Methodology (Hesitant Recitation Focus)

Our real target is **hesitant amateur memory recitation** (pauses, restarts, self-corrections, slower pace) - not professional fluent studio recitation. Most published WERs are on fluent recitations; we must evaluate on learner-like hesitant clips.

### Test Set (~30 clips, priority)
- **Own hesitant recitations** (developer): ~30 clips of actual memory recitation with pauses, hesitations, false starts. Label ground truth verbatim (what was attempted/intended) to separate hesitation artifacts from true errors.
- Supplement with **real learner** samples where available (see datasets §3). Prioritize clips that include natural pauses, mid-word breaks, restarts.

### Metrics
| Metric | Purpose | Notes |
|---|---|---|
| WER (Word Error Rate) | Overall accuracy | Standard, but sensitive to hesitations. |
| CER (Character Error Rate) | Finer-grained | Better for Arabic diacritics/short words. |
| Per-ayah error attribution | Error localization | Track which ayah positions errors occur. |
| **Hesitation-artifact separation** | Critical | Classify model outputs as: true substitution/insertion/deletion vs. false positive due to mid-word pause, breath, restart, filler silence. We must not penalize the model for reasonable hesitation handling - but our product constraint says *never bias decoder when scoring errors* (biasing hides mistakes). So evaluation must measure raw decoder behavior on hesitant audio, not biased. |
| p50/p95 latency per chunk | Real-time feasibility | Chunk-based (see below). p95 is what matters for UX. |

### Test Matrix
Run all candidates that fit memory; at minimum:
- {whisper-base (plain), tarteel-ai/whisper-base-ar-quran, tarteel-ai/whisper-tiny-ar-quran, raghadOmar/whisper-quran} × {cpu int8, cuda int8}
- {yousifgamalo/quran-s-finetuned, large-v3-turbo variants} if VRAM allows (int8)
- Baselines: openai/whisper-small × cpu/cuda int8
- whisper.cpp equivalent builds for CPU-focused comparison

Runtimes: faster-whisper (CTranslate2) is primary for CPU+GPU; whisper.cpp as alternative CPU runtime (§5).

### Chunking Strategy (from whisper-quran-v1 learnings)
- **10-second chunks** (sweet spot reported: chunks of 5-15 words / ~10s eliminate long-ayah drift). Test 5s, 10s, 15s on hesitant audio.
- Overlap between chunks to avoid boundary effects.
- Avoid very long chunks (drift) and very short (context loss).

### Decision Rule (explicit)
Pick the model M* such that:
1. **Memory**: fits in 4GB VRAM with room for buffers (target ≤ 3.0–3.2GB GPU alloc in practice) AND leaves ~1.5GB RAM headroom acceptable. If M* cannot run with int8 on GPU without OOM, reject for GPU path.
2. **Latency (real-time feasibility)**: p50 per 10s chunk ≤ ~2–3s on target hardware (or better) for CPU path minimum; p95 ≤ 5s. On GPU, expect better but Pascal modest. If p95 > 8s on CPU int8, likely unacceptable for near-real-time UX.
3. **Accuracy on hesitant recitations**: WER on our ~30 hesitant clips is the primary accuracy metric, with hesitation-artifact separation applied. Prefer model with better precision on true errors (minimize false “corrections” hiding mistakes - aligns with “precision over recall” product constraint). Do **not** pick purely by fluent-WER.
4. **Robustness to hesitation**: fewer false positives from pauses/restarts (measured via hesitation-artifact rate). A model that fragments on pauses is worse for our use case even if fluent-WER is good.
5. **Pragmatics**: Apache-2.0 license compatibility (Tarteel base, raghadOmar, naazimsnh variants), active/usable with faster-whisper/Pipecat WhisperSTTService, reasonable download size.
6. **Tie-breaker**: smaller memory footprint and lower CPU latency wins if accuracy within ~1–2% WER on hesitant set.

**Minimum acceptance**: Must run on CPU int8 (AVX2) with p95 < 6s per 10s chunk; GPU int8 preferred if it helps latency without hurting precision on errors. Start with **tarteel-ai/whisper-base-ar-quran**; only switch if it fails on hesitant recitations or latency.

---

## 3) Datasets for Evaluation

Investigate public data for evaluation (especially learner/hesitant). Verify licenses and usability.

| Dataset | Contents | Size | License | Usability for our eval | Notes/Links |
|---|---|---|---|---|---|
| [tarteel-ai/everyayah](https://huggingface.co/datasets/tarteel-ai/everyayah) | Per-ayah recitations, many reciters | Large (114 reciters, 6236 ayahs each in parts) | Check card ([HF](https://huggingface.co/datasets/tarteel-ai/everyayah)) - verify terms; often used for training/eval. | Good for fluent baseline, but need to ensure held-out from training of candidate models. | Commonly used (e.g. naazimsnh02 trained on it). |
| [Buraaq/quran-md-ayahs](https://huggingface.co/datasets/Buraaq/quran-md-ayahs) | Multilingual/multimodal Quran data incl. audio alignment | Medium-large | Varies by subsets; check HF card | Useful for ayah-level alignment/eval. | Used by wasimlhr/whisper-quran-v1. |
| [QDAT](https://arxiv.org/abs/2107.05209) (Osman et al.) | 1505 recordings from 150 readers; 3 tajweed rules; recorded over WhatsApp at 11kHz; contains learner errors | 1505 utterances | Open-source as described in paper ([arXiv](https://arxiv.org/abs/2107.05209), [project refs](https://arxiv.org/html/2509.00094v2)) | **Highly relevant** - explicitly contains learner errors. Good for error detection eval. | Widely cited; check exact license distribution (HF mirrors may vary). |
| [qdat_bench](https://huggingface.co/datasets/obadx/qdat_bench) ([paper](https://arxiv.org/abs/2509.00094)) | 159 samples of real learner recitation errors (Surah Al-Ma’idah 5:109); phonemes/diacritization/tajweed rules (Ghunnah, Qalqalah, Madd) | 159 samples | CC BY 4.0 ([HF card states](https://huggingface.co/datasets/obadx/qdat_bench), arXiv CC BY 4.0) | **Very relevant** - real learner errors, small but focused. Good for precision/recall on true errors. | From Quran Muaalem work (obadx). |
| [QuranMB v1/v2](https://ieee-dataport.org/documents/comprehensive-quranic-dataset-version-1-cqdv1) (Alfadhli et al., IEEE DataPort) | 114 surahs × 35 reciters (~218k files), Hafs | Large | IEEE DataPort terms - access may require subscription; verify license. | Potential eval set (fluent+varied). Check accessibility/copyright. | Listed in reviews; access controlled. |
| [IqraEval shared task benchmarks](https://github.com/llm-lab-org/QuranicBenchmarking) | Quranic benchmarking resources (ASR/QA etc.) | Varies | Repo states licensing largely undocumented across reviewed datasets ([README](https://github.com/llm-lab-org/QuranicBenchmarking/blob/main/datasets.md)). | Investigate carefully; licensing unclear. Treat as reference only unless license confirmed. | Good survey of gaps. |
| [CMV-Ar (Common Voice Arabic subsets)](https://huggingface.co/datasets/mozilla-foundation/common_voice_11_0) | General Arabic speech (not Quran-specific) | Large | CC0/CC BY ([Common Voice terms](https://commonvoice.mozilla.org/en/terms)) | Not directly Quranic, but useful sanity check on general Arabic ASR if needed. Low priority. | Avoid using as primary Quran eval. |
| [FaisaI/tadabur](https://huggingface.co/datasets/FaisaI/tadabur) | 1400+ hours, 600+ reciters, verse+word timing | Very large | [CC BY-NC 4.0](https://huggingface.co/datasets/FaisaI/tadabur) | Large, diverse. Non-commercial license - acceptable for internal research/eval; verify usage aligns with NC if sharing results. | Rich metadata; good for held-out evaluation if we respect NC. |
| [Quran-Lab/quran-audio](https://huggingface.co/datasets/quranlab/quran-audio) | Per-ayah references + word timing (CC-BY) for subsets | Medium | Mixed per subsets ([card](https://huggingface.co/datasets/quranlab/quran-audio)) | Useful alignment; check subset licenses. | Complementary to text corpus. |

**Recommendation for eval set construction:** Build primary set from our own ~30 hesitant clips (ground-truthed). Augment with qdat_bench (159 learner-error samples, CC BY 4.0) and QDAT (learner errors) where license permits. Avoid using training data of candidate models as test (e.g. if model trained on everyayah, don’t test on everyayah held-out that overlaps).

---

## 4) Hardware Constraints & CTranslate2

Target hardware: **Quadro P2000 4GB VRAM, compute capability 6.1 (Pascal), no tensor cores**. CPU **i7-8850H, 6 cores, AVX2 only, no AVX-512, no VNNI**. RAM 15.8GB, only ~1.5GB free.

### CTranslate2 compute types (Pascal CC 6.1)
From CTranslate2 docs ([quantization](https://opennmt.net/CTranslate2/quantization.html), [runtime compute types](https://opennmt.net/CTranslate2/python/ctranslate2.get_supported_compute_types.html)):

**On GPU (Pascal CC 6.1):**
- Supported: `int8`, `int8_float32`, `int16`, `float16` (float16 supported on CC 7.0+ generally; CC 6.1: float16 may be converted/fallback in practice - check docs table). Specifically: table shows CC 6.1 supports `int8_float32`, `int8_float16`? Wait - CTranslate2 table states:
> - 6.1 | int8_float32 | int8_float32 | int8_float32 | float32 | float32 | float32

So for CC 6.1: `int8` is supported (int8_float32 path), but `float16` and `int8_float16` map to float32/fallback (not true float16 compute). Also `bfloat16` not supported as true compute. So on Pascal, best GPU compute types are **int8** (via int8_float32) or **float32**. True float16 is not available on CC < 7.0.

**Implications:**
- `int8` gives memory win (weights ~4x smaller) which is critical for 4GB VRAM. Compute win from tensor cores is absent (Pascal has no tensor cores), so int8 speedup on Pascal is more modest than Turing/Ampere - but still often faster than float32 and saves memory.
- `int8_float16` is not a true float16 path on CC 6.1; avoid expecting float16 performance.
- CPU: int8 supported on x86-64 (oneDNN/MKL) and gives good speedup on AVX2; float32 also works.

### Memory sizing (rough guidance)
| Model | fp32 | fp16 | int8 (CT2) | VRAM target (with overhead) |
|---|---|---|---|---|
| base (74M) | ~0.3GB | ~0.15GB | ~0.08GB | < 0.5GB - trivial |
| small (244M) | ~1.0GB | ~0.5GB | ~0.25GB | < 0.8GB |
| medium (769M) | ~3.1GB | ~1.5GB | ~0.8GB | 1.5–2.0GB (tight but possible) |
| large-v3-turbo (809M) | ~3.2GB | ~1.6GB | ~0.9GB | 1.8–2.2GB |
| large-v3 (1.55B) | ~6GB | ~3GB | ~1.6GB | 2.5–3.5GB (could fit in 4GB with care, but slower; CPU very slow) |

But real allocations include input buffers, KV cache, chunking overlap - estimate +20-40% overhead. **base/small** are safe. **medium/turbo** borderline on 4GB depending on implementation. **large-v3** risky.

### Latency reality check (Pascal CPU AVX2)
Pascal GPU: no tensor cores, so Whisper inference is more memory-bandwidth limited for int8. Realistic numbers vary by runtime (faster-whisper/CTranslate2 vs whisper.cpp).

From community benchmarks:
- faster-whisper: on older CPUs int8 often faster than fp32; on GPU Pascal, expect modest gains over CPU. Reported small model CPU int8: ~2-3x realtime in some cases, but need per-chunk (10s) numbers.
- whisper.cpp: optimized for CPU (AVX/AVX2/AVX512), often competitive on CPU-only. AVX2-only is important (no AVX-512). 
- OpenBenchmarking whisper.cpp shows varied results by CPU; i7-8850H is 6-core AVX2 (Coffee Lake era) - expect middle-of-road CPU performance. Small/base models likely run within real-time envelope; medium+ slower.

**Realistic estimates for 10s chunk on i7-8850H (AVX2, 6 cores), faster-whisper int8 CPU:**
- tiny/base (39–74M): p50 ~0.8–1.5s, p95 ~1.8–2.5s (likely < 3s)
- small (244M): p50 ~2–4s, p95 ~4–6s
- medium (769M): p50 ~6–10s, p95 ~12–16s (likely > 8s, borderline/unacceptable for near-real-time)
- large-v3-turbo (809M): similar to medium or better due to fewer decoder layers; p50 ~4–8s, p95 ~8–12s
- large-v3 (1.55B): p50 ~10–15s, p95 ~18–25s (too slow)

On Quadro P2000 (Pascal, int8 via CT2): expect better than CPU for larger models if memory fits, but gains modest vs modern GPUs. Small/base should be fast enough. Medium/turbo may run but latency still several seconds per chunk.

**Conclusion on latency:** Only **tiny/base/small** are realistically viable for near-real-time on this hardware. **medium/turbo** are borderline on latency (especially CPU path); **large-v3** likely too slow. This reinforces starting with **tarteel-ai/whisper-base-ar-quran**.

---

## 5) whisper.cpp as Alternative Runtime

[whisper.cpp](https://github.com/ggml-org/whisper.cpp) is a C/C++ port (GGML) of Whisper, optimized for CPU inference with AVX/AVX2/NEON, no heavy Python deps.

**Pros vs faster-whisper (CTranslate2):**
- Often very fast on CPU (especially with good BLAS/threads). GGML kernels optimized for x86.
- Lower memory overhead in some cases; can run on CPU-only with small footprint.
- Easy to embed; no CUDA runtime version sensitivity beyond GPU build.
- Good for older hardware (AVX2-only fine).

**Cons:**
- Less flexible for some quantization schemes vs CT2; quantization types differ (GGML types).
- GPU support exists (CUDA/OpenCL/Vulkan) but CT2 often better optimized for NVIDIA; on Pascal, differences smaller.
- Pipecat’s WhisperSTTService typically uses faster-whisper/Transformers; integrating whisper.cpp may need adapter, but architecture allows swapping runtime.
- Model format conversion needed (GGUF/ggml) from HF safetensors.

**Recommendation:** Test both. For CPU-dominant path on AVX2-only, whisper.cpp often competitive. For GPU path on Pascal, faster-whisper (CT2 int8) is likely easier. Do head-to-head: same model, same 10s chunk, measure p50/p95 on CPU and GPU.

---

## 6) Tajweed Models (Later Phase)

[Quran Muaalem](https://arxiv.org/abs/2509.00094) (ICML 2026 style work) introduces multi-level CTC model with Quran Phonetic Script (QPS) encoding tajweed rules; reports 75.8% Tajweed F1 on real learner errors (qdat_bench) and strong PER. Model weights: [obadx/muaalem-model-v3_2](https://huggingface.co/obadx/muaalem-model-v3_2) (HF), related repos [Quran Muaalem site](https://obadx.github.io/quran-muaalem/).

**Considerations for 4GB VRAM:**
- Check model size. FastConformer-based variants (e.g. [Muno459/fastconformer-quran](https://huggingface.co/Muno459/fastconformer-quran)) are encoder-heavy ASR+pronunciation heads; sizes vary (CT2/ONNX artifacts smaller). Need to inspect actual weights.
- CT2 int8 quantized builds reduce footprint. ONNX runtime also possible.
- 4GB is tight if running ASR + tajweed model concurrently; may need to run sequentially or use smaller quantized variant.
- License: Quran-Lab No-Profit License (NPL) appears for some Quran Lab artifacts (e.g. [quran-tajweed-phonetics](https://hf.yi-lab.net/datasets/Quran-Lab/quran-tajweed-phonetics), [zipformer_p-arabic-v3](https://huggingface.co/Quran-Lab/zipformer_p-arabic-v3)) - verify muaalem model license on its HF card. [muaalem-model-v3_2](https://huggingface.co/obadx/muaalem-model-v3_2) card should state license (Apache-2.0 or other). Verify before adoption.

**Assessment:** Promising for later phases (tajweed error detection). For initial benchmarking phase, focus on ASR model selection; tajweed is separate pipeline component.

---

## 7) Benchmark Harness Design (Concrete)

### Harness components
1. **Data loader**: Load ~30 hesitant clips + qdat_bench subset (where permitted). Normalize to 16kHz mono.
2. **Transcriber wrapper**: Abstract over faster-whisper (CT2) and whisper.cpp. Same chunking config, same decoding params (beam_size, temperature, language='ar', task='transcribe').
3. **Chunker**: Configurable chunk_length_s {5,10,15}, overlap {0.1,0.5,1.0}s. Start with 10s/0.5s overlap.
4. **Metrics collector**: WER/CER via JiWER or rapidfuzz, per-chunk latency (wall time), GPU mem usage (nvidia-smi/pynvml), CPU mem.
5. **Hesitation artifact classifier**: Manual review of false positives - tag as: pause-induced fragmentation, restart, breath, true error. Count rates.
6. **Ground truth**: Verbatim transcripts of hesitant clips (what was actually recited, including hesitations noted separately). Do not “clean” hesitations from GT when measuring raw error detection behavior.

### Decoding constraints (critical - never bias when scoring)
- **Do NOT use hotwords/initial_prompt** when measuring error scoring. These bias decoder toward expected text and can mask mistakes - this is a hard product constraint. 
- For “which ayah is being recited” identification (context lookup), biasing may be acceptable later; for **scoring errors** (detecting mistakes), decoder must be unbiased.
- Test unbiased decoding: default Whisper decoding with language='ar', no prompt forcing ayah text.
- Beam size: test 1, 3, 5 - larger beams slower, sometimes better accuracy; find balance.

### Test commands (sketch)
```bash
# faster-whisper CPU int8
python bench.py --model tarteel-ai/whisper-base-ar-quran --device cpu --compute_type int8 --chunk 10 --overlap 0.5

# faster-whisper CUDA int8 (Pascal CC6.1)
python bench.py --model tarteel-ai/whisper-base-ar-quran --device cuda --compute_type int8 --chunk 10 --overlap 0.5

# whisper.cpp CPU
whisper-bench -m ggml-base-ar-quran-int8.bin -t 6 --chunk 10
```

### Reporting template
For each run: model, runtime, device/compute_type, chunk config, p50/p95 chunk latency, peak VRAM/RAM, WER/CER on hesitant set, hesitation-artifact rate, notes on OOM/slowdown.

---

## 8) Sources (with URLs, verified)

- Tarteel base card: https://huggingface.co/tarteel-ai/whisper-base-ar-quran (Apache-2.0, WER 5.75%)
- Tarteel tiny card: https://huggingface.co/tarteel-ai/whisper-tiny-ar-quran (Apache-2.0, WER 7.05%)
- Yousifgamalo quran-s-finetuned: https://huggingface.co/yousifgamalo/quran-s-finetuned (Apache-2.0, WER 0.1162 test)
- wasimlhr/whisper-quran-v1: https://huggingface.co/wasimlhr/whisper-quran-v1 (CC-BY-NC-4.0, WER 5.35% best)
- raghadOmar/whisper-quran: https://huggingface.co/raghadOmar/whisper-quran (Apache-2.0, WER 10.34%)
- naazimsnh02/whisper-large-v3-turbo-ar-quran: https://github.com/Naazimsnh02/whisper-large-v3-turbo-ar-quran (Apache-2.0, WER 1.18% test)
- dev-ahmedhany CT2 int8: https://huggingface.co/dev-ahmedhany/whisper-large-v3-turbo-arabic-ft-ct2-int8 (Apache-2.0)
- OpenAI Whisper: https://github.com/openai/whisper (MIT)
- CTranslate2 quantization: https://opennmt.net/CTranslate2/quantization.html
- faster-whisper: https://github.com/guillaumekln/faster-whisper (MIT)
- whisper.cpp: https://github.com/ggml-org/whisper.cpp (MIT)
- QDAT: https://arxiv.org/abs/2107.05209
- qdat_bench: https://huggingface.co/datasets/obadx/qdat_bench (CC BY 4.0), https://arxiv.org/abs/2509.00094
- Quran Muaalem: https://arxiv.org/abs/2509.00094, https://obadx.github.io/quran-muaalem/
- Tadabur: https://huggingface.co/datasets/FaisaI/tadabur (CC BY-NC 4.0)

---

## 9) Next Steps (Execution Order)

1. **Setup harness**: Create `bench.py` that wraps faster-whisper with chunking, metrics, timing. Add whisper.cpp path later.
2. **Collect test data**: Record ~30 hesitant clips, ground-truth verbatim. Download qdat_bench (CC BY 4.0).
3. **Smoke test**: Run tarteel-ai/whisper-base-ar-quran on CPU int8 and CUDA int8 with 10s chunks - verify latency/memory.
4. **Benchmark matrix**: Execute per test matrix (§2). Record all metrics.
5. **Hesitation analysis**: Review outputs, classify artifacts, compute hesitation-artifact rate.
6. **Decision**: Apply decision rule (§2). If base fails on hesitant set, try tiny, small, then others. 
7. **Report**: Document findings, chosen model, configs, measured numbers.

**Immediate action:** Start with tarteel-ai/whisper-base-ar-quran as specified. All other candidates are fallbacks if it does not meet the acceptance criteria on hesitant recitations.