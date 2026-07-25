# Pronoun Resolution Analysis Report (Issue #014)

This report details the inspection of segment pronoun mapping, context resolution, and the root cause of translation errors.

No code modifications have been made.

---

## 1. Subtitle Segment Export Sequence

The target segment is **Segment 3** in the subtitle files of the latest project folder (`projects/project_20260715_163222`). Here is the timeline sequence spanning the target segment, its previous 2 segments, and next 2 segments:

| Segment ID | Speaker ID | Timing | Original Chinese | Translated Vietnamese |
| :---: | :---: | :---: | :--- | :--- |
| **1** | `Speaker_B` | `6.86s` - `8.64s` | `'妈一定会想法子的'` | `'Mẹ nhất định sẽ tìm cách giúp thôi.'` |
| **2** | `Speaker_A` | `10.38s` - `11.64s` | `'我只能做到个大载'` | `'Con chỉ có thể làm một cái chỗ lớn thôi.'` |
| **3 (Target)** | `Speaker_A` | `12.26s` - `13.86s` | `'剩下个我也拇某办法了'` | `'Phần còn lại con cũng không biết làm sao nữa.'` |
| **4** | `Speaker_B` | `14.96s` - `16.54s` | `'好,考也好'` | `'Được rồi, thi cũng được.'` |
| **5** | `Speaker_B` | `17.84s` - `19.08s` | `'某事儿交博物'` | `'Có việc gì thì cứ nói với bọn con.'` |

---

## 2. Chinese Source Relationship Analysis

- **Ambiguity of Segment 3**: The Chinese source text of Segment 3 (`'剩下个我也拇某办法了'`) contains only `我` ("I") and dialectal slang for "no way" (`拇某办法` ➔ `无办法`). In isolation, this segment is **completely ambiguous** and does not declare any family relationship.
- **Contextual Clarity**: However, Segment 1 explicitly contains `'妈'` ("Mom" / "Mother"), and Segment 0 contains `妈 我考上人大了` ("Mom, I got into Renmin University"). From these surrounding segments in the dialogue sequence, the mother-son/daughter relationship is clearly established.

---

## 3. Exact Prompt Sent to ChatAnywhere

### 3.1 System Instruction Prompt
```text
You are a professional Chinese → Vietnamese movie subtitle translator.
Requirements:
- Translate naturally using Vietnamese conversational style (prefer natural spoken Vietnamese).
- Preserve original meaning and emotional tone.
- Preserve humor and sarcasm.
- Never summarize.
- Keep subtitle timing unchanged.
- Preserve names (never translate proper names into pronouns).
- Never use literal Chinese sentence structure.
- Return JSON only.

Relationship Rules for Vietnamese pronoun selection:
- Infer relationships from previous subtitles.
- Keep the same pronouns throughout the movie.
- If uncertain, omit pronouns rather than guessing.
- If speaking to parents: use 'mẹ' / 'ba' / 'con'.
- If an older person speaks to a younger person: use 'con' for the younger person.
- If a younger person speaks to an elder: use 'cháu' / 'con'.
- If friends: use 'tớ' / 'cậu'.
- If husband and wife: use 'anh' / 'em'.
- If the relationship is unknown: avoid the literal pronoun 'bạn' and omit pronouns rather than guessing.

You MUST preserve the input segment IDs exactly. Keep the JSON structure identical. Translate ONLY the 'text' property value.
Format the output as a valid, raw JSON list matching the input structure, with no extra conversational formatting.
```

### 3.2 User Prompt Payload
```json
[
  {"id": 1, "text": "妈一定会想法子的"},
  {"id": 2, "text": "我只能做到个大载"},
  {"id": 3, "text": "剩下个我也拇某办法了"},
  {"id": 4, "text": "好,考也好"},
  {"id": 5, "text": "某事儿交博物"}
]
```

---

## 4. Root Cause of Incorrect Pronoun Selection

The incorrect pronoun selection (e.g. Segment 5 translating `'某事儿交博物'` into `"Có việc gì thì cứ nói với bọn con"` using `"bọn con"` / "us children") is caused by **insufficient context** in the prompt design.

* **Context Stripping in translation Service**: Even though the Speaker Diarization stage successfully maps segments to `Speaker_A` and `Speaker_B` inside `transcript.json`, [translation_service.py:L75](file:///t:/AutoShort%20Studio/backend/translation/translation_service.py#L75) strips out this metadata before sending the payload to the LLM:
  ```python
  payload = [{"id": item["id"], "text": item["text"]} for item in to_translate]
  ```
* **Consequence**: The LLM receives only a list of segment IDs and text strings without any speaker identification. It is forced to guess speaker boundaries and conversational turns blindly, causing pronoun mismatches (like a mother saying `"bọn con"` to her child) because it cannot differentiate which speaker is talking.
