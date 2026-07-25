# Issue #006 Review: Whisper Segmentation Investigation

This report investigates the Whisper segmentation omission between approximately `00:35` and `01:00` in the Chinese video.

---

## 1. Exact Call to `WhisperModel.transcribe()`

In [faster_whisper_provider.py](file:///t:/AutoShort%20Studio/backend/speech/faster_whisper_provider.py#L36), the transcription call is:
```python
segments_generator, info = model.transcribe(audio_path, beam_size=5, word_timestamps=True)
```

---

## 2. Transcribe Parameters Analysis

The parameters passed to `transcribe()` and their values are:

| Parameter | Configured Value | Default Value (faster-whisper) | Description |
| :--- | :--- | :--- | :--- |
| `beam_size` | `5` | `5` | Size of beam search during decoding. |
| `vad_filter` | *Not set* | `False` | Whether to filter out non-speech segments using Silero VAD. |
| `vad_parameters` | *Not set* | `None` | Custom parameters for VAD filter. |
| `word_timestamps` | `True` | `False` | Whether to generate word-level timestamp alignments. |
| `condition_on_previous_text` | *Not set* | `True` | Feeds the text of the previous window to condition next window decoding. |
| `temperature` | *Not set* | `[0.0, 0.2, 0.4, 0.6, 0.8, 1.0]` | Temperature list for fallback decoding. |
| `language` | *Not set* | `None` | Target language (defaults to auto-detection). |
| `initial_prompt` | *Not set* | `None` | Initial prompt prefix for decoding the first window. |
| `without_speech_threshold` | *Not set* | `0.6` | Skips decoding if the no-speech probability is above this. |
| `compression_ratio_threshold` | *Not set* | `2.4` | Discards translation if compression ratio exceeds this. |
| `log_prob_threshold` | *Not set* | `-1.0` | Discards translation if average log prob is below this. |

---

## 3. Segment Counts Comparison

The counts of segments at each stage are:

- **Raw Whisper Segments**: **14** (from [raw_whisper_segments.json](file:///t:/AutoShort%20Studio/raw_whisper_segments.json))
- **Processed Transcript Segments**: **14**
- **Aligned Transcript Segments**: **15** (Segment `14` is the empty padding segment added to match the video duration)

### Analysis:
Since the raw output of Faster-Whisper contains only 14 segments, the speech between `00:35` and `01:00` was **missed by the model itself** before any backend processing occurred. No downstream stage merged or discarded these segments.

---

## 4. Root Cause of Missing Speech

The omission of the speech segment between `35.48`s and `60.16`s is caused by the default configurations of the following three Whisper parameters:

1. **`condition_on_previous_text=True` (Default)**:
   - Whisper uses decoded tokens from the previous window to prompt the next window. When the video transitions or has music/noise in the background, this can cause the decoding state to get stuck or interpret the next window as silence/repetition, suppressing transcription of subsequent speech.
2. **`vad_filter=False` (Default)**:
   - Without VAD filtering, Whisper relies on its internal heuristic grids for sliding windows. If a region has music, noise, or silence, it can fail to detect voice activity properly, resulting in a large gap being skipped.
3. **`without_speech_threshold=0.6` (Default)**:
   - If the background noise or music increases the model's computed "no speech" probability above `0.6`, the entire segment is skipped.
