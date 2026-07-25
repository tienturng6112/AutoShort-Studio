import json
import logging
import re
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.repositories.repositories import (
    ProviderRepository,
    SettingRepository,
    ProjectRepository,
    AssetRepository,
    HistoryRepository
)
from backend.app.providers.factory import AIProviderFactory
from backend.app.services.prompt_service import PromptService
from backend.app.services.audio_service import AudioService
from backend.app.services.asset_service import AssetService
from backend.app.services.render_service import RenderService

logger = logging.getLogger("workflow")

class WorkflowService:
    def __init__(
        self,
        db: AsyncSession,
        prompt_service: PromptService,
        audio_service: AudioService,
        asset_service: AssetService,
        render_service: RenderService
    ):
        self.db = db
        self.prompt_service = prompt_service
        self.audio_service = audio_service
        self.asset_service = asset_service
        self.render_service = render_service
        
        self.provider_repo = ProviderRepository(db)
        self.setting_repo = SettingRepository(db)
        self.project_repo = ProjectRepository(db)
        self.asset_repo = AssetRepository(db)
        self.history_repo = HistoryRepository(db)

    def _extract_json_array(self, text: str) -> List[Dict[str, Any]]:
        """Cleans and extracts JSON array content from raw model string response."""
        try:
            return json.loads(text.strip())
        except Exception:
            pass
            
        # Regex search for brackets
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
                
        # Regex search for braces (in case of wrapping object)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                for v in data.values():
                    if isinstance(v, list):
                        return v
            except Exception:
                pass
                
        raise ValueError(f"Could not parse script JSON array structure. Raw output was: {text}")

    async def run_workflow(self, project_id: str):
        """Runs the entire AutoShort pipeline and updates the database state."""
        project = await self.project_repo.get(project_id)
        if not project:
            logger.error(f"Project ID {project_id} not found in database.")
            return
            
        project.status = "rendering"
        await self.db.commit()
        
        try:
            config = project.config or {}
            topic = config.get("topic", "")
            duration = config.get("duration", 30)
            language = config.get("language", "Vietnamese")
            voice_type = config.get("voice_type", "edge")
            voice_name = config.get("voice_name", "vi-VN-HoaiMyNeural")
            bg_music = config.get("bg_music", None)
            bg_volume = config.get("bg_volume", 0.1)
            
            # 1. Load active AI Provider configuration
            provider_id = config.get("provider_id")
            if provider_id:
                provider = await self.provider_repo.get(provider_id)
            else:
                active_providers = await self.provider_repo.get_active()
                provider = active_providers[0] if active_providers else None
                
            if not provider:
                raise ValueError("No active AI Provider configured. Add a provider in Settings first.")
                
            model_name = config.get("model_name")
            
            # Setup AI strategy client
            ai_client = AIProviderFactory.get_provider(
                name=provider.name,
                api_key=provider.api_key,
                base_url=provider.base_url
            )
            
            # 2. Topic -> Script
            await self.history_repo.create({
                "project_id": project_id,
                "action": "generating_script",
                "details": {"topic": topic}
            })
            await self.db.commit()
            
            prompt_vars = {
                "topic": topic,
                "duration": duration,
                "language": language
            }
            
            script_prompt = self.prompt_service.format_prompt("script", prompt_vars)
            
            script_raw = await ai_client.generate_text(
                prompt=script_prompt["user"],
                system_prompt=script_prompt["system"],
                model=model_name,
                json_mode=True
            )
            
            scenes_data = self._extract_json_array(script_raw)
            
            # 3. Optional Script Polish (Rewrite)
            if config.get("rewrite", False):
                await self.history_repo.create({
                    "project_id": project_id,
                    "action": "rewriting_script",
                    "details": {}
                })
                await self.db.commit()
                
                rewrite_prompt = self.prompt_service.format_prompt("rewrite", {"script": json.dumps(scenes_data)})
                rewrite_raw = await ai_client.generate_text(
                    prompt=rewrite_prompt["user"],
                    system_prompt=rewrite_prompt["system"],
                    model=model_name,
                    json_mode=True
                )
                scenes_data = self._extract_json_array(rewrite_raw)
                
            # Update project configuration with the final script scenes
            config["scenes"] = scenes_data
            project.config = config
            await self.db.commit()
            
            # 4. Generate Voice Over and Stock Visual Assets for each scene
            processed_scenes = []
            subtitle_timeline = []
            cumulative_time = 0.0
            
            # Load download tokens/credentials
            pexels_key = await self.setting_repo.get_value("pexels_api_key")
            pixabay_key = await self.setting_repo.get_value("pixabay_api_key")
            
            # Resolve TTS API credentials
            tts_api_key = None
            if voice_type == "openai":
                tts_api_key = provider.api_key
            elif voice_type == "elevenlabs":
                tts_api_key = await self.setting_repo.get_value("elevenlabs_api_key")
                
            for idx, scene in enumerate(scenes_data):
                text = scene.get("text", "")
                visual_desc = scene.get("visual_description", "")
                
                # 4a. Text-To-Speech conversion
                voice_filename = f"voice_{project_id}_scene_{idx}.mp3"
                audio_path, word_boundaries = await self.audio_service.generate_tts(
                    text=text,
                    voice_type=voice_type,
                    voice_name=voice_name,
                    api_key=tts_api_key,
                    output_name=voice_filename
                )
                
                # Load TTS duration
                from moviepy import AudioFileClip
                audio_clip = AudioFileClip(audio_path)
                scene_duration = audio_clip.duration
                audio_clip.close()
                
                # Register voice asset
                await self.asset_repo.create({
                    "project_id": project_id,
                    "type": "audio",
                    "path": audio_path,
                    "source": "generated",
                    "meta": {"text": text, "scene_index": idx}
                })
                
                # 4b. Find matching visual asset
                asset_path, source_type = await self.asset_service.search_and_download(
                    keywords=visual_desc,
                    project_id=project_id,
                    asset_type="image",
                    pexels_key=pexels_key,
                    pixabay_key=pixabay_key
                )
                
                # Register visual asset in database
                await self.asset_repo.create({
                    "project_id": project_id,
                    "type": "image",
                    "path": asset_path,
                    "source": source_type,
                    "meta": {"visual_desc": visual_desc, "scene_index": idx}
                })
                
                processed_scenes.append({
                    "audio_path": audio_path,
                    "asset_path": asset_path,
                    "asset_type": "image",
                    "text": text
                })
                
                # 4c. Align subtitles globally
                scene_end = cumulative_time + scene_duration
                
                mapped_words = []
                for w in word_boundaries:
                    mapped_words.append({
                        "text": w["text"],
                        "start": cumulative_time + w["start"],
                        "end": cumulative_time + w["end"]
                    })
                    
                subtitle_timeline.append({
                    "start": cumulative_time,
                    "end": scene_end,
                    "text": text,
                    "words": mapped_words
                })
                
                cumulative_time = scene_end
                
            # 5. Composite and Render final mp4 output
            await self.history_repo.create({
                "project_id": project_id,
                "action": "rendering_video",
                "details": {"scenes_count": len(processed_scenes)}
            })
            await self.db.commit()
            
            final_video_path = await self.render_service.render_video(
                scenes=processed_scenes,
                subtitle_data=subtitle_timeline,
                aspect_ratio=project.aspect_ratio,
                bg_music_path=bg_music,
                bg_music_volume=bg_volume,
                project_id=project_id
            )
            
            # Register completed video asset
            await self.asset_repo.create({
                "project_id": project_id,
                "type": "video",
                "path": final_video_path,
                "source": "rendered",
                "meta": {"aspect_ratio": project.aspect_ratio}
            })
            
            # 6. Save metadata and finish
            project.status = "completed"
            config["final_video"] = final_video_path
            project.config = config
            
            await self.history_repo.create({
                "project_id": project_id,
                "action": "completed",
                "details": {"video_path": final_video_path}
            })
            await self.db.commit()
            logger.info(f"Project {project_id} successfully compiled and exported.")
            
        except Exception as e:
            logger.exception(f"Workflow pipeline failed for project {project_id}")
            project.status = "failed"
            await self.history_repo.create({
                "project_id": project_id,
                "action": "failed",
                "details": {"error": str(e)}
            })
            await self.db.commit()
            raise e
