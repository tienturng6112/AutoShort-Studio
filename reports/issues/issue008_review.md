# Issue #008 Review: Missing Translation at 00:41 Investigation

This report investigates the observed behavior where the original Chinese subtitle `"要好好吃饭啊"` remains visible in the output video around `00:41` without corresponding Vietnamese subtitles or narration.

---

## 1. Artifact Search Results

A text search (literal and Unicode-escaped formats) was performed on every pipeline artifact generated during the latest E2E run (`project_20260714_164547`):

| Pipeline Artifact | Existence of "要好好吃饭" / "要好好吃饭啊" | Status / Observation |
| :--- | :---: | :--- |
| **`raw_whisper_segments.json`** | **Not Found** | Raw output from Whisper (without enhancement). |
| **`transcript.json`** | **Not Found** | Input to translation stage. |
| **`translated_transcript.json`** | **Not Found** | Output of translation stage. |
| **`subtitle.srt`** | **Not Found** | Subtitles burned into the final video. |
| **`speech_input.txt`** | **Not Found** | Aggregated text sent to Edge-TTS. |
| **`tts/` folder** | **Not Found** | Contains 14 dialogue WAVs; no wav corresponds to this segment. |
| **`voice.wav` timeline** | **Not Found** | Silent gap between `35.52`s and `60.16`s. |

---

## 2. Point of Omission / Disappearance

- **Omission Stage**: The text was **never transcribed at Stage 3 (Speech Recognition)**.
- **Root Cause**: 
  - The E2E run command was executed **without** the optional `--enhance-speech` flag (Demucs AI Speech Enhancement).
  - Without vocals isolation, the heavy background music masked the speaker's voice in the source video.
  - Faster-Whisper and Silero VAD classified this timeline region (`35.52s` to `60.16s`) as non-speech/silence and omitted it from the raw transcript.
  - Since it never entered the transcript, it was not translated, synced, or synthesized.

---

## 3. Explanation of Visible Chinese Subtitle

- **Why is the Chinese subtitle still visible at 00:41?**
  - The Chinese subtitle is **hardcoded (burned) into the source video track** of the input file.
  - Our pipeline composites the output video by keeping the original video stream (including its burned-in Chinese text) and burning the Vietnamese subtitle track on top of it.
  - Because no Vietnamese subtitle was generated for this region, the original burned-in Chinese text remains visible on screen with silence on the narration track.
