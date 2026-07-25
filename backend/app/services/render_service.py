import os
import subprocess
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from moviepy import ImageClip, VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
from moviepy.video.fx import Loop
from moviepy.audio.fx import AudioLoop
from backend.app.core.config import settings

class RenderService:
    def __init__(self, output_dir: str = "videos", temp_dir: str = "projects"):
        self.output_dir = Path(output_dir).resolve()
        if not self.output_dir.exists():
            self.output_dir = Path("../videos").resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.temp_dir = Path(temp_dir).resolve()
        if not self.temp_dir.exists():
            self.temp_dir = Path("../projects").resolve()
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def _resize_and_crop(self, clip, target_w: int, target_h: int):
        """Resizes and crops a clip to fill the target resolution (9:16, 16:9, 1:1) in MoviePy 2.x."""
        clip_aspect = clip.w / clip.h
        target_aspect = target_w / target_h
        
        if clip_aspect > target_aspect:
            # Clip is wider than target. Resize by height, crop sides.
            new_h = target_h
            new_w = int(new_h * clip_aspect)
            clip_resized = clip.resized(height=new_h)
            x_center = clip_resized.w / 2
            crop_x = x_center - (target_w / 2)
            return clip_resized.cropped(x1=crop_x, y1=0, x2=crop_x + target_w, y2=target_h)
        else:
            # Clip is taller than target. Resize by width, crop top/bottom.
            new_w = target_w
            new_h = int(new_w / clip_aspect)
            clip_resized = clip.resized(width=new_w)
            y_center = clip_resized.h / 2
            crop_y = y_center - (target_h / 2)
            return clip_resized.cropped(x1=0, y1=crop_y, x2=target_w, y2=crop_y + target_h)

    def generate_srt(self, subtitle_data: List[Dict[str, Any]], srt_path: Path):
        """Generates standard SRT subtitles file."""
        def format_time(seconds: float) -> str:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds - int(seconds)) * 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        with open(srt_path, "w", encoding="utf-8") as f:
            for idx, entry in enumerate(subtitle_data):
                start = entry["start"]
                end = entry["end"]
                text = entry["text"]
                f.write(f"{idx + 1}\n")
                f.write(f"{format_time(start)} --> {format_time(end)}\n")
                f.write(f"{text}\n\n")

    def generate_ass(self, subtitle_data: List[Dict[str, Any]], ass_path: Path, width: int = 1080, height: int = 1920):
        """Generates ASS subtitle file with styled word-highlighting/karaoke effects."""
        def format_time(seconds: float) -> str:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            cs = int((seconds - int(seconds)) * 100) # centiseconds
            return f"{h:02d}:{m:02d}:{s:02d}.{cs:02d}"

        # Setup basic ASS content
        ass_header = f"""[Script Info]
Title: AutoShort Studio Subtitles
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{int(height * 0.04)},&H00FFFFFF,&H0000FFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,4,0,2,10,10,{int(height * 0.4)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(ass_header)
            for entry in subtitle_data:
                start = format_time(entry["start"])
                end = format_time(entry["end"])
                
                # Check if word timing details are provided
                words_info = entry.get("words", [])
                if words_info:
                    # Construct Karaoke string: e.g. {\k20}Word1 {\k30}Word2
                    karaoke_text = ""
                    for w in words_info:
                        w_start = w["start"]
                        w_end = w["end"]
                        w_text = w["text"]
                        
                        # Duration in centiseconds
                        dur_cs = max(1, int((w_end - w_start) * 100))
                        # Karaoke code \k in centiseconds
                        karaoke_text += f"{{\\k{dur_cs}}}{w_text} "
                    text = karaoke_text.strip()
                else:
                    text = entry["text"]
                    
                f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")

    async def render_video(
        self,
        scenes: List[Dict[str, Any]], # List of dict: {"audio_path": str, "asset_path": str, "text": str, "asset_type": "image"|"video"}
        subtitle_data: List[Dict[str, Any]], # Subtitle entries with timing
        aspect_ratio: str = "9:16",
        bg_music_path: Optional[str] = None,
        bg_music_volume: float = 0.1,
        project_id: Optional[str] = None
    ) -> str:
        """Renders video, overlays subtitles, returns path to completed video file."""
        if not project_id:
            project_id = uuid.uuid4().hex
            
        # Determine resolutions
        if aspect_ratio == "16:9":
            width, height = 1920, 1080
        elif aspect_ratio == "1:1":
            width, height = 1080, 1080
        else: # "9:16"
            width, height = 1080, 1920
            
        scene_clips = []
        cumulative_duration = 0.0
        
        # 1. Process and composite each scene clip
        for scene in scenes:
            audio_path = scene["audio_path"]
            asset_path = scene["asset_path"]
            asset_type = scene.get("asset_type", "image")
            
            # Load Audio Clip to get duration
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            
            # Create Visual Clip
            if asset_type == "image":
                visual_clip = ImageClip(asset_path).with_duration(duration)
            else:
                visual_clip = VideoFileClip(asset_path).subclipped(0, duration)
                # Ensure it fits duration, loop if shorter
                if visual_clip.duration < duration:
                    visual_clip = visual_clip.with_effects([Loop(duration=duration)])
                    
            # Scale and Crop
            visual_clip = self._resize_and_crop(visual_clip, width, height)
            
            # Set Audio
            visual_clip = visual_clip.with_audio(audio_clip)
            
            scene_clips.append(visual_clip)
            cumulative_duration += duration
            
        # Concatenate scenes
        final_clip = concatenate_videoclips(scene_clips, method="compose")
        
        # 2. Add Background Music if provided
        if bg_music_path and os.path.exists(bg_music_path):
            bg_music = AudioFileClip(bg_music_path)
            # Loop bg music if shorter than video, crop if longer
            bg_music = bg_music.with_effects([AudioLoop(duration=final_clip.duration)])
            # Lower volume
            bg_music = bg_music.with_volume_scaled(bg_music_volume)
            # Mix music with narration audio
            mixed_audio = CompositeAudioClip([final_clip.audio, bg_music])
            final_clip = final_clip.with_audio(mixed_audio)
            
        # 3. Export draft video
        draft_video_path = self.temp_dir / f"draft_{project_id}.mp4"
        
        # Run MoviePy render in threadpool since it's sync and heavy CPU bound
        import asyncio
        def run_moviepy():
            final_clip.write_videofile(
                str(draft_video_path),
                fps=24,
                codec="libx264",
                audio_codec="aac",
                logger=None
            )
            
        await asyncio.to_thread(run_moviepy)
        
        # Close all clips to release file handles
        final_clip.close()
        for c in scene_clips:
            c.close()
            
        # 4. Generate subtitles files
        ass_sub_path = self.temp_dir / f"subs_{project_id}.ass"
        self.generate_ass(subtitle_data, ass_sub_path, width, height)
        
        # 5. Burn subtitles using FFmpeg
        final_video_name = f"video_{project_id}.mp4"
        final_video_path = self.output_dir / final_video_name
        
        # Escape path backslashes for FFmpeg filters on Windows
        escaped_ass_path = str(ass_sub_path).replace("\\", "/").replace(":", "\\:")
        
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", str(draft_video_path),
            "-vf", f"ass={escaped_ass_path}",
            "-c:a", "copy", # Copy audio directly without re-encoding
            str(final_video_path)
        ]
        
        def run_ffmpeg():
            subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        await asyncio.to_thread(run_ffmpeg)
        
        # 6. Cleanup draft files
        try:
            if draft_video_path.exists():
                os.remove(draft_video_path)
            if ass_sub_path.exists():
                os.remove(ass_sub_path)
        except Exception as e:
            print(f"Cleanup error: {e}")
            
        return str(final_video_path)
