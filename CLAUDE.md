# Quran Hifz Assistant (voice agent) - Project Handoff

Owner: Gemy (Ahmed Gamal). Written 2026-11-20 from a Claude chat session, for continuing in Claude Code.
Reply to Gemy in English only. Keep answers short and direct. When he asks for a decision, give it immediately.
Gemy keeps shared memory in Notion ("Agent Memory" page, id 413c8b5d-4af4-8160-98e6-ddd1e342226d, subpage "Quran"). Entry format: `- YYYY-MM-DD: fact (source: agent name)`. Update it whenever he shares something new, before replying.

## 1. The idea (as Gemy described it)

A voice agent that listens while Gemy recites from memory (hifz) and:

1. **Corrects him when he goes wrong** (wrong word, skipped ayah, wrong harakah, jump to a similar verse).
2. **Interrupts with similar verses (mutashabihat):** says where else the same or a similar ayah appears, by wording or by meaning.
3. **Tracks his hifz progress.**

Origin: a sheikh's assistant used to drill him on similar verses while he memorized. He found it beautiful and helpful, and wants to rebuild that experience.

Status: long-buried idea, he decided to start building it on 2026-11-20 (he was tired, so start small).

Context:
- Personal project, separate from his DataQueue job. Monetization is secondary; he mainly wants the idea to see the light.
- Sama El Moataz (built Quran Semantic Search) wants to hear the details and start simple, then grow step by step. A call is not scheduled yet. Gemy will explain details in a meeting, not in chat.

## 2. Hard requirement (decided by Gemy)

**Exact comparison with tashkeel on both sides. No fuzzy matching.** Fuzzy matching would hide exactly the mistakes he wants caught. The hardest part of the project is speech-to-text that is correct and diacritized.

Design consequence: in hifz he already knows what he is reciting. So the user declares the surah and start ayah and the agent tracks position. No "which ayah is this?" search is needed, so no fuzzy matching is needed. Compare the recitation against the expected text for that position.

## 3. Research findings (web search, 2026-11-20)

### Plain ASR does not give reliable tashkeel
- Pre-trained Whisper produces full diacritics for some Quranic verses but not all, and almost none for casual MSA (arXiv 2302.14022, "Diacritic Recognition Performance in Arabic ASR").
- A comparison space of Quran-tuned Whisper models (IJyad/whisper-large-v3-Tarteel, deepdml/whisper-medium-ar-quran-mix-norm, naazimsnh02/whisper-large-v3-turbo-ar-quran, Habib-HF/tarbiyah-ai-whisper-medium-merged) notes their output is plain Arabic, usually without tashkeel.
- Community model with diacritics: moatazlumin/Arabic_ASR_whisper_small_with_diacritics (Whisper small, fine-tuned on a Quran reciters dataset), WER 16.9. Too weak for exact comparison.
- A study of Quranic ASR on 870+ hours found undiacritized labels worked particularly well. Good for letter-level checking, not for harakat.
- A wav2vec2 harakat-error study reported WER about 0.37 for words plus harakat. Reliable harakat detection is hard, so expect tuning.

### Best lead: Quran Muaalem (obadx)
Open source (MIT), built for exactly this: pronunciation and recitation error detection at the phoneme level, with a tashkeel error type.
- Docs: https://obadx.github.io/quran-muaalem/en/
- Code: https://github.com/obadx/quran-muaalem
- Paper: arXiv 2509.00094, "Automatic Pronunciation Error Detection and Correction of the Holy Quran's Learners Using Deep Learning" (Abdelfattah, Khalil, Abbas).
- Reported in the paper: 848 hours of audio (286K annotated utterances), qdat_bench benchmark (phonemes, diacritization, Tajweed rules: Ghunnah, Qalqalah, Madd; 159 real-error samples), a 98% automated data pipeline, a Quran Phonetic Script (QPS) that encodes Tajweed rules, and the "Tasmeea" algorithm for verifying transcripts.
- Hugging Face model: `obadx/muaalem-model-v3_2`. Dataset: `obadx/muaalem-annotated-v3`. PyPI: `quran-muaalem`; toolkit `quran-transcript`.
- Model uses a multi-level CTC head (phonemes plus tajweed attributes) and compares predicted phonemes to a reference phonetic script made by `quran_transcript.quran_phonetizer`.

Install (from the README):
- System packages: `ffmpeg`, `libsndfile1`, `portaudio19-dev`
- `pip install quran-muaalem librosa "numba>=0.61.2"`
- Gradio UI: `uvx quran-muaalem[ui] quran-muaalem-ui`
- Servers: `uv add quran-muaalem[engine]`, then `quran-muaalem-engine` (port 8000) and `quran-muaalem-app` (port 8001) via `uv run`

