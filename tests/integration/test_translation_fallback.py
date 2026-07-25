import os
import subprocess
import json
import shutil
import sys
import time

def test_translation_fallback():
    print("--- Running Translation Fallback Regression Test ---")
    
    workspace = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    project_id = "test_fallback_project"
    project_dir = os.path.join(workspace, "projects", project_id)
    
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)
        
    os.makedirs(os.path.join(project_dir, "subtitle"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "translation"), exist_ok=True)
    
    dummy_vid = "fake.mp4"
    
    fake_transcript = {
        "text": "Hello world",
        "language": "en",
        "language_probability": 1.0,
        "duration": 5.0,
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 5.0,
                "text": "Hello world",
                "words": [],
                "confidence": 1.0
            }
        ]
    }
    with open(os.path.join(project_dir, "subtitle", "transcript.json"), "w", encoding="utf-8") as f:
        json.dump(fake_transcript, f)
        
    project_metadata = {
        "project_id": project_id,
        "project_name": "Test Project",
        "created_at": time.time(),
        "modified_at": time.time(),
        "input_video": dummy_vid,
        "pipeline_state": {
            "stage_1_import": True,
            "stage_2_denoise": True,
            "stage_3_speech": True
        },
        "metadata": {
            "video_path": dummy_vid,
            "speech_audio_path": "fake.wav",
            "speaker_map": {"SPEAKER_00": "Speaker_A"}
        },
        "execution_state": {
            "status": "Running",
            "progress_percent": 37,
            "current_stage": "Stage 3: Speech Recognition"
        },
        "settings_snapshot": {
            "output_mode": "Subtitle Only"
        },
        "languages": {
            "source": "en",
            "target": "vi"
        }
    }
    with open(os.path.join(project_dir, "project.json"), "w", encoding="utf-8") as f:
        json.dump(project_metadata, f)

    settings_path = os.path.join(workspace, "config", "settings.json")
    backup_settings_path = os.path.join(workspace, "config", "settings.json.bak")
    
    if os.path.exists(settings_path):
        shutil.copy2(settings_path, backup_settings_path)
        
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
            
        settings["translation_provider"] = "ChatAnywhere"
        if "chatanywhere" not in settings:
            settings["chatanywhere"] = {}
        settings["chatanywhere"]["api_key"] = "sk-invalid-test-key-for-401"
        
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
            
        cmd = [
            sys.executable, "backend/run_pipeline.py",
            "--project-id", project_id
        ]
        
        print("Running pipeline with invalid API key (Expect 401 Unauthorized)...")
        result = subprocess.run(cmd, cwd=workspace, capture_output=True, text=True)
        
        print(f"Pipeline Return Code: {result.returncode}")
        
        if result.returncode == 0:
            print("FAILED: Pipeline reported success instead of failing!")
            sys.exit(1)
            
        full_out = result.stdout + result.stderr
        
        if "Lỗi Dịch Thuật" not in full_out and "API Key không hợp lệ" not in full_out:
            print("FAILED: Did not find expected localized error message.")
            print(full_out)
            sys.exit(1)
            
        if "MockTranslationProvider" in full_out:
            print("FAILED: MockTranslationProvider is still being invoked.")
            sys.exit(1)
            
        print("PASSED: Pipeline failed as expected without mock fallback, displaying localized error.")
        
    finally:
        if os.path.exists(backup_settings_path):
            shutil.copy2(backup_settings_path, settings_path)
            os.remove(backup_settings_path)
            
if __name__ == "__main__":
    test_translation_fallback()
