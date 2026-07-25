# AutoShort Studio - Alpha 0.1 Verification Test Plan

This document outlines the validation test plan and acceptance standards for the Alpha 0.1 release of AutoShort Studio.

---

## 1. Acceptance Criteria

To be ready for Alpha 0.1 release, the system must meet the following criteria:
* **Compilation**: Every module compiles without syntax or type errors.
* **Test Pass Rate**: 100% of unit and integration tests must pass.
* **Subprocess Stability**: FFmpeg, FFprobe, and yt-dlp commands must execute successfully without raising subprocess errors.
* **Accuracy**: Generated timing alignments (SRT/JSON) must be accurate, and generated voice tracks must match segment boundaries.

---

## 2. End-to-End Pipeline

The end-to-end media generation pipeline flows as follows:

```
[Local/URL Media Video]
         │
         ▼
[Project Scaffolding] -> Scaffolds video/, audio/, subtitle/, logs/ folders
         │
         ▼
[Video Importing]     -> Downloads via yt-dlp or copies local files
         │
         ▼
[Audio Demuxing]      -> Extracts 16kHz Mono PCM WAV audio using FFmpeg
         │
         ▼
[Speech Recognition]  -> Transcribes audio to JSON using faster-whisper
         │
         ▼
[AI Scriptwriting]    -> Generates script suggestions from LLM prompts
         │
         ▼
[Translation Engine]  -> Translates script segments using LLM provider
         │
         ▼
[Timeline Alignment]  -> Resolves timeline overlaps, splits, and merges segments
         │
         ▼
[Voice Synthesis]     -> Generates voice.wav and voice.mp3 using EdgeTTS & FFmpeg
```

---

## 3. Test Scenarios

### Scenario A: Local File Import and Synthesis
- **Input**: A local 10-second MP4 video file.
- **Workflow**: Copy file, extract audio, transcribe, translate, align timelines, and synthesize voice audio.
- **Expected Outcome**: Standard project directories are created, metadata is extracted, and `voice.wav` and `voice.mp3` are generated.

### Scenario B: Remote YouTube Import and Synthesis
- **Input**: A valid YouTube video URL.
- **Workflow**: Download video via `yt-dlp`, extract audio, transcribe, translate, align timelines, and synthesize voice audio.
- **Expected Outcome**: The video is successfully downloaded, and aligned transcripts and normalized voiceover files are generated.

### Scenario C: Timeline Collision Optimization
- **Input**: A translated transcript containing overlapping segments and zero durations.
- **Workflow**: Run `TimelineAlignmentService`.
- **Expected Outcome**: Timestamps are optimized to eliminate overlaps, minimum durations are enforced, and sequential IDs are reindexed.

---

## 4. Required Sample Videos

* **Sample A (Short Local Clip)**: 10-second `test_clip.mp4` (H.264 video + AAC stereo audio, 1080p, 30fps).
* **Sample B (YouTube Link)**: A public, short 30-second YouTube clip containing spoken dialogue.

---

## 5. Success Criteria

* **Loudness Normalization**: Output audio must match EBU R128 (-16 LUFS +/- 1.0 LUFS) volume guidelines.
* **Timing Precision**: Voice synthesis files must be aligned with segment timestamps.
* **Integrity**: Segments in the output `translated_transcript.json` must retain the original segment IDs.

---

## 6. Failure Criteria

* **Subprocess Collisions**: Any unhandled `subprocess.CalledProcessError` exceptions from FFmpeg/FFprobe/yt-dlp.
* **Invalid Timelines**: Negative segment durations, overlapping timestamps, or empty segment text.
* **Data Loss**: Truncated segments, or missing words metadata in output transcripts.

---

## 7. Manual Verification Steps

1. **Scaffold Project**:
   Run `ProjectService.create_project("alpha_proj_01", "Alpha Project")` and verify all project folders are created.
2. **Import Local Video**:
   Run `LocalImporter.import_media("samples/test_clip.mp4", "projects/alpha_proj_01/video/")` and verify the video is copied.
3. **Extract Metadata**:
   Run `MetadataExtractor.extract_metadata()` and verify it returns valid duration, FPS, and codec details.
4. **Demux Audio**:
   Run `AudioExtractor.extract_audio()` and verify the output is a 16kHz mono PCM WAV file.
5. **Transcribe**:
   Run `SpeechService.transcribe_audio()` and verify it outputs `transcript.json` and `transcript.srt`.
6. **Translate**:
   Run `TranslationService.translate_transcript()` to translate the transcript into Spanish (`es`) and verify segment structures are preserved.
7. **Align Timeline**:
   Run `TimelineAlignmentService.align_transcript()` to split/merge segments and verify overlaps are resolved.
8. **Synthesize Voice**:
   Run `VoiceService.synthesize_transcript()` to generate the final audio files.

---

## 8. Expected Outputs

The following files must be generated in `projects/alpha_proj_01/` after running the pipeline:
* `video/youtube_download.mp4` (if using YouTube import)
* `audio/audio.wav` (raw audio extraction)
* `metadata/metadata.json` (extracted video metadata)
* `subtitle/transcript.json` & `subtitle/transcript.srt` (English transcript)
* `translation/translated_transcript.json` & `translation/translated_transcript.srt` (Translated transcript)
* `subtitle/aligned_transcript.json` & `subtitle/aligned_transcript.srt` (Aligned timeline)
* `render/voice.wav` & `render/voice.mp3` (Final normalized audio)

---

## 9. Performance Metrics

* **Import Latency**: Local copies should take less than 1.0 second. YouTube downloads depend on network speed.
* **Audio Extraction Speed**: FFmpeg audio extraction should complete in less than 2.0 seconds for a 30-second clip.
* **Transcription RTF**: Whisper transcription realtime factor should be less than 0.5 (e.g. less than 15s to transcribe a 30s audio clip).
* **Alignment Latency**: Timeline alignment processing should take less than 5.0 milliseconds.
* **Synthesis RTF**: Voice synthesis realtime factor should be less than 0.3.

---

## 10. Release Readiness Checklist

- [ ] All 45 unit tests pass cleanly.
- [ ] No compilation errors or warnings.
- [ ] Subprocess tools (FFmpeg, FFprobe, yt-dlp) are available in the system path.
- [ ] Provider registry is populated with active providers.
- [ ] Test plan manual verification steps are completed successfully.