Minimal usage (from the README, condensed; verify against the repo):
```python
import torch
from librosa.core import load
from quran_transcript import Aya, MoshafAttributes, quran_phonetizer
from quran_muaalem import Muaalem

uthmani_ref = Aya(8, 75).get_by_imlaey_words(17, 9).uthmani
moshaf = MoshafAttributes(rewaya="hafs", madd_monfasel_len=2,
                          madd_mottasel_len=4, madd_mottasel_waqf=4,
                          madd_aared_len=2)
ref = quran_phonetizer(uthmani_ref, moshaf, remove_spaces=True)

device = "cuda" if torch.cuda.is_available() else "cpu"
muaalem = Muaalem(device=device)
wave, _ = load("./assets/test.wav", sr=16000, mono=True)
out = muaalem([wave], [ref], sampling_rate=16000)[0]
print(out.phonemes.text)
for sifa in out.sifat:
    print(sifa)
```

Output:
- `phonemes`: `text`, `probs` (confidence per phoneme), `ids`.
- `sifat`: one entry per phoneme (`phonemes_group` plus optional features such as hams_or_jahr, shidda_or_rakhawa, tafkheem_or_taqeeq, itbaq, safeer, qalqla, tikraar, tafashie, istitala, ghonna), each with `text`, `prob`, `idx`.
- `/correct-recitation` endpoint returns mismatches: `start`/`end`, `predicted_phonemes`, `reference_phonemes`, `uthmani_text`, and an `errors` list. Each error has `error_type` (tajweed, normal, or tashkeel), `speech_error_type` (insert, delete, replace), expected vs predicted phonemes and lengths, and the relevant tajweed rules.

Requirements: audio must be 16 kHz; default max clip length 15 s (ayah-by-ayah fits); about 1.5 GB GPU memory, falls back to CPU (slower); engine supports cuda, cpu, mps; default dtype bfloat16; MIT license.

### Other relevant papers (leads, not checked in depth)
- Iqra'Eval shared task systems for phoneme-level Quranic mispronunciation detection (ACL Anthology 2025.arabicnlp-sharedtasks.62 and .66), e.g. wav2vec2-xls-r-1b fine-tunes with a Quranic phonemizer.
- Quran-MD dataset paper, arXiv 2601.17880.

### Datasets (if training or fine-tuning is needed)
- Rdyh/everyayah: 4 reciters, about 174 hours, fully diacritized text per ayah (MP3, 16 kHz).
- abosalah/Part_of_tarteel_ai_everyayah_dataset: 19 reciters (subset of Tarteel EveryAyah).
- Buraaq/quran-md-ayahs: 187,080 verse-level samples, 32 reciters (word-level set: Buraaq/quran-md-words, 77,429 samples).
- quranlab/quran-audio: verse-aligned references and word timing (CC-BY); it hosts no audio, you fetch audio from the source CDN under its terms.
- zaibihassan/Quranic-Recitation-Data: word-by-word timing with per-surah audio.
- Check each dataset's license and quality before using it.

## 4. What is NOT verified
- Accuracy on Gemy's own voice and learner pace. The model was trained on expert reciters, so false errors are possible. Test first.
- Real-time or streaming behavior for live interruptions. Short clip per ayah is fine; streaming is unconfirmed.
- Whether the output cleanly separates which harakah was said versus expected in every case. Test with deliberate mistakes.
- Exact current README details may have changed. Re-read the repo.

## 5. Plan (start small)

1. **Smoke test (tonight/tomorrow):** record Gemy reciting one ayah he knows well, once correctly and once with a deliberate harakah mistake, 16 kHz mono. Run both through the Gradio UI or the Python example. Pass condition: correct one passes, mistaken one shows a tashkeel error at the right spot.
2. **Wrapper script:** given surah, ayah, and a wav file, build the reference with `quran_phonetizer`, run Muaalem, print mismatches in plain language (word, expected vs heard, error type).
3. **Position tracking:** user declares start surah/ayah; the agent advances ayah by ayah, and reports errors per ayah.
4. **Progress tracking:** store per-ayah results (date, pass/fail, error types) in a simple local store (SQLite or JSON). Later: link to Gemy's Notion Quran page.
5. **Similar verses (mutashabihat):** build an index of similar-ayah groups (wording similarity first, meaning similarity later via embeddings; Quran Semantic Search by Sama is related prior art). Trigger: when the current ayah has twins, tell him where else it appears.
6. **Voice loop:** mic capture, chunk at ayah or pause boundaries, optional TTS for spoken corrections. Handle the 15 s limit and interruptions. Gemy's stack is Google ADK, LiteLLM, FastAPI, Redis, LangGraph, Qdrant, MCP, so use these where they fit (Qdrant for the similar-verse index is a natural match).
7. **Only if Muaalem is not accurate enough:** fine-tune on diacritized data (section 3 datasets), then tune thresholds on Gemy's voice.

## 6. Notes
- Keep this a personal project, separate from DataQueue work.
- Be careful with false corrections: a wrong "correction" of sacred text is worse than a missed one. Prefer reporting confidence and letting Gemy decide, at least at first.
- Gemy works long hours (two jobs); keep steps small and give a clear next action each time.
