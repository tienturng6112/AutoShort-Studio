# AutoShort Studio - Development Roadmap

This document outlines the roadmap and milestones for the upcoming development cycles of AutoShort Studio.

---

## Completed Milestones

* **Sprint 1 - 4**: Scaffolding project core structures, logging system, SQLite database migrations, and `ChatAnywhereProvider` LLM adapters.
* **Sprint 5**: LLM Service, cost calculations, tiktoken token tracking, conversation turn management, and YAML prompt templates.
* **Sprint 6**: Video Import Engine, local file copying, `yt-dlp` YouTube downloads, `ffprobe` metadata queries, and `ffmpeg` audio wav conversions.
* **Sprint 7**: Speech Recognition, `faster-whisper` local integrations, word boundary timestamps, cancellation tokens, and progress callbacks.
* **Sprint 8**: Translation Engine, glossary brand mappings, segment checkpoints, and translation caching.
* **Sprint 9**: Timeline Alignment, CPL segment splitting, neighboring short merging, overlap optimizations, and silence pause inserts.
* **Sprint 10**: Voice Synthesis, MS Edge TTS public integrations, gap silence merges, and EBU R128 loudness normalizations.

---

## Future Milestones

### Sprint 11: Workflow Engine Orchestrator
- Define execution DAG (Directed Acyclic Graph) engine nodes.
- Orchestrate sequential workflow runs (Import -> Transcribe -> Translate -> Align -> Synthesize -> Render).
- Event bus state triggers and execution error recoveries.

### Sprint 12: Subtitles timings & styling
- Word alignments timing to SRT/ASS conversions.
- Custom styled ASS subtitle templates support (font sizes, stroke outline borders, active highlight colors, vertical margins).

### Sprint 13: Render Engine
- MoviePy timeline compositing.
- Layer compositions (video track, audio voice track, background music track, ASS overlay subtitles track).
- Hardware-accelerated H.264 video rendering and audio mixing.

### Sprint 14: API Presentation Layer
- FastAPI REST endpoint integrations.
- SSE (Server-Sent Events) execution progress streams.
- Local storage downloads and workspace management.

### Sprint 15: Frontend Interface
- Modern Next.js dashboard UI.
- Interactive timeline editors, preview players, logs views, and project configuration panels.
