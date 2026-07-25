# Voice ID vs Display Name Inspection Report (Issue #013)

This report presents the inspection of the Speaker Voices combobox, settings persistence format, and the root cause of the backend validation error.

No code modifications have been made.

---

## 1. Inspection of Speaker Voices Combobox Stored Value

### 1.1 Storage Format (Display vs. Stored Value)
In `desktop_app.py`, items are added to each speaker's QComboBox using:
```python
combo.addItem(friendly, name)
```
- **Display Name (first argument)**: The user-friendly display string returned by `get_friendly_name` (e.g. `"Nam Minh (Male)"`).
- **Stored Value (second argument / UserData)**: The technical name variable `name` retrieved from the list of available voices.

### 1.2 Settings Persistence
In `save_settings`, the combobox value is read using `combo.currentData()`, which returns the stored UserData (the technical name), not the display text. 

Therefore:
- The UI displays friendly names.
- `settings.json` is configured to persist only the technical/canonical identifiers, keeping the display names separated.

---

## 2. Root Cause of the Observed Error

### 2.1 The Issue
The backend validation failed with the error:
```text
Got: Microsoft Server Speech Text to Speech Voice (vi-VN, NamMinhNeural)
```
This long descriptive display string was persisted into `settings.json` instead of the canonical `vi-VN-NamMinhNeural` ID.

### 2.2 Root Cause Analysis
In [edge_tts_provider.py](file:///t:/AutoShort%20Studio/backend/tts/edge_tts_provider.py), the `list_voices` method queries the Microsoft edge-tts voices list and maps properties as follows:
```python
        for voice in manager.voices:
            results.append({
                "name": voice.get("Name", ""),
                "gender": voice.get("Gender", "Unknown"),
                "language": voice.get("Locale", "Unknown"),
                "provider": "edge-tts"
            })
```
- Microsoft's API returns two keys:
  - `"Name"`: The full descriptive display name, e.g., `"Microsoft Server Speech Text to Speech Voice (vi-VN, NamMinhNeural)"`.
  - `"ShortName"`: The canonical identifier used by `edge-tts` communicate client, e.g., `"vi-VN-NamMinhNeural"`.
- Because the code maps `"name"` to `voice.get("Name", "")`, the full descriptive string is saved as the UserData in the UI comboboxes and persisted to `settings.json`.

---

## 3. Recommended Resolution

Modify `backend/tts/edge_tts_provider.py` to extract `"ShortName"` instead of `"Name"` for the voice identifier:

```diff
         for voice in manager.voices:
             results.append({
-                "name": voice.get("Name", ""),
+                "name": voice.get("ShortName", ""),
                 "gender": voice.get("Gender", "Unknown"),
                 "language": voice.get("Locale", "Unknown"),
                 "provider": "edge-tts"
```
This maps only the canonical Edge voice ID (e.g. `vi-VN-NamMinhNeural`) as the stored value, keeping display strings out of `settings.json` and the synthesis backend.
