import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any

from backend.app.core.config import settings
from backend.app.core.database import engine, Base, get_db, AsyncSessionLocal
from backend.app.models.models import Provider, Setting
from backend.app.repositories.repositories import (
    ProviderRepository,
    ProjectRepository,
    AssetRepository,
    HistoryRepository,
    SettingRepository,
    LogRepository
)
from backend.app.schemas.schemas import (
    ProviderCreate,
    ProviderUpdate,
    ProviderResponse,
    ProjectCreate,
    ProjectResponse,
    SettingUpdate,
    PromptUpdate
)
from backend.app.providers.factory import AIProviderFactory
from backend.app.services.prompt_service import PromptService
from backend.app.services.queue_manager import queue_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

async def seed_data():
    """Seed initial settings and default providers if database is empty."""
    async with AsyncSessionLocal() as db:
        # Check providers
        result = await db.execute(select(Provider))
        providers = result.scalars().all()
        if not providers:
            logger.info("Seeding default providers...")
            default_providers = [
                Provider(name="chatanywhere", base_url="https://api.chatanywhere.tech/v1", is_active=True),
                Provider(name="openai", base_url="https://api.openai.com/v1", is_active=False),
                Provider(name="gemini", base_url="https://generativelanguage.googleapis.com", is_active=False),
                Provider(name="claude", base_url="https://api.anthropic.com", is_active=False),
                Provider(name="groq", base_url="https://api.groq.com/openai/v1", is_active=False),
                Provider(name="openrouter", base_url="https://openrouter.ai/api/v1", is_active=False),
                Provider(name="ollama", base_url="http://localhost:11434/v1", is_active=False),
                Provider(name="lm_studio", base_url="http://localhost:1234/v1", is_active=False)
            ]
            db.add_all(default_providers)
            
        # Seed standard settings
        setting_repo = SettingRepository(db)
        for key, val in [("pexels_api_key", ""), ("pixabay_api_key", ""), ("elevenlabs_api_key", "")]:
            setting = await setting_repo.get(key)
            if not setting:
                await setting_repo.set_value(key, val)
                
        await db.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    await seed_data()
    
    # Start task queue
    queue_manager.start()
    
    yield
    
    # Shutdown
    queue_manager.stop()

app = FastAPI(
    title="AutoShort Studio API",
    description="Modern rebuild of ShortGPT pipeline",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Mount static asset folders for media playback
app.mount("/videos", StaticFiles(directory=settings.VIDEOS_DIR), name="videos")
app.mount("/voices", StaticFiles(directory=settings.VOICES_DIR), name="voices")
app.mount("/assets", StaticFiles(directory=settings.ASSETS_DIR), name="assets")

# Initialize prompt service
prompt_service = PromptService()

# -----------------
# 1. PROVIDERS API
# -----------------
@app.get("/providers", response_model=List[ProviderResponse])
async def get_providers(db: AsyncSession = Depends(get_db)):
    repo = ProviderRepository(db)
    return await repo.get_all()

@app.post("/providers", response_model=ProviderResponse)
async def create_provider(data: ProviderCreate, db: AsyncSession = Depends(get_db)):
    repo = ProviderRepository(db)
    existing = await repo.get_by_name(data.name)
    if existing:
        raise HTTPException(status_code=400, detail="Provider name already exists")
    
    new_provider = await repo.create(data.model_dump())
    await db.commit()
    await db.refresh(new_provider)
    return new_provider

@app.put("/providers/{provider_id}", response_model=ProviderResponse)
async def update_provider(provider_id: str, data: ProviderUpdate, db: AsyncSession = Depends(get_db)):
    repo = ProviderRepository(db)
    provider = await repo.get(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    updated = await repo.update(provider, data.model_dump(exclude_unset=True))
    await db.commit()
    await db.refresh(updated)
    return updated

@app.post("/providers/{provider_id}/test")
async def test_provider_connection(provider_id: str, db: AsyncSession = Depends(get_db)):
    repo = ProviderRepository(db)
    provider = await repo.get(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
        
    ai_client = AIProviderFactory.get_provider(
        name=provider.name,
        api_key=provider.api_key,
        base_url=provider.base_url
    )
    
    is_ok = await ai_client.test_connection()
    return {"status": "success" if is_ok else "failed"}

# -----------------
# 2. MODELS API
# -----------------
@app.get("/models")
async def list_provider_models(provider_name: str, api_key: Optional[str] = None, base_url: Optional[str] = None):
    """Loads models list dynamically by query calling provider.list_models()."""
    ai_client = AIProviderFactory.get_provider(
        name=provider_name,
        api_key=api_key,
        base_url=base_url
    )
    try:
        models = await ai_client.list_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load models: {str(e)}")

# -----------------
# 3. PROJECTS API
# -----------------
@app.get("/projects", response_model=List[ProjectResponse])
async def get_projects(db: AsyncSession = Depends(get_db)):
    repo = ProjectRepository(db)
    return await repo.get_all()

@app.post("/projects", response_model=ProjectResponse)
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    repo = ProjectRepository(db)
    new_project = await repo.create(data.model_dump())
    await db.commit()
    await db.refresh(new_project)
    return new_project

@app.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    repo = ProjectRepository(db)
    project = await repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.delete("/projects/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    repo = ProjectRepository(db)
    project = await repo.delete(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.commit()
    return {"status": "success", "message": f"Project {project_id} deleted."}

# -----------------
# 4. WORKFLOW API
# -----------------
@app.post("/workflow/run/{project_id}")
async def run_project_workflow(project_id: str, db: AsyncSession = Depends(get_db)):
    repo = ProjectRepository(db)
    project = await repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if project.status in ["queuing", "rendering"]:
        return {"status": "error", "message": "Project is already in queue or rendering."}
        
    project.status = "queuing"
    await db.commit()
    
    # Add project to queue
    await queue_manager.add_project(project_id)
    return {"status": "queued", "message": f"Project {project_id} added to execution queue."}

# -----------------
# 5. RENDER API
# -----------------
@app.get("/render/queue")
async def get_render_queue_status():
    return queue_manager.get_status()

# -----------------
# 6. HISTORY API
# -----------------
@app.get("/history/{project_id}")
async def get_project_history(project_id: str, db: AsyncSession = Depends(get_db)):
    repo = HistoryRepository(db)
    return await repo.get_by_project(project_id)

# -----------------
# 7. SETTINGS API
# -----------------
@app.get("/settings")
async def get_settings(db: AsyncSession = Depends(get_db)):
    repo = SettingRepository(db)
    settings_list = await repo.get_all()
    return {s.key: s.value.get("value") if isinstance(s.value, dict) else s.value for s in settings_list}

@app.post("/settings")
async def update_setting(data: SettingUpdate, db: AsyncSession = Depends(get_db)):
    repo = SettingRepository(db)
    updated = await repo.set_value(data.key, data.value)
    await db.commit()
    return {"status": "success", "key": updated.key, "value": updated.value}

# -----------------
# 8. PROMPTS API
# -----------------
@app.get("/prompts")
async def list_prompts():
    return {"groups": prompt_service.list_groups()}

@app.get("/prompts/{group}")
async def get_prompt_details(group: str):
    details = prompt_service.load_prompt(group)
    if not details:
        raise HTTPException(status_code=404, detail=f"Prompt group {group} not found")
    return details

@app.post("/prompts/{group}")
async def update_prompt_details(group: str, data: PromptUpdate):
    if data.group != group:
        raise HTTPException(status_code=400, detail="URL group does not match body")
    success = prompt_service.save_prompt(group, data.system, data.user)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save prompt configuration")
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    # Use config specifications
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.reload)
