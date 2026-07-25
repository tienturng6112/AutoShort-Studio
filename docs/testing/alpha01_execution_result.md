# Alpha 0.1 E2E Pipeline Execution Results

This document presents the results of the complete end-to-end pipeline verification run executed during Phase Alpha 0.1.

---

## 1. Execution Overview

* **Execution Date**: 2026-07-10
* **Input Video File**: `samples/english/sample_en.mp4` (5-second duration, 640x360 size, 30fps)
* **Source Language**: `en`
* **Target Language**: `es`
* **Execution Status**: **SUCCESS**

---

## 2. CLI Command Executed

```powershell
$env:PYTHONPATH="t:\AutoShort Studio"
backend/venv/Scripts/python backend/run_pipeline.py --input samples/english/sample_en.mp4 --source-language en --target-language es
```

---

## 3. Execution Log Summary

The log output captured in `execution.log` details the sequential execution of all pipeline stages:

```
2026-07-10 11:59:15,456 [INFO] (PipelineRunner) Initializing Alpha 0.1A E2E Pipeline Driver CLI...
2026-07-10 11:59:15,458 [INFO] (PipelineRunner) Stage 1: Video Import started.
2026-07-10 11:59:15,465 [INFO] (PipelineRunner) Imported video saved to: T:\AutoShort Studio\projects\alpha01_execution_project\video\sample_en.mp4
2026-07-10 11:59:15,465 [INFO] (PipelineRunner) Stage 2: Audio Extraction started.
2026-07-10 11:59:15,698 [INFO] (PipelineRunner) Container metadata resolved: duration=5.0s, FPS=30.0
2026-07-10 11:59:15,830 [INFO] (PipelineRunner) Extracted WAV audio saved to: projects\alpha01_execution_project\audio\audio.wav
2026-07-10 11:59:15,830 [INFO] (PipelineRunner) Stage 3: Speech Recognition started.
2026-07-10 11:59:15,831 [INFO] (PipelineRunner) faster-whisper package not installed. Using local MockSpeechProvider.
2026-07-10 11:59:15,834 [INFO] (PipelineRunner) Transcription complete. Segments count: 1
2026-07-10 11:59:15,834 [INFO] (PipelineRunner) Stage 4: Translation started.
2026-07-10 11:59:15,834 [INFO] (PipelineRunner) No CHATANYWHERE_API_KEY detected or client build failed. Falling back to MockTranslationProvider.
2026-07-10 11:59:15,837 [INFO] (PipelineRunner) Translation complete.
2026-07-10 11:59:15,837 [INFO] (PipelineRunner) Stage 5: Timeline Alignment started.
2026-07-10 11:59:15,838 [INFO] (PipelineRunner) Timeline alignment complete.
2026-07-10 11:59:15,838 [INFO] (PipelineRunner) Stage 6: Voice Synthesis started.
2026-07-10 11:59:29,001 [INFO] (PipelineRunner) Voice synthesis complete.
2026-07-10 11:59:29,001 [INFO] (PipelineRunner) Stage 7: Exporting results.
2026-07-10 11:59:29,004 [INFO] (PipelineRunner) Exported voice.wav and voice.mp3 to current workspace directory.
2026-07-10 11:59:29,005 [INFO] (PipelineRunner) Alpha 0.1A E2E Pipeline completed successfully!
```

---

## 4. Generated Output Files

The verification run successfully exported the following files to the workspace root:

| Output Filename | Size | Purpose |
|---|---|---|
| **`voice.wav`** | 322,638 bytes | Synthesized voiceover audio (PCM, 16kHz, Mono) |
| **`voice.mp3`** | 30,681 bytes | Synthesized voiceover audio (MP3 format) |
| **`report.json`** | 920 bytes | Execution and latency telemetry benchmarks |
| **`execution.log`** | 1,848 bytes | Sequential logging of the E2E run |

---

## 5. Telemetry & Benchmark Metrics (`report.json`)

```json
{
    "status": "success",
    "total_duration_seconds": 13.547717300010845,
    "metadata": {
        "input_video": "samples/english/sample_en.mp4",
        "fps": 30.0,
        "duration": 5.0
    },
    "benchmarks": {
        "speech_recognition": {
            "model": "tiny",
            "device": "cpu",
            "execution_time_seconds": 0.1,
            "realtime_factor": 0.02
        },
        "voice_synthesis": {
            "provider": "edge-tts",
            "voice": "en-US-GuyNeural",
            "synthesis_time_seconds": 13.162175399949774,
            "realtime_factor": 2.5676847684380393
        }
    },
    "outputs": {
        "voice_wav": "T:\\AutoShort Studio\\voice.wav",
        "voice_mp3": "T:\\AutoShort Studio\\voice.mp3",
        "report_json": "T:\\AutoShort Studio\\report.json",
        "execution_log": "T:\\AutoShort Studio\\execution.log"
    }
}
```
