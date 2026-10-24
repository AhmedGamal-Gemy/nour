# Recording guide — Phase 0 eval clips

This gates everything. The harness, the teacher conversation, the model choice —
all of them wait on these recordings. Nothing else is worth doing until they
exist.

## What you are recording

**Your own recitation.** Hesitant, imperfect, the real thing. Not a performance.

The corpus does not exist publicly in this form. These clips are the only
training signal the model will ever get for *your* voice, *your* stumbles, *your*
mistakes. They are the most valuable thing in this project.

## How much

| | |
|---|---|
| Clips | ~30 |
| Length | 30–60 seconds each |
| **Total time** | **~30 minutes** |
| Format | Phone voice memos — fine as-is |

Thirty minutes of *imperfect* recitation. The fluent parts are easy and the
model does not need them. You are recording the stumbles.

## What makes a clip good

- At least one hesitation, repeat, or wrong word per clip
- Mix of surahs — not all from one
- Same mic setup throughout (don't switch between phone and headset mid-session)
- You are reading from memory, not the book

## What breaks a clip

- **All-fluent** — no signal for the model to learn from. Discard, record again.
- **Background noise** — car, TV, other voices. The model cannot separate it.
- **Too short** (< 10 seconds) — not enough ayahs to align against.
- **Reading from the mushaf** — sight-assisted recitation is not what this
  measures. The harness scores free recall only.

## How to record

1. Open your phone's voice memo app.
2. Pick an ayah or short passage you are learning or have learned.
3. Start recording.
4. Recite from memory. Let the stumbles happen. Do not stop and restart the
   recording when you make a mistake — that's the signal. One continuous take.
5. Stop when you have covered the passage, or 60 seconds, whichever comes first.
6. Name the file something useful: `surah-name_ayah-range.mp4`. Example:
   `al-baqara_2_255-257.mp4`.

Repeat 30 times. Vary the surahs. Do not overthink which ayahs — anything you
are actually working on is perfect.

## Where they live

- Default: `data/clips/` — **gitignored**. These are personal audio, not
  committed.
- Exception: a few sanitised clips may be committed as CI regression fixtures.
  Decide explicitly when the harness exists. Do not commit raw clips.

## After recording

1. **The teacher conversation** — hand the clips to a sheikh. 30 minutes. The
   ask is in `PLAN.md` §9b. This is the highest-value step and it is sitting
   unstarted.
2. **Label ground truth** — per clip, per word: correct / substitution / deletion
   / insertion / hesitation. The harness needs this to score anything.
3. **Build the harness** — `jiwer` + `WhisperX` + `hifz-tester`'s alignment
   engine. See `PLAN.md` Phase 0.

## One rule

Do not record 30 clips of perfect recitation and then discover the model has
nothing to learn. The value is in the mistakes. If every clip is clean, the
harness is measuring fluency, not error detection — and that's the wrong thing
to measure.