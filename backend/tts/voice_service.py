print("VOICE_SERVICE =", __file__)
import os
import time
import subprocess
import wave
import struct
import tempfile
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from backend.speech.models import Transcript
from backend.tts.audio_merger import AudioMerger
from backend.tts.audio_normalizer import AudioNormalizer
from backend.tts.silence_generator import SilenceGenerator
from backend.providers.speech.base_speech_provider import BaseSpeechProvider
from backend.tts.voice_cache import VoiceCache

class TTSBenchmark(BaseModel):
    """Execution telemetry captured for voice synthesis performance audits."""
    provider: str = Field(..., description="TTS provider identifier")
    voice: str = Field(..., description="Selected voice model name")
    synthesis_time_seconds: float = Field(..., description="Total processing time in seconds")
    realtime_factor: float = Field(..., description="Execution speed ratio (synthesis_time / audio_duration)")


class VoiceService:
    """Orchestrates timeline voice synthesis, cache lookups, silences insertion, and exports."""

    def __init__(
        self, 
        provider: BaseSpeechProvider, 
        cache: VoiceCache, 
        temp_dir: str = "projects/temp_tts"
    ) -> None:
        self._provider = provider
        self._cache = cache
        self._temp_dir = temp_dir
        os.makedirs(self._temp_dir, exist_ok=True)

    async def synthesize_transcript(
        self, 
        transcript: Transcript, 
        voice_name: str, 
        output_dir: str,
        tts_dir: Optional[str] = None,
        provider_name: str = "edge-tts",
        speaker_voices: Optional[Dict[str, str]] = None
    ) -> Tuple[str, str, TTSBenchmark]:
        """Synthesizes an entire transcript, adding silences for timing gaps and saving as WAV/MP3.
        
        Args:
            transcript (Transcript): The input aligned transcript.
            voice_name (str): Target voice to use.
            output_dir (str): Location folder to export the final audio.
            tts_dir (Optional[str]): Location folder to export individual tts segment clips.
            provider_name (str): Provider identifier name.
            
        Returns:
            Tuple[str, str, TTSBenchmark]: Path to voice.wav, path to voice.mp3, and benchmark telemetry.
        """
        if not transcript.segments:
            raise ValueError("Voice synthesis error: Transcript contains no segments.")

        # Resolve tts directory
        if tts_dir is None:
            parent_dir = os.path.dirname(output_dir)
            tts_dir = os.path.join(parent_dir, "tts")
        os.makedirs(tts_dir, exist_ok=True)

        # Verify the text passed into Edge-TTS, save speech_input.txt, and verify it equals subtitle.srt (without timestamps)
        speech_input_content = "\n".join(seg.text.strip() for seg in transcript.segments if seg.text.strip())
        
        # Save to speech_input.txt (both workspace root and output_dir)
        try:
            with open("speech_input.txt", "w", encoding="utf-8") as f:
                f.write(speech_input_content)
        except Exception as e:
            pass
            
        try:
            os.makedirs(output_dir, exist_ok=True)
            with open(os.path.join(output_dir, "speech_input.txt"), "w", encoding="utf-8") as f:
                f.write(speech_input_content)
        except Exception as e:
            pass
            
        # Get subtitle.srt (without timestamps)
        srt_content = transcript.to_srt()
        srt_lines = srt_content.splitlines()
        clean_srt_lines = []
        for line in srt_lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.isdigit():
                continue
            if "-->" in stripped:
                continue
            clean_srt_lines.append(stripped)
        clean_srt_content = "\n".join(clean_srt_lines)
        
        # Verify
        norm_speech = "\n".join(line.strip() for line in speech_input_content.splitlines() if line.strip())
        norm_srt = "\n".join(line.strip() for line in clean_srt_content.splitlines() if line.strip())
        if norm_speech != norm_srt:
            mismatch_idx = 0
            min_len = min(len(norm_speech), len(norm_srt))
            while mismatch_idx < min_len and norm_speech[mismatch_idx] == norm_srt[mismatch_idx]:
                mismatch_idx += 1
            
            start_pos = max(0, mismatch_idx - 30)
            speech_snippet = norm_speech[start_pos:min(len(norm_speech), mismatch_idx + 50)]
            srt_snippet = norm_srt[start_pos:min(len(norm_srt), mismatch_idx + 50)]
            
            import logging
            logger = logging.getLogger("VoiceService")
            logger.error(
                f"Mismatch at index {mismatch_idx}\n\n"
                f"speech_input:\n{speech_snippet}\n\n"
                f"subtitle:\n{srt_snippet}"
            )
            
            raise ValueError(
                f"Verification failed: speech_input.txt does not equal subtitle.srt without timestamps!\n"
                f"Speech length: {len(norm_speech)}, SRT length: {len(norm_srt)}\n"
                f"Mismatch at index {mismatch_idx}\n\n"
                f"speech_input:\n{speech_snippet}\n\n"
                f"subtitle:\n{srt_snippet}"
            )

        # Enforce voice verification
        voices_to_verify = [voice_name]
        if speaker_voices:
            voices_to_verify.extend(speaker_voices.values())
        for v in voices_to_verify:
            await self._provider.validate_voice(v, transcript.language)

        start_time = time.perf_counter()
        
        def transcode_to_pcm(input_path: str, output_path: str, sample_rate: int = 24000) -> None:
            cmd = [
                "ffmpeg", "-y",
                "-i", input_path,
                "-ar", str(sample_rate),
                "-ac", "1",
                "-c:a", "pcm_s16le",
                output_path
            ]
            result = subprocess.run(cmd, capture_output=True, check=False)
            if result.returncode != 0:
                stderr_msg = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
                raise RuntimeError(f"FFmpeg segment transcode failed: {stderr_msg}")

        def write_wav_with_header(pcm_data: bytes, output_path: str, sample_rate: int = 24000) -> None:
            num_channels = 1
            bytes_per_sample = 2
            byte_rate = sample_rate * num_channels * bytes_per_sample
            block_align = num_channels * bytes_per_sample
            data_size = len(pcm_data)
            chunk_size = 36 + data_size
            
            header = struct.pack(
                "<4sI4s4sIHHIIHH4sI",
                b"RIFF", chunk_size, b"WAVE", b"fmt ", 16, 1, num_channels,
                sample_rate, byte_rate, block_align, 16, b"data", data_size
            )
            with open(output_path, "wb") as fp:
                fp.write(header)
                fp.write(pcm_data)

        # Initialize silent PCM mono canvas at 24000Hz matching video duration
        sample_rate = 24000
        num_samples = int(transcript.duration * sample_rate)
        pcm_canvas = bytearray(num_samples * 2)  # 16-bit mono PCM (2 bytes/sample)

        # 1. Iterate segments, generate/retrieve cached audio, transcode, and overlay onto canvas
        for idx, seg in enumerate(transcript.segments):
            if tts_dir:
                p_dir = os.path.dirname(os.path.abspath(tts_dir))
                pause_flag = os.path.join(p_dir, "pause.flag")
                import asyncio
                while os.path.exists(pause_flag):
                    await asyncio.sleep(0.5)
            if not seg.text.strip():
                # Skip silent/empty timeline padded segments
                continue

            # Output segment clip path
            seg_output = os.path.join(tts_dir, f"{seg.id:04d}.wav")
            
            # Determine the voice for this segment based on speaker_id
            seg_voice = voice_name
            if speaker_voices:
                if not seg.speaker_id:
                    raise ValueError(
                        f"Voice synthesis error: Segment {seg.id} is missing a speaker_id assignment "
                        f"while speaker_voices mapping is configured."
                    )
                if seg.speaker_id not in speaker_voices:
                    raise KeyError(
                        f"Voice synthesis error: Speaker ID '{seg.speaker_id}' in segment {seg.id} "
                        f"is not configured in speaker_voices mapping."
                    )
                seg_voice = speaker_voices[seg.speaker_id]
                
            import logging
            logger = logging.getLogger("VoiceService")
            logger.info(f"[DEBUG] Voice passed to synthesize(): Segment {seg.id} ({repr(seg.text[:15])}) -> {seg_voice}")
                
            # Synthesize or retrieve cached segment audio
            cached_path = self._cache.get(seg.text, seg_voice)
            if cached_path and os.path.exists(cached_path):
                import shutil
                shutil.copy2(cached_path, seg_output)
            else:
                emotion_profile = seg.emotion if hasattr(seg, "emotion") else None
                await self._provider.generate(seg.text, seg_voice, seg_output, emotion_profile=emotion_profile)
                cached_path = self._cache.set(seg.text, seg_voice, seg_output)
                if cached_path != seg_output:
                    import shutil
                    shutil.copy2(cached_path, seg_output)
                
            # Transcode segment WAV to PCM 24kHz mono temporarily
            temp_pcm_path = os.path.join(self._temp_dir, f"temp_pcm_{seg.id}.wav")
            transcode_to_pcm(seg_output, temp_pcm_path, sample_rate=sample_rate)
            
            try:
                with open(temp_pcm_path, "rb") as fp:
                    wav_content = fp.read()
                pcm_bytes = wav_content[44:]  # Skip RIFF header
                
                # Overlay onto silent canvas by timeline
                start_sample = int(seg.start * sample_rate)
                num_seg_samples = len(pcm_bytes) // 2
                
                # Unpack and mix (with clamp protection)
                seg_samples = struct.unpack(f"<{num_seg_samples}h", pcm_bytes)
                for i, val in enumerate(seg_samples):
                    target_idx = start_sample + i
                    if target_idx >= num_samples:
                        break
                    
                    # Read target PCM frame
                    curr_val = struct.unpack_from("<h", pcm_canvas, target_idx * 2)[0]
                    mixed_val = max(-32768, min(32767, curr_val + val))
                    struct.pack_into("<h", pcm_canvas, target_idx * 2, mixed_val)
            finally:
                if os.path.exists(temp_pcm_path):
                    try:
                        os.remove(temp_pcm_path)
                    except Exception:
                        pass

        # 2. Write the composite PCM canvas into final raw merged file
        merged_raw_path = os.path.join(self._temp_dir, "merged_raw.wav")
        write_wav_with_header(bytes(pcm_canvas), merged_raw_path, sample_rate=sample_rate)

        # 3. Normalize and export target WAV and MP3 formats
        os.makedirs(output_dir, exist_ok=True)
        final_wav = os.path.join(output_dir, "voice.wav")
        final_mp3 = os.path.join(output_dir, "voice.mp3")

        # Normalize outputs to 16kHz mono EBU R128 standards
        AudioNormalizer.normalize_audio(merged_raw_path, final_wav, sample_rate=16000, channels=1)
        AudioNormalizer.normalize_audio(merged_raw_path, final_mp3, sample_rate=16000, channels=1)

        end_time = time.perf_counter()
        elapsed = end_time - start_time
        rtf = elapsed / transcript.duration if transcript.duration > 0 else 0.0

        benchmark = TTSBenchmark(
            provider=provider_name,
            voice=voice_name,
            synthesis_time_seconds=elapsed,
            realtime_factor=rtf
        )

        # Cleanup temp raw merged file
        if os.path.exists(merged_raw_path):
            try:
                os.remove(merged_raw_path)
            except Exception:
                pass

        return final_wav, final_mp3, benchmark
