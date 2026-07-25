# Alpha 0.1 Pipeline Execution Documentation

This document describes the CLI interface, execution logic, and generated outputs for the Alpha 0.1 end-to-end pipeline driver.

---

## 1. CLI Command & Parameters

The pipeline runner CLI is implemented at `backend/run_pipeline.py` and supports the following input flags:
* `--input`: (Required) Path to the source MP4 video file.
* `--source-language`: (Optional) Speech recognition audio language code (defaults to `"en"`).
* `--target-language`: (Optional) Target translation language code (defaults to `"es"`).

### Run Command Example:
```powershell
python backend/run_pipeline.py --input samples/english/sample_en.mp4 --source-language en --target-language es
```

---

## 2. Pipeline Execution Stages

The pipeline driver executes 7 stages sequentially:
1. **Video Import**: Creates project folders and imports raw video to `video/`.
2. **Audio Extraction**: Runs FFmpeg to demux a mono 16kHz WAV track to `audio/audio.wav`.
3. **Speech Recognition**: Downloads/loads local Whisper `tiny` weights and transcribes speech into timestamps.
4. **Translation**: Translates text. If `CHATANYWHERE_API_KEY` is not present, it automatically falls back to an offline `MockTranslationProvider` ensuring verification runs compile without API restrictions.
5. **Timeline Alignment**: Solves segment timing overlaps, merges small neighbor segments, splits line length overflows, and saves aligned transcripts.
6. **Voice Synthesis**: Generates audio segments via EdgeTTS, inserts gap silences, merges tracks, normalizes to EBU R128 loudness limits, and writes WAV/MP3 files.
7. **Export**: Copies the final synthesized voiceover tracks and execution telemetries into the current directory.

---

## 3. Generated Outputs

The pipeline produces four core output files in the root workspace folder:
* **`voice.wav`**: Standard mono 16kHz PCM loudness-normalized wav file containing synthesized audio matching transcript gaps.
* **`voice.mp3`**: Standard stereo 16kHz EBU R128-normalized MP3 copy.
* **`report.json`**: Telemetry benchmarks file containing total latency, import metadata, Whisper models settings, and realtime factor factors.
* **`execution.log`**: Debugging file detailing logger timestamps and exceptions during execution.
