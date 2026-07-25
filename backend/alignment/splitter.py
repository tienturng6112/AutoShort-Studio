from typing import List
from backend.speech.models import Segment, Word

class SegmentSplitter:
    """Splits long segments to respect maximum characters per line (CPL) constraints."""

    def __init__(self, max_cpl: int = 40) -> None:
        self._max_cpl = max_cpl

    def split_segment(self, segment: Segment) -> List[Segment]:
        """Splits a single long Segment into multiple smaller Segments.
        
        Args:
            segment (Segment): Long segment to split.
            
        Returns:
            List[Segment]: Sub-segments list, splitting on word boundaries.
        """
        if len(segment.text.strip()) <= self._max_cpl:
            return [segment]

        # Case 1: Word-level alignments are available
        # Prevent reconstruction bugs if segment was translated (e.g. Latin text but Chinese words)
        has_chinese_words = segment.words and any('\u4e00' <= char <= '\u9fff' for w in segment.words for char in w.word)
        has_latin_text = any('a' <= char.lower() <= 'z' for char in segment.text)
        is_translated = has_latin_text and has_chinese_words

        if segment.words and not is_translated:
            sub_segments = []
            current_words: List[Word] = []
            current_len = 0
            
            for w in segment.words:
                word_len = len(w.word) + 1  # include space char
                if current_words and (current_len + word_len > self._max_cpl):
                    sub_text = " ".join(item.word for item in current_words)
                    sub_segments.append(Segment(
                        id=segment.id,
                        start=current_words[0].start,
                        end=current_words[-1].end,
                        text=sub_text,
                        words=current_words,
                        confidence=segment.confidence,
                        speaker_id=segment.speaker_id,
                        speaker_gender=segment.speaker_gender,
                        voice=segment.voice,
                        emotion=segment.emotion,
                        metadata=segment.metadata.copy() if segment.metadata else {}
                    ))
                    current_words = [w]
                    current_len = word_len
                else:
                    current_words.append(w)
                    current_len += word_len

            if current_words:
                sub_text = " ".join(item.word for item in current_words)
                sub_segments.append(Segment(
                    id=segment.id,
                    start=current_words[0].start,
                    end=current_words[-1].end,
                    text=sub_text,
                    words=current_words,
                    confidence=segment.confidence,
                    speaker_id=segment.speaker_id,
                    speaker_gender=segment.speaker_gender,
                    voice=segment.voice,
                    emotion=segment.emotion,
                    metadata=segment.metadata.copy() if segment.metadata else {}
                ))
            return sub_segments

        # Case 2: No word alignments, split text using character length ratios
        words = segment.text.strip().split()
        sub_segments = []
        current_words_str: List[str] = []
        current_len = 0
        
        total_chars = sum(len(w) for w in words)
        duration = max(segment.end - segment.start, 0.0)
        running_start = segment.start

        for w in words:
            word_len = len(w) + 1
            if current_words_str and (current_len + word_len > self._max_cpl):
                sub_text = " ".join(current_words_str)
                chars_count = sum(len(x) for x in current_words_str)
                sub_dur = (chars_count / total_chars) * duration if total_chars > 0 else 0.0
                
                sub_segments.append(Segment(
                    id=segment.id,
                    start=running_start,
                    end=running_start + sub_dur,
                    text=sub_text,
                    words=[],
                    confidence=segment.confidence,
                    speaker_id=segment.speaker_id,
                    speaker_gender=segment.speaker_gender,
                    voice=segment.voice,
                    emotion=segment.emotion,
                    metadata=segment.metadata.copy() if segment.metadata else {}
                ))
                running_start += sub_dur
                current_words_str = [w]
                current_len = word_len
            else:
                current_words_str.append(w)
                current_len += word_len

        if current_words_str:
            sub_text = " ".join(current_words_str)
            sub_segments.append(Segment(
                id=segment.id,
                start=running_start,
                end=segment.end,
                text=sub_text,
                words=[],
                confidence=segment.confidence,
                speaker_id=segment.speaker_id,
                speaker_gender=segment.speaker_gender,
                voice=segment.voice,
                emotion=segment.emotion,
                metadata=segment.metadata.copy() if segment.metadata else {}
            ))
            
        return sub_segments
