import pytest
import os
import json
from backend.speech.models import Transcript, TranscriptSegment
from backend.translation.translation_memory import TranslationMemory
from backend.translation.post_optimizer import PostTranslationOptimizer
from backend.translation.scene_builder import SceneBuilder
from backend.translation.context_builder import TranslationContextBuilder

@pytest.fixture
def temp_project_dir(tmp_path):
    project_id = "test_project_123"
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    config_dir = projects_dir / project_id / "config"
    config_dir.mkdir(parents=True)
    return str(tmp_path), project_id

def test_translation_memory_persistence(temp_project_dir):
    base_dir, project_id = temp_project_dir
    tm = TranslationMemory(project_id, projects_dir=os.path.join(base_dir, "projects"))
    
    tm.add_term("Apple", "Quả Táo")
    tm.add_character_mapping("Speaker_A", "John", "anh")
    
    context = tm.get_context_string()
    assert "Apple -> Quả Táo" in context
    assert "Speaker_A" in context
    assert "anh" in context
    
    tm.save()
    
    # Reload
    tm2 = TranslationMemory(project_id, projects_dir=os.path.join(base_dir, "projects"))
    assert tm2.memory["terminology"]["Apple"] == "Quả Táo"
    assert tm2.memory["characters"]["Speaker_A"]["pronoun"] == "anh"

def test_post_optimizer():
    # Test hallucinated punctuation
    seg1 = {"id": 1, "text": "Hello....."}
    opt1 = PostTranslationOptimizer.optimize(seg1)
    assert opt1["text"] == "Hello..."
    
    seg2 = {"id": 2, "text": "What???"}
    opt2 = PostTranslationOptimizer.optimize(seg2)
    assert opt2["text"] == "What?"
    
    seg3 = {"id": 3, "text": "Wow!!!"}
    opt3 = PostTranslationOptimizer.optimize(seg3)
    assert opt3["text"] == "Wow!"
    
    # Test hallucinated quotes
    seg4 = {"id": 4, "text": '"This is a test"'}
    opt4 = PostTranslationOptimizer.optimize(seg4)
    assert opt4["text"] == "This is a test"
    
    # Test weird spacing
    seg5 = {"id": 5, "text": "Yes , I am ."}
    opt5 = PostTranslationOptimizer.optimize(seg5)
    assert opt5["text"] == "Yes, I am."

@pytest.mark.asyncio
async def test_translation_context_builder(temp_project_dir):
    base_dir, project_id = temp_project_dir
    tm = TranslationMemory(project_id, projects_dir=os.path.join(base_dir, "projects"))
    tm.add_term("Sword", "Kiếm")
    
    scene_builder = SceneBuilder()
    context_builder = TranslationContextBuilder(scene_builder, analyzer=None)
    
    segments = [
        TranscriptSegment(id=1, start=0, end=1, text="Draw your sword!", speaker_id="Speaker_A")
    ]
    
    context = await context_builder.build_context_for_scene(segments, "Previous scene happened", tm)
    
    assert "--- Project Translation Memory ---" in context
    assert "Sword -> Kiếm" in context
    assert "Previous scene happened" in context
    assert "Speaker_A" in context
