import asyncio
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.app.core.database import Base
from backend.app.models.models import Provider, Project
from backend.app.repositories.repositories import ProviderRepository, ProjectRepository
from backend.app.services.prompt_service import PromptService
from backend.app.services.audio_service import AudioService
from backend.app.services.asset_service import AssetService
from backend.app.services.render_service import RenderService
from backend.app.services.workflow_service import WorkflowService

# Test config
DB_URL = "sqlite+aiosqlite:///database/test_verify.db"

async def test_integration_run():
    print("Starting integration test run...")
    
    # 1. Database engine init
    engine = create_async_engine(DB_URL, connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        # Seed default mock provider
        provider_repo = ProviderRepository(db)
        existing = await provider_repo.get_by_name("chatanywhere")
        if not existing:
            await provider_repo.create({
                "name": "chatanywhere",
                "base_url": "https://api.chatanywhere.tech/v1",
                "is_active": True
            })
            await db.commit()
            
        # Create verification project
        project_repo = ProjectRepository(db)
        project = await project_repo.create({
            "name": "Verify Render Pipeline",
            "aspect_ratio": "9:16",
            "config": {
                "topic": "Verify the universe creation",
                "duration": 10,
                "language": "English",
                "voice_type": "edge",
                "voice_name": "en-US-BrianNeural",
                "rewrite": False
            }
        })
        await db.commit()
        project_id = project.id
        print(f"Created verification project ID: {project_id}")
        
        # Instantiate services
        prompt_svc = PromptService()
        audio_svc = AudioService()
        asset_svc = AssetService()
        render_svc = RenderService()
        
        workflow_svc = WorkflowService(
            db=db,
            prompt_service=prompt_svc,
            audio_service=audio_svc,
            asset_service=asset_svc,
            render_service=render_svc
        )
        
        # Mock LLM calls by directly supplying mock scenes list inside config
        # to bypass external API requirement during verification
        project.config["scenes"] = [
            {"text": "Welcome to the universe compilation test.", "visual_description": "starry sky space nebula"},
            {"text": "Everything is functioning perfectly.", "visual_description": "network server coding concept"}
        ]
        db.add(project)
        await db.commit()
        
        print("Running workflow pipeline mock rendering...")
        # Since we preloaded scenes, run the workflow stages (TTS + Visual fallbacks + MoviePy stitching + subtitle overlay)
        # We can simulate the second half of run_workflow
        # Let's verify and trigger the render directly to test all media codecs, MoviePy timeline compilation,
        # ASS subtitle styling, and FFmpeg filter burning.
        
        processed_scenes = []
        subtitle_timeline = []
        cumulative_time = 0.0
        
        for idx, scene in enumerate(project.config["scenes"]):
            text = scene["text"]
            visual_desc = scene["visual_description"]
            
            # Voice
            print(f"Generating TTS for scene {idx}...")
            voice_filename = f"verify_voice_{project_id}_{idx}.mp3"
            audio_path, word_boundaries = await audio_svc.generate_tts(
                text=text,
                voice_type="edge",
                voice_name="en-US-BrianNeural",
                output_name=voice_filename
            )
            
            # Asset
            print(f"Generating gradient background fallback for scene {idx}...")
            asset_path, source = await asset_svc.search_and_download(
                keywords=visual_desc,
                project_id=project_id,
                asset_type="image"
            )
            
            # Audio duration
            from moviepy import AudioFileClip
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            audio_clip.close()
            
            processed_scenes.append({
                "audio_path": audio_path,
                "asset_path": asset_path,
                "asset_type": "image",
                "text": text
            })
            
            scene_end = cumulative_time + duration
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
            
        print("Stitching timeline and burning subtitles via FFmpeg filters...")
        output_video_path = await render_svc.render_video(
            scenes=processed_scenes,
            subtitle_data=subtitle_timeline,
            aspect_ratio="9:16",
            project_id=project_id
        )
        
        print(f"Rendering completed successfully! Output file is at: {output_video_path}")
        assert os.path.exists(output_video_path)
        print("All assertions passed!")
        
        # Cleanup verification test outputs
        try:
            # Clean db session
            await db.close()
            await engine.dispose()
            
            # Remove test voice clips
            for scene in processed_scenes:
                if os.path.exists(scene["audio_path"]):
                    os.remove(scene["audio_path"])
                if os.path.exists(scene["asset_path"]):
                    os.remove(scene["asset_path"])
            
            # Keep the output video so the user can verify it, or clean up if desired.
            # Let's keep the video in the videos/ directory as proof of work.
            if os.path.exists(DB_URL.replace("sqlite:///", "")):
                os.remove(DB_URL.replace("sqlite:///", ""))
            print("Cleanup completed.")
        except Exception as e:
            print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    asyncio.run(test_integration_run())
