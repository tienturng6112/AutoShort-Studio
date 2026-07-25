from typing import Callable, Optional

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

from backend.speech.base_speech_provider import BaseSpeechProvider
from backend.speech.cancellation import CancellationToken
from backend.speech.models import Transcript, Segment, Word

class FasterWhisperProvider(BaseSpeechProvider):
    """Speech-to-text adapter implementing faster-whisper for transcription and word alignments."""

    async def transcribe(
        self, 
        audio_path: str, 
        model_path: str, 
        device: str, 
        progress_callback: Optional[Callable[[float], None]] = None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> Transcript:
        if WhisperModel is None:
            raise ImportError(
                "Speech recognition error: The 'faster_whisper' package is not installed "
                "in this Python environment. Please install it to use this provider."
            )

        # Determine compute precision targeting device
        compute_type = "float16" if device == "cuda" else "int8"
        
        # Load local Whisper model weights
        model = WhisperModel(model_path, device=device, compute_type=compute_type)
        
        # Run transcription with beam size 5 and word alignments enabled
        segments_generator, info = model.transcribe(audio_path, beam_size=5, word_timestamps=True)
        
        total_duration = info.duration
        segments_list = []
        text_parts = []
        
        for idx, seg in enumerate(segments_generator):
            if cancellation_token:
                cancellation_token.raise_if_cancelled()
                
            words_list = []
            if seg.words:
                for w in seg.words:
                    words_list.append(Word(
                        word=w.word,
                        start=w.start,
                        end=w.end,
                        probability=w.probability
                    ))
            
            segment_obj = Segment(
                id=idx,
                start=seg.start,
                end=seg.end,
                text=seg.text,
                words=words_list,
                confidence=seg.avg_logprob
            )
            
            segments_list.append(segment_obj)
            text_parts.append(seg.text)
            
            if progress_callback and total_duration > 0:
                progress = min((seg.end / total_duration) * 100.0, 100.0)
                progress_callback(progress)
                
        if progress_callback:
            progress_callback(100.0)
            
        return Transcript(
            text=" ".join(text_parts).strip(),
            language=info.language,
            language_probability=info.language_probability,
            duration=total_duration,
            segments=segments_list
        )
