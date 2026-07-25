# Alpha 0.1 Pipeline Execution Guide

This document describes the prerequisites, required environments, and steps to execute the end-to-end media pipeline in AutoShort Studio.

---

## 1. Prerequisites

Before running the acceptance pipeline, ensure the following components are configured:

### Required FFmpeg
* `ffmpeg` and `ffprobe` must be installed on your system.
* The directory containing `ffmpeg.exe` and `ffprobe.exe` must be added to your system's `PATH` environment variable.
* Verify installation by running:
  ```powershell
  ffmpeg -version
  ffprobe -version
  ```

### Required Python Packages
Ensure the project's virtual environment is active and contains the necessary dependencies:
* `edge-tts` (Microsoft Edge public TTS interface)
* `faster-whisper` (CTranslate2 Whisper engine)
* `openai` (Python SDK for LLM translation provider calls)
* `pydantic` (Data models)
* `pytest` (Acceptance run tests)

### Required Models
* **Speech Recognition**: The engine will automatically attempt to download the Whisper models (defaulting to the local cache directory). The model size is configurable (e.g. `tiny`, `base`, `small`).
* **Translation**: A valid LLM connection provider config must be registered to run LLM translations.

---

## 2. Sample Videos

Ensure that sample videos are located under the appropriate subdirectories of the root `samples/` folder:
* `samples/english/`: Short test video files in English (e.g. `sample_en.mp4`).
* `samples/japanese/`: Test video files in Japanese (e.g. `sample_jp.mp4`).
* `samples/podcast/`: Longer audio/video files.
* `samples/shorts/`: Vertical aspect ratio clips.
* `samples/music/`: Background tracks.

---

## 3. Execution Steps

To execute the verification pipeline end-to-end:

1. **Activate Virtual Environment**:
   ```powershell
   . backend/venv/Scripts/Activate.ps1
   ```
2. **Execute Acceptance Run Command (Pipeline)**:
   Run the pipeline driver as a module:
   ```powershell
   python -m backend.run_pipeline --input samples\english\sample_en.mp4 --source-language en --target-language es
   ```
3. **Execute Acceptance Test Suite**:
   Run pytest targeting the acceptance package:
   ```powershell
   python -m pytest backend/tests/acceptance/
   ```

---

## 4. Expected Outputs

A successful execution will write all output assets inside the designated project directory (under the configured `projects_root`):
* `video/`: Imported raw video track file.
* `audio/audio.wav`: Extracted 16kHz mono PCM voiceover WAV file.
* `subtitle/transcript.json` & `subtitle/transcript.srt`: Speech recognition transcripts.
* `translation/translated_transcript.json` & `translation/translated_transcript.srt`: Translated transcripts.
* `subtitle/aligned_transcript.json` & `subtitle/aligned_transcript.srt`: Time-aligned timelines.
* `render/voice.wav` & `render/voice.mp3`: Output normalized audio tracks.

---

## 5. Troubleshooting

* **FFmpeg Not Found**:
  * *Symptoms*: FileNotFoundError when demuxing audio or generating silences.
  * *Fix*: Ensure `ffmpeg` is in the environment PATH. Test it directly from your command shell.
* **Network Failures on TTS**:
  * *Symptoms*: Timeout or connection error logs during EdgeTTS executions.
  * *Fix*: Verify internet connectivity, as EdgeTTS communicates with Microsoft's public API.
* **Whisper Download Failures**:
  * *Symptoms*: Errors loading Whisper models.
  * *Fix*: Ensure the cache directory is writable, or manually download model weight repositories.
