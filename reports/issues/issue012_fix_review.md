# Voice Preview Fix Report (Issue #012)

This report confirms the resolution of the voice preview issues in the Settings Dialog.

---

## 1. Implemented Fixes

1. **Selected Target Language Mapping**:
   - Preview text is resolved strictly based on the selected Target Language.
   - Text is set to `"Xin chào, đây là giọng mẫu."` if language is `"vi"`.
   - Text is set to `"Hello, this is a sample voice."` for other target languages.
   - Removed all voice name prefix parsing logic.

2. **Playback Stopping & Source Release**:
   - In `on_preview_finished`, calls `self.player.stop()` and resets the source `self.player.setSource(QUrl())` before writing the newly synthesized bytes to disk. This successfully releases locks on the file system.

3. **Unique Preview File Name Generator**:
   - Integrated Python's `uuid` module to generate a unique filename for each preview request: `temp_preview_<uuid_hex>.mp3`.

4. **Auto-cleanup**:
   - Clears out all old preview MP3 assets in `projects/temp_preview/` before creating a new preview file.

---

## 2. Verification Details

- **Hoài My Preview**: Correctly resolves to the Vietnamese sample sentence and outputs the Vietnamese female neural voice.
- **Nam Minh Preview**: Correctly resolves to the Vietnamese sample sentence and outputs the Vietnamese male neural voice.
- **File System verification**: Checked `projects/temp_preview/` and confirmed that only the actively playing preview file exists, with all previous preview requests automatically cleaned.
- **Stability**: Standard pytest run succeeded.
