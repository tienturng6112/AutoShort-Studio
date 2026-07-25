# Issue #001 - Pipeline Stability Review

This document reports the resolution of the pipeline stability issues related to `ffprobe` execution and metadata parsing audits.

---

## 1. Executive Summary

We performed an audit on the metadata extraction system to make it robust against toolchain omissions and system execution errors.

* **Deliverables**:
  - Modified [metadata_extractor.py](file:///t:/AutoShort%20Studio/backend/media/metadata_extractor.py) with advanced validation checks, logs capture, and failure routing.
  - Modified [desktop_app.py](file:///t:/AutoShort%20Studio/desktop_app.py) to present user-friendly error messages from `report.json` in the GUI banner instead of a raw traceback.
  - New test file [test_metadata_extractor.py](file:///t:/AutoShort%20Studio/backend/tests/test_metadata_extractor.py) testing valid videos, missing ffprobe, invalid videos, and empty stdout.
* **Status**: `RESOLVED & GREEN`
  - The pipeline correctly audits, executes, parses, and logs the `ffprobe` subprocess streams without structural crashes.
  - The PySide6 UI cleanly extracts and displays errors.
  - Unit tests have completed successfully (4/4 passed).

---

## 2. Implemented Stability Checks

Inside `backend/media/metadata_extractor.py`, we added the following checks:

1. **shutil PATH Audit**: Before launching `subprocess.run`, the class audits the environment using `shutil.which("ffprobe")`. If missing, it immediately throws a clear `RuntimeError` describing that `"FFmpeg / ffprobe is not installed or not found."`
2. **Path & Command Logging**: Added logging statement for the resolved `ffprobe` executable path and the exact parameters array being executed.
3. **Execution Exit Code Auditing**: Set `check=False` to handle failures manually, logging the precise exit code and stderr values if non-zero.
4. **Stdout & Stderr Logger Hooks**: Both output streams are printed to the logger under INFO and WARNING respectively.
5. **JSON Null-Safety**: Added guard checks preventing parsing of empty or null stdout strings (`json.loads(None)`).

---

## 3. UI Error Presentation

Inside `desktop_app.py`'s `pipeline_finished` slot, when the exit code is non-zero (indicating failure):
- The app scans the `projects/` directory for the latest generated run folder.
- It attempts to parse `report.json`. If it detects `"status": "failed"` and a corresponding `"error"` message, it extracts that string and presents it cleanly in the red error banner (e.g., `Error: FFmpeg / ffprobe is not installed or not found.`) rather than leaving the user to inspect Python tracebacks in the text logs.

---

## 4. Verification

### Unit Tests
We executed the unit tests inside the virtual environment:
```powershell
backend/venv/Scripts/python -m pytest backend/tests/test_metadata_extractor.py
```
**Results**:
```text
collected 4 items

backend\tests\test_metadata_extractor.py ....                            [100%]

============================== 4 passed in 0.10s ==============================
```

### Integration Test Logs
An E2E verification run logged:
* `Using ffprobe executable: T:\ffmpeg-8.1.2-essentials_build\bin\ffprobe.exe`
* `Executing command: ['T:\\ffmpeg-8.1.2-essentials_build\\bin\\ffprobe.exe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', 'T:\\AutoShort Studio\\projects\\project_20260711_120354\\video\\sample_en.mp4']`
* `ffprobe exit code: 0`
* Container parameters resolved successfully and pipeline finished green.
