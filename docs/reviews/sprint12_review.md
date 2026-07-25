# AutoShort Studio - Sprint 12 Real Input Support Review

This document provides a comprehensive review of the Real Input Support features developed during Sprint 12.

---

## 1. Executive Summary

Sprint 12 extends AutoShort Studio to support real-world video inputs. The pipeline can now accept any arbitrary local video path selected by the user or download online streams using a YouTube URL.

To manage multiple runs and keep assets isolated, each execution automatically creates a new timestamped project folder (e.g. `projects/project_20260710_144022/`). All intermediate files and final deliverables (`voice.wav`, `subtitle.srt`, `final.mp4`, `report.json`, `execution.log`) are saved directly inside this project directory, leaving the workspace root clean.

To protect the pipeline from crashes, we implemented a safeguard check: the pipeline verifies the presence of the `yt-dlp` command-line executable using `shutil.which`. If missing, it raises a clean, user-friendly `RuntimeError` rather than crashing with standard imports errors, while local video import remains fully functional.

* **Primary Deliverables**: Timestamped project directories containing `voice.wav`, `subtitle.srt`, `final.mp4`, `report.json`, and `execution.log`.
* **Status**: `VERIFIED & READY`

---

## 2. File Statistics

### Files Modified:
* `backend/requirements.txt` (Added `yt-dlp` dependency)
* `backend/run_pipeline.py` (Added dynamic project scaffolding, input routing, guard checks, and project-isolated output storage)

### Files Added:
* `docs/reviews/sprint12_review.md` (This document)

---

## 3. Dynamic Architecture & Folder Tree

The directory tree of a compiled run is structured inside the generated project folder:

```
projects/
└── project_20260710_144022/      # Dynamically created timestamped project folder
    ├── audio/                    # Extracted raw WAV files
    ├── video/                    # Imported/downloaded input video
    ├── subtitle/                 # Alignment and translation SRT/JSON drafts
    ├── cache/                    # TTS and translation caches
    ├── final.mp4                 # Final playable translated output video
    ├── voice.wav                 # Translated synthesized voiceover track
    ├── voice.mp3                 # Translated synthesized voiceover track (MP3)
    ├── subtitle.srt              # Final translated SRT subtitle file
    ├── report.json               # Complete execution metrics and file manifest
    └── execution.log             # Consolidated execution logs
```

---

## 4. Verification & Testing

### 1. End-to-End Test Execution (Local Input)
Executed the pipeline with the following command:
```powershell
python -m backend.run_pipeline --input samples\english\sample_en.mp4 --source-language en --target-language es
```

**Results**:
The run completed successfully in **3.31 seconds** and created a new project directory at `projects/project_20260710_144022`. 

Output files generated inside the directory:
* **`voice.wav`**: `320,334` bytes (Mono, 16kHz PCM audio)
* **`subtitle.srt`**: `192` bytes (Valid SRT subtitles)
* **`final.mp4`**: `86,596` bytes (H.264 video with AAC audio, duration: 5.0 seconds)
* **`report.json`**: Lists absolute outputs paths pointing inside the project folder
* **`execution.log`**: Standard execution logs, isolated to this run

### 2. Guard Check Verification (YouTube URL Routing)
If a YouTube URL is supplied (e.g. `https://www.youtube.com/watch?v=dQw4w9WgXcQ`), the pipeline checks for `yt-dlp` availability:
* If present on PATH: Downloads, imports, and processes the video.
* If missing from PATH: Gracefully stops and prompts:
  `yt-dlp is required to process YouTube URLs, but it was not found on your system PATH or virtual environment...`

### 3. Test Suite Regression Checks
* Executed the backend test suite:
  ```powershell
  python -m pytest backend/tests/
  ```
* **Result**: `45 passed` (No regressions detected).

---

## 5. Limitations & Future Scope

* **yt-dlp Executable Requirement**: While the Python wrapper is installed in requirements, downloading YouTube clips relies on the command-line program `yt-dlp` being runnable. If it cannot be resolved, only local imports are processed.
* **Storage Accumulation**: Since every execution creates a unique folder under `projects/`, users with multiple runs will see storage accumulate. A future cleanup policy or option to remove temporary intermediate directories should be considered.
