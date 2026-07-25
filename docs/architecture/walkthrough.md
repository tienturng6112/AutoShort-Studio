# Walkthrough: Speaker Diarization, Voice Mapping, Translation & TTS Provider Updates

This walkthrough documents the code modifications, verification scripts, and results for the latest features implemented.

---

## 1. Features Implemented

### 1.1 Translation Prompt Updates (Feature #009)
- **[chatanywhere_provider.py](file:///t:/AutoShort%20Studio/backend/translation/chatanywhere_provider.py)**:
  - Updated Vietnamese system instructions to include contextual pronoun selection:
    - **Inference**: Infer relationship pronouns from dialogue history.
    - **Consistency**: Keep identical pronouns throughout the timeline.
    - **Omission**: Omit pronouns on uncertainty.
    - **Proper Names**: Avoid translating proper names to pronouns.
    - **Style**: Maintain emotional tone, humor, sarcasm, and natural conversational Vietnamese.

### 1.2 Speaker Diarization Foundation (Feature #011A)
- **[models.py](file:///t:/AutoShort%20Studio/backend/speech/models.py)**:
  - Integrated `speaker_id` key in the segment dataclass.
- **[diarization.py](file:///t:/AutoShort%20Studio/backend/speech/diarization.py)**:
  - Added modular `BaseDiarizationProvider`, `PyannoteDiarizationProvider` (production PyAnnote), and `MockDiarizationProvider` (fallback alternating turns).
  - Matches timeline timings to associate a speaker to each transcript segment.
- **[run_pipeline.py](file:///t:/AutoShort%20Studio/backend/run_pipeline.py)**:
  - Inserted **Stage 3.5: Speaker Diarization** producing `speaker_map.json`.

### 1.3 Speaker Voice Mapping (Feature #011B)
- **[voice_service.py](file:///t:/AutoShort%20Studio/backend/tts/voice_service.py)**:
  - Modified `synthesize_transcript` to accept custom speaker-voice mapping dicts and resolve segment voices.
- **[desktop_app.py](file:///t:/AutoShort%20Studio/desktop_app.py)**:
  - Added Speaker Voices Config options to settings dialog, loading all Edge-TTS neural voices and persisting mappings inside `config/settings.json`.

### 1.4 Smart Voice Manager (Feature #011C)
- **[desktop_app.py](file:///t:/AutoShort%20Studio/desktop_app.py)**:
  - **Locale Filtering**: Filters voices list based on the active target language of the MainWindow.
  - **Friendly Names**: Displays nice names like `Hoài My (Female)` instead of Microsoft technical IDs.
  - **Previews**: Added `[▶ Preview]` buttons playing sample synthesis clips using `QMediaPlayer`.
  - **Diarization summaries**: Extracts and displays segment counts and durations per speaker from the latest project folder.

### 1.5 Fix Voice Preview (Issue #012)
- **[desktop_app.py](file:///t:/AutoShort%20Studio/desktop_app.py)**:
  - Updated preview text language selection to resolve strictly based on the target language combobox.
  - Releases player locks using `self.player.stop()` and `self.player.setSource(QUrl())` before writes.
  - Generates unique filenames for preview requests (`temp_preview_<uuid>.mp3`).
  - Clears out older files inside `projects/temp_preview/` folder.

### 1.6 Voice ID Mapping Fix (Issue #013)
- **[edge_tts_provider.py](file:///t:/AutoShort%20Studio/backend/tts/edge_tts_provider.py)**:
  - Changed voice `"name"` lookup key to use `"ShortName"` with fallback to `"Name"` for test harness mock compatibility.

### 1.7 Kira AI TTS Provider Integration (Feature #021)
- **[kira_provider.py](file:///t:/AutoShort%20Studio/backend/tts/kira_provider.py)**:
  - Implemented the `KiraProvider` class conforming to the `BaseTTSProvider` abstract interface.
  - Integrates with Kira's OpenAI-compatible speech endpoint (`POST https://kiraai.vn/api/v1/audio/speech`) and queries supported voices via `GET /api/v1/audio/voices`.
  - Returns raw synthesized bytes synchronously without polling.
  - Provides static fallbacks for popular Kira voices (Aoede, Fenrir, Kore, Charon, Puck).
- **[tts_provider.py](file:///t:/AutoShort%20Studio/backend/tts/tts_provider.py)**:
  - Updated `TTSProviderFactory` to support dynamic creation of `KiraProvider` under the `"Kira"` configuration path.
- **[run_pipeline.py](file:///t:/AutoShort%20Studio/backend/run_pipeline.py)**:
  - Integrated `TTSProviderFactory.create()` to dynamically build the Kira provider in Stage 6.
- **[desktop_app.py](file:///t:/AutoShort%20Studio/desktop_app.py)**:
  - Replaced the AusyncLab UI layout with a clean "Kira Config" group box containing inputs for `API Key`, `Model Name`, `Speed (0.25-4.0)`, and `Test Connection` / `Preview`.
  - Replaced all connection/preview workers to target the Kira backend.
  - Persisted settings under `settings["kira"]` and `settings["tts_provider"] = "Kira"`.

---

## 2. Verification Results

### 2.1 E2E Pipeline and Unit Tests
- Pytest suite successfully executed passing all 55 tests (including the new `test_kira_provider_and_factory` test).
- Run logs confirm that all voice synthesis configurations compile and behave correctly under mock environments.

### 2.2 Programmatic UI Settings Check
Run log for [test_kira_settings.py](file:///C:/Users/DN%20GROUP/.gemini/antigravity-ide/brain/ee01ae7b-52ea-4655-9b59-09ab109251d2/scratch/test_kira_settings.py):
```text
Constructing MainWindow and SettingsDialog...
Configuring Kira settings in UI...
Calling save_settings()...
Reading saved config from: config/settings.json
  tts_provider: 'Kira'
  kira config: {'api_key': 'my-test-kira-key', 'model': 'kira-3.0-flash-tts', 'speed': 1.2}
  Success: 'ausynclab' key is removed from settings.

Verification SUCCESS: Kira settings persisted correctly!
```
