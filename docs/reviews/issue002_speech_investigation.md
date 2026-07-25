# Speech Recognition Stage Investigation (Issue #002)

This report details the investigation of the Speech Recognition stage and why the E2E pipeline generates a short 6-second video with a single translated sentence.

---

## 1. Speech Provider Verification
* **Active Provider**: **MockSpeechProvider**
* **Provider Type**: Evaluates to `MockSpeechProvider` because the `faster-whisper` package is not installed in the virtual environment. In `backend/run_pipeline.py` (lines 121–125), importing `faster_whisper` raises an `ImportError`, triggering the inline mock transcript fallback.

---

## 2. Transcript Telemetry Verification

The generated transcript file [transcript.json](file:///t:/AutoShort%20Studio/projects/project_20260713_155634/subtitle/transcript.json) contains:

* **Number of segments**: 1 segment.
* **First segment**:
  - `id`: 0
  - `start`: 0.5s
  - `end`: 70.437007s
  - `text`: `"这是一个关于Alpha 0.1A端到端管道测试的视频。"`
* **Last segment**: (Same as the first segment, as it is the only segment).
* **Total duration**: 70.937007 seconds.

---

## 3. Root Cause Analysis (Single Segment & 6s Output Video)

1. **Fallback Mock Trigger**: Because the virtual environment lacks `faster-whisper`, the pipeline falls back to hardcoded mock values.
2. **Single Segment Generation**: The mock generator creates exactly **one** Chinese sentence segment mapping the entire timeline length of the video (`0.5s` to `70.437s`).
3. **TTS Voice Synthesis Duration**: When sending the translated text (`"This is a video about the Alpha 0.1A end-to-end pipeline test."`) to the TTS engine, the synthesized speech audio is only **~6 seconds** long.
4. **Timeline Truncation**: During Stage 8 (Video/Audio Composition), the video is trimmed/stitched to align with the generated TTS voice track duration (~6 seconds), discarding the rest of the silent video frames.
