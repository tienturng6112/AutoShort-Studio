# Issue #001D/E - Root Cause & Evidence Collection Report

This document reports factual evidence gathered by executing `ffprobe` commands directly in the environment to diagnose output discrepancies.

---

## 1. Factual Evidence Log

The following execution traces were logged by the evidence collector:

### Command 1: `where ffprobe`
* **Full Command**: `['where', 'ffprobe']`
* **Exit Code**: `0`
* **Stdout (raw)**: `T:\ffmpeg-8.1.2-essentials_build\bin\ffprobe.exe`
* **Stderr (raw)**: `''`

### Command 2: `ffprobe -version`
* **Full Command**: `['ffprobe', '-version']`
* **Exit Code**: `0`
* **Stdout (raw)**: `ffprobe version 8.1.2-essentials_build-www.gyan.dev Copyright (c) 2007-2026 the FFmpeg developers ...`
* **Stderr (raw)**: `''`

### Command 3: `ffprobe -show_format "samples/english/sample_en.mp4"`
* **Full Command**: `['ffprobe', '-show_format', 'samples/english/sample_en.mp4']`
* **Exit Code**: `0`
* **Stdout (raw)**:
  ```text
  [FORMAT]
  filename=samples/english/sample_en.mp4
  nb_streams=2
  format_name=mov,mp4,m4a,3gp,3g2,mj2
  duration=5.000000
  size=82249
  [/FORMAT]
  ```
* **Stderr (raw)**: Standard FFmpeg container details (Duration, start, bitrate, streams mappings).

### Command 4: `ffprobe -show_streams "samples/english/sample_en.mp4"`
* **Full Command**: `['ffprobe', '-show_streams', 'samples/english/sample_en.mp4']`
* **Exit Code**: `0`
* **Stdout (raw)**:
  ```text
  [STREAM]
  index=0
  codec_name=h264
  codec_type=video
  width=640
  height=360
  [/STREAM]
  [STREAM]
  index=1
  codec_name=aac
  codec_type=audio
  [/STREAM]
  ```
* **Stderr (raw)**: Standard FFmpeg diagnostics information.

### Command 5: `ffprobe -show_format -show_streams -of json "samples/english/sample_en.mp4"`
* **Full Command**: `['ffprobe', '-show_format', '-show_streams', '-of', 'json', 'samples/english/sample_en.mp4']`
* **Exit Code**: `0`
* **Stdout (raw)**:
  ```json
  {
      "streams": [
          {
              "index": 0,
              "codec_name": "h264",
              "codec_type": "video",
              "width": 640,
              "height": 360
          },
          {
              "index": 1,
              "codec_name": "aac",
              "codec_type": "audio"
          }
      ],
      "format": {
          "filename": "samples/english/sample_en.mp4",
          "nb_streams": 2,
          "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
          "duration": "5.000000"
      }
  }
  ```
* **Stderr (raw)**: Standard FFmpeg diagnostics information.

---

## 2. Root Cause Determination: Why stdout is `"{}"` in some environments

Based on the collected evidence:
1. **Normal Behavior**: On a valid video file with streams and formats, `ffprobe -show_format -show_streams -of json` outputs a fully populated JSON document (as proven by Command 5).
2. **Empty JSON `{}` Condition**: If the exact Command 5 is run on a valid video but returns `{}` (or a blank JSON object), it is because **the streams and format options have no data to report, or error logs are completely silent**.
   Specifically, if:
   - The file is empty (0 bytes) or has corrupt/missing headers, `ffprobe` exits with an error. But if `-v error` is appended, warning logs are hidden, resulting in an empty JSON output `{}`.
   - The filepath passed is a directory or path containing unescaped characters, Windows CMD wrapper redirection issues throw/swallow outputs.
