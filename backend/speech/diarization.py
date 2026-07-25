import os
import time
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from backend.speech.models import Transcript

logger = logging.getLogger("Diarization")

class BaseDiarizationProvider(ABC):
    """Port interface for Speaker Diarization engines."""
    
    @abstractmethod
    def diarize(self, audio_path: str) -> List[Dict[str, Any]]:
        """Detects speaker turns in an audio file.
        
        Args:
            audio_path (str): Path to input WAV file.
            
        Returns:
            List[Dict[str, Any]]: Chronological list of speaker turns, e.g.:
                [{"start": 0.0, "end": 2.5, "speaker": "SPEAKER_00"}, ...]
        """
        pass


class PyannoteDiarizationProvider(BaseDiarizationProvider):
    """Speaker diarization engine utilizing Pyannote Audio pre-trained pipelines."""
    
    def __init__(self, hf_token: Optional[str] = None):
        self.hf_token = hf_token or os.environ.get("HF_TOKEN")
        
    def diarize(self, audio_path: str) -> List[Dict[str, Any]]:
        if not self.hf_token:
            raise ValueError("Hugging Face API token (HF_TOKEN) is required for pyannote.audio")
            
        from pyannote.audio import Pipeline
        import torch
        
        # Determine device
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading pyannote.audio pipeline on device: {device}")
        
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=self.hf_token
        )
        if pipeline is None:
            raise RuntimeError("Failed to load pyannote/speaker-diarization-3.1 model.")
            
        # Move pipeline to target device
        pipeline.to(torch.device(device))
        
        logger.info(f"Running pyannote diarization on: {audio_path}")
        annotation = pipeline(audio_path)
        
        turns = []
        for turn, _, speaker in annotation.itertracks(yield_label=True):
            turns.append({
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker
            })
        return turns


class MockDiarizationProvider(BaseDiarizationProvider):
    """Mock speaker diarizer that generates alternating 5-second speaker turns for offline verification."""
    
    def diarize(self, audio_path: str) -> List[Dict[str, Any]]:
        import wave
        duration = 30.0  # Default fallback duration
        
        if os.path.exists(audio_path):
            try:
                with wave.open(audio_path, 'rb') as wav_file:
                    frames = wav_file.getnframes()
                    rate = wav_file.getframerate()
                    duration = frames / float(rate)
            except Exception as e:
                logger.warning(f"Failed to read WAV duration: {str(e)}. Using default duration.")
                
        logger.info(f"Generating mock speaker turns for audio duration: {duration:.2f}s")
        turns = []
        step = 5.0
        current = 0.0
        speaker_idx = 0
        
        while current < duration:
            end = min(current + step, duration)
            turns.append({
                "start": current,
                "end": end,
                "speaker": f"SPEAKER_{speaker_idx:02d}"
            })
            current += step
            speaker_idx = 1 - speaker_idx  # Alternate between SPEAKER_00 and SPEAKER_01
            
        return turns


class DiarizationService:
    """Orchestrates speech diarization runs and aligns speaker timelines with subtitle segments."""
    
    def __init__(self, provider: BaseDiarizationProvider):
        self._provider = provider
        
    def diarize_transcript(self, transcript: Transcript, audio_path: str) -> Dict[str, Any]:
        """Runs diarization on audio, maps speaker turns to transcript segments, and outputs the speaker map.
        
        Args:
            transcript (Transcript): The in-memory transcript with segments.
            audio_path (str): Speech audio WAV path.
            
        Returns:
            Dict[str, Any]: Mapped speaker metadata dictionary.
        """
        # 1. Run diarizer provider to extract raw speaker turns
        logger.info("Executing speaker diarization provider...")
        turns = self._provider.diarize(audio_path)
        
        # 2. Extract unique speakers in order of appearance
        unique_speakers = []
        for turn in turns:
            spk = turn["speaker"]
            if spk not in unique_speakers:
                unique_speakers.append(spk)
                
        # 3. Create mapping to friendly speaker IDs (Speaker_A, Speaker_B, etc.)
        speaker_mapping = {}
        for i, spk in enumerate(unique_speakers):
            letter = chr(65 + i) if i < 26 else f"Sub_{i-25}"
            speaker_mapping[spk] = f"Speaker_{letter}"
            
        logger.info(f"Mapped {len(speaker_mapping)} raw speaker label(s) to friendly ID(s): {speaker_mapping}")
        
        # 4. Map each subtitle segment to the speaker with the maximum timing overlap
        for seg in transcript.segments:
            best_speaker = None
            max_overlap = 0.0
            
            for turn in turns:
                overlap_start = max(seg.start, turn["start"])
                overlap_end = min(seg.end, turn["end"])
                overlap = max(0.0, overlap_end - overlap_start)
                
                if overlap > max_overlap:
                    max_overlap = overlap
                    best_speaker = turn["speaker"]
                    
            if best_speaker:
                seg.speaker_id = speaker_mapping[best_speaker]
            else:
                # If no speaker overlap is found (e.g. silence or pad segment), default to Speaker_A
                seg.speaker_id = "Speaker_A"
                
        # 5. Build output speaker_map metadata schema
        speaker_map = {}
        for spk, mapped_id in speaker_mapping.items():
            speaker_map[mapped_id] = {
                "raw_label": spk,
                "gender": None,
                "voice": None
            }
            
        # Ensure at least Speaker_A exists if no turns were detected
        if not speaker_map:
            speaker_map["Speaker_A"] = {
                "raw_label": "SPEAKER_00",
                "gender": None,
                "voice": None
            }
            
        return speaker_map
