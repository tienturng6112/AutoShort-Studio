# AutoShort Studio - Sprint 10 Voice Synthesis Review

This document provides a comprehensive review of the Voice Synthesis Engine developed during Sprint 10.

---

## 1. Executive Summary

Sprint 10 builds the Voice Synthesis Engine for AutoShort Studio, translating text transcripts into natural-sounding speech. The engine operates independently of cloud providers by integrating the open Microsoft Edge TTS interface, which requires no API keys. The synthesis pipeline inserts silent gaps based on timeline coordinates, normalizes loudness according to video standards, downmixes to mono, resamples to 16kHz, and caches files to prevent redundant synthesis requests.

---

## 2. Folder Tree

The directory tree of the Voice Synthesis Engine is structured as follows:

```
backend/
├── tts/
│   ├── __init__.py
│   ├── audio_merger.py           # FFmpeg concat demuxer wrapper
│   ├── audio_normalizer.py       # FFmpeg loudnorm filter wrapper
│   ├── edge_tts_provider.py      # EdgeTTS concrete adapter
│   ├── silence_generator.py      # FFmpeg anullsrc silence wrapper
│   ├── tts_provider.py           # Base TTS interface definition
│   ├── voice_cache.py            # MD5 file cache system
│   ├── voice_manager.py          # Voice registry and filtering service
│   └── voice_service.py          # Timeline voice service orchestrator
```

---

## 3. File Statistics

### Files Added:
* `backend/tts/edge_tts_provider.py`
* `backend/tts/voice_manager.py`
* `backend/tts/voice_cache.py`
* `backend/tts/silence_generator.py`
* `backend/tts/audio_merger.py`
* `backend/tts/audio_normalizer.py`
* `backend/tts/voice_service.py`
* `backend/tests/test_voice_synthesis.py`

### Files Modified:
None since initial scaffolding.

---

## 4. New Services

1. **`EdgeTTSProvider`**: Interfaces with `edge-tts` to list voices and stream audio bytes, parsing 100ns units into word alignment seconds.
2. **`VoiceManager`**: Manages registered TTS providers and handles queries for available voices.
3. **`VoiceCache`**: Caches audio files using MD5 hashes to prevent redundant synthesis requests.
4. **`SilenceGenerator`**: Runs FFmpeg's `anullsrc` virtual filter to generate mono 16kHz silent audio clips.
5. **`AudioMerger`**: Sequential concatenator wrapping FFmpeg's `concat` demuxer to merge audio clips.
6. **`AudioNormalizer`**: Downmixes channels to mono, resamples to 16kHz, and normalizes volume to EBU R128 (-16 LUFS) standards.
7. **`VoiceService`**: The pipeline orchestrator.

---

## 5. Pipeline Stages

The voice synthesis pipeline runs in the following order:
1. **Initial Silence Check**: Inserts initial silence if the first segment start time is greater than 0.
2. **Segment Synthesis & Caching**: Processes segments, checking the cache and generating new clips when needed.
3. **Gap Silence Insertion**: Inserts silence clips in the timeline gaps between consecutive segments.
4. **Audio Merging**: Concatenates speech and silence segments into a single raw WAV file.
5. **Loudness Normalization & Format Export**: Normalizes the merged audio to EBU R128 standards and exports it as `voice.wav` and `voice.mp3`.
6. **Benchmark Logging**: Records performance metrics (execution time, realtime factors).

---

## 6. Export Formats

The voice engine exports the following files:
* **`voice.wav`**: Resampled, loudness-normalized mono WAV file (optimized for video compositing).
* **`voice.mp3`**: Resampled, loudness-normalized MP3 file.

---

## 7. Performance & Verification Summary

### Unit Tests
We have 7 unit test cases covering all aspects of the pipeline (`test_voice_synthesis.py`):
* `test_edge_tts_provider_voices_and_generate`: Verifies voice lists and offset calculations.
* `test_voice_manager`: Checks voice filtering rules.
* `test_voice_cache`: Checks cache hits and invalidations.
* `test_silence_generator`: Checks FFmpeg virtual silence generation.
* `test_audio_merger`: Verifies FFmpeg list concat operations.
* `test_audio_normalizer`: Checks resampling and loudness filter calls.
* `test_voice_service_pipeline`: Tests the complete voice synthesis pipeline.

All 45 project tests pass cleanly!

### Performance Notes
* **FFmpeg Stream Copying**: `AudioMerger` uses FFmpeg's stream copy command (`-c copy`), which concatenates audio files without re-encoding them, reducing processing times.
* **Granular Hashing Cache**: Caching at the segment level allows the engine to reuse translations and speech files across different project iterations.

### Known Limitations
* **Network Latency**: Microsoft Edge TTS requires internet connectivity. If the server is slow, the synthesis request will experience latency.
* **Subprocess Commands Requirement**: The engine requires `ffmpeg` and `ffprobe` to be available in the system's `PATH`.

---

## 8. Remaining TODOs

* **Sprint 11**: Workflow Engine Orchestrator Nodes.
