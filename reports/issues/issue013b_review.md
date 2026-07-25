# Settings Persistence Bug Investigation (Issue #013B)

This report traces the save pipeline when clicking **Save Settings** and inspects the combobox values and properties.

No code modifications have been made.

---

## 1. Save Path Trace

When the user clicks the **Save Settings** button:
1. It triggers `self.save_settings()` in [desktop_app.py:L469](file:///t:/AutoShort%20Studio/desktop_app.py#L469).
2. The method constructs the `speaker_voices` dict by looping over `self.speaker_combos` in [desktop_app.py:L485-489](file:///t:/AutoShort%20Studio/desktop_app.py#L485-489):
   ```python
           speaker_voices = {}
           for spk, combo in self.speaker_combos.items():
               val = combo.currentData()
               if val:
                   speaker_voices[spk] = val
   ```
3. The dict is assigned to `data["speaker_voices"]` in [desktop_app.py:L494](file:///t:/AutoShort%20Studio/desktop_app.py#L494):
   ```python
           data = {
               "translation_provider": provider,
               "speech_enhancement": "demucs" if self.enhance_combo.currentIndex() == 1 else "off",
               "speaker_voices": speaker_voices,
               ...
   ```
4. The dictionary `data` is written to `config/settings.json` in [desktop_app.py:L507-509](file:///t:/AutoShort%20Studio/desktop_app.py#L507-509):
   ```python
               with open(settings_path, "w", encoding="utf-8") as f:
                   json.dump(data, f, indent=4)
   ```

---

## 2. Values Returned for Speaker_A

When Speaker_A is configured with the first Vietnamese voice:
- **`combo.currentText()`** returns the friendly text: `"Hoài My (Female)"`.
- **`combo.currentData()`** returns the UserData: `"Microsoft Server Speech Text to Speech Voice (vi-VN, HoaiMyNeural)"`.

---

## 3. Combobox UserData Mapping Verification

The combobox UserData still contains Microsoft's long **`Name`** property instead of the canonical **`ShortName`**. 

This happens because the voice list loaded in [desktop_app.py:L231](file:///t:/AutoShort%20Studio/desktop_app.py#L231) is queried from `provider.list_voices()`, which maps `"name"` to `Name` on [edge_tts_provider.py:L27](file:///t:/AutoShort%20Studio/backend/tts/edge_tts_provider.py#L27):

```python
        for voice in manager.voices:
            results.append({
                "name": voice.get("Name", ""),  # <--- Exact line returning long display name
                "gender": voice.get("Gender", "Unknown"),
                "language": voice.get("Locale", "Unknown"),
                "provider": "edge-tts"
            })
```

### Conclusion
- The Save Settings logic is correct and correctly retrieves the UserData (`combo.currentData()`).
- However, because the underlying list of voices in the provider maps the `"name"` key to the full long `Name` string instead of `ShortName`, the combobox UserData is populated with the wrong value.
- To fix the issue, the provider code must be updated to retrieve `ShortName`.
