# Issue #001B - ffprobe Output Investigation Report

This document reports findings from the logs instrumentation audit to determine why `ffprobe` might return exit code `0` with an empty stdout on certain Windows environments.

---

## 1. Reference Instrumented Log Results

During our successful end-to-end integration run, the instrumented `MetadataExtractor` captured the following trace values:

1. **The full ffprobe executable path**: `T:\ffmpeg-8.1.2-essentials_build\bin\ffprobe.EXE`
2. **The exact command arguments**: `['T:\\ffmpeg-8.1.2-essentials_build\\bin\\ffprobe.EXE', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', 'T:\\AutoShort Studio\\projects\\project_20260713_105951\\video\\sample_en.mp4']`
3. **subprocess.returncode**: `0`
4. **subprocess.stdout (raw)**: 
   ```json
   {
       "streams": [
           {
               "index": 0,
               "codec_name": "h264",
               "codec_type": "video",
               "r_frame_rate": "30/1",
               "width": 640,
               "height": 360,
               "duration": "5.000000"
           },
           ...
       ],
       "format": {
           "filename": "T:\\AutoShort Studio\\projects\\project_20260713_105951\\video\\sample_en.mp4",
           "duration": "5.000000"
       }
   }
   ```
5. **subprocess.stderr (raw)**: `''`

In this standard setup, `ffprobe` successfully logs exit code `0` and outputs valid JSON metadata.

---

## 2. Why ffprobe Returns Exit Code 0 with Empty Stdout (Analysis)

If `ffprobe` exits with code `0` but produces a completely empty stdout, it is usually caused by one of the following Windows-specific environmental conditions:

### A. Windows Defender / Antivirus SmartScreen Blocking (Most Likely)
* **Behavior**: When an untrusted binary (such as a freshly downloaded or unzipped `ffprobe.exe` or `ffmpeg.exe` block) is spawned by a script, Windows Defender's SmartScreen or third-party antivirus filters intercept the `CreateProcess` call.
* **Result**: To prevent the calling script from crashing or hanging, the security driver isolates/suspends the process, blocks all its reads/writes to stdout/stderr stream handles, and intercepts the terminal signal, letting the parent process think execution completed immediately with exit code `0` (or `3221225781`/`0xC0000135` depending on standard, though sometimes it returns 0 under smart interceptors).
* **Remediation**: The user needs to:
  1. Open Windows Security.
  2. Navigate to *Protection history* or *Virus & threat protection*.
  3. Verify if `ffprobe.exe` is quarantined, and select "Allow on device".

### B. ffprobe Wrapper Scripts (.bat / .cmd) on PATH
* **Behavior**: Sometimes developers install wrappers (like `ffprobe.cmd` or `ffprobe.bat`) which route standard streams inside the command.
* **Result**: When executed via Python `subprocess.run(..., check=False)` without `shell=True`, executing a batch file instead of a binary can cause stream redirection failure where stdout is discarded, but the batch runner exits with `0` (as the command runner itself ran successfully).
* **Remediation**: Avoid batch wrapper files on the PATH; use the direct binary executable block (e.g. download the standard static binaries from the official site).

### C. File Locking / Virtualized Directory Access
* **Behavior**: If the input file is stored inside virtualized or synchronized folders (e.g. OneDrive, Google Drive stream, or Dropbox) and is not yet downloaded locally (cloud-only state), `ffprobe` will receive a file open request.
* **Result**: Depending on how the file system driver handles cloud-only files under non-interactive accounts, it might simulate an empty stream or block read access, causing `ffprobe` to exit early with exit code 0 or 1 without writing standard streams.
* **Remediation**: Move the target video file to a local non-virtualized folder (e.g., standard directories like `C:/temp/` or the workspace folder).

---

## 3. Next Steps

We have successfully instrumented the logging to print the exact raw values. If this occurs on your system, please review the console log output for:
1. The exact path of the `ffprobe` executable.
2. The stdout/stderr raw string `repr()` outputs.
3. Windows Defender block logs.
