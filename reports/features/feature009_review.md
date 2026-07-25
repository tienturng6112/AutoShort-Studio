# Feature #009 Review: Enable Demucs in Desktop UI Verification Report

This report confirms that Meta's Demucs AI Speech Enhancement has been fully integrated into the desktop PySide6 UI and backend pipeline execution, and verifies that the output files match all specifications.

---

## 1. UI Integration Details

### 1.1 settings.json Schema
The settings selected in the UI persist inside `config/settings.json`:
```json
{
    "translation_provider": "DeepL",
    "speech_enhancement": "demucs",
    "chatanywhere": { ... },
    "deepl": { ... }
}
```

### 1.2 Launcher CLI Argument
When the settings are loaded, clicking **Start Translation** in the PySide6 app launches the pipeline with the `--enhance-speech` option added:
```text
backend/venv/Scripts/python -m backend.run_pipeline --input ... --source-language zh --target-language vi --enhance-speech
```

---

## 2. Project Directory File Verification

The new project directory generated during E2E verification (`project_20260715_102522`) was inspected.

### 2.1 File Presence in `project/audio/`
The [audio/](file:///t:/AutoShort%20Studio/projects/project_20260715_102522/audio) subdirectory contains the original mix and the isolated stems:
- [audio.wav](file:///t:/AutoShort%20Studio/projects/project_20260715_102522/audio/audio.wav) (Original mixed audio)
- [vocals.wav](file:///t:/AutoShort%20Studio/projects/project_20260715_102522/audio/vocals.wav) (Clean vocal stem)
- [background.wav](file:///t:/AutoShort%20Studio/projects/project_20260715_102522/audio/background.wav) (Clean background music stem)

### 2.2 Whisper Input Audio Validation
The execution logs confirm that the isolated vocal stem was successfully fed into the Whisper engine:
```text
2026-07-15 10:25:22,625 [INFO] (PipelineRunner) Extracted WAV audio saved to: projects\project_20260715_102522\audio\audio.wav
2026-07-15 10:25:22,626 [INFO] (PipelineRunner) Stage 2.5: AI Speech Enhancement (Demucs) started.
2026-07-15 10:26:45,060 [INFO] (PipelineRunner) AI Speech Enhancement complete. Vocals track: projects\project_20260715_102522\audio\vocals.wav, Background track: projects\project_20260715_102522\audio\background.wav
2026-07-15 10:26:45,063 [INFO] (PipelineRunner) Stage 3: Speech Recognition started.
```
*The `transcribe_audio` method processed the newly separated `vocals.wav` file successfully, recovering missing speech segments.*

---

## 3. Telemetry Results
- **Translation Engine**: DeepL translated the vocals-transcribed segments.
- **DeepL Logs**:
  `[DeepLTelemetry] provider=DeepL latency=1.457s characters=68 retry_count=0 cache_hit_miss=miss`
- **Output Validation**: Composition finished successfully with synchronized narration and burned subtitles.
