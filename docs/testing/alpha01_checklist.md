# Alpha 0.1 Readiness Checklist

This document tracks verification steps and checklist items required to validate the Alpha 0.1 pipeline.

---

## 1. Environment & Setup

- [ ] `ffmpeg` is installed and accessible via system PATH.
- [ ] `ffprobe` is installed and accessible via system PATH.
- [ ] Python dependencies (`faster-whisper`, `edge-tts`, `openai`, `pydantic`) are installed in the local virtual environment.
- [ ] Test sample directory `samples/` exists with folders `english/`, `japanese/`, `podcast/`, `shorts/`, and `music/`.
- [ ] A sample video is placed in `samples/english/` for E2E runs.

---

## 2. Component Verification

- [ ] **Import Engine**: Local files can be copied; youtube downloads via `yt-dlp` work.
- [ ] **Speech Engine**: Local Whisper models can download, load, and transcribe audio to timed segments.
- [ ] **Translation Engine**: LLM translation calls preserve segment boundaries, confidence, and structure.
- [ ] **Timeline Alignment**: Splitting long lines, merging short adjacent items, and overlap timings resolution work cleanly.
- [ ] **Voice Synthesis**: EdgeTTS synthesizes clips, silence gaps are inserted, and audio is merged and loudness-normalized to EBU R128 guidelines.

---

## 3. End-to-End Execution Checklist

- [ ] Project workspace directories are scaffolded correctly.
- [ ] Extracted audio `audio.wav` is verified as PCM, 16kHz, mono format.
- [ ] Final synthesized voice track is exported to both `voice.wav` and `voice.mp3`.
- [ ] Validation errors are checked, and outputs contain no overlaps or negative durations.
- [ ] Acceptance execution report is generated containing telemetry and latency benchmarks.
