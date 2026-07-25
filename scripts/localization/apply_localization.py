import codecs
import re
import os

replacements = {
    # window_tools
    '"Tools"': 'loc.translate("window_tools")',
    
    # settings_window
    '"Settings"': 'loc.translate("settings")',
    '"Interface Language:"': 'loc.translate("interface_language") + ":"',
    '"General"': 'loc.translate("interface_section")',
    '"Translation Provider:"': 'loc.translate("translation_provider") + ":"',
    '"API Key:"': 'loc.translate("api_key") + ":"',
    '"Base URL:"': 'loc.translate("base_url") + ":"',
    '"Model Name:"': 'loc.translate("model_name") + ":"',
    '"TTS Provider:"': 'loc.translate("tts_provider") + ":"',
    '"Refresh Models"': 'loc.translate("refresh_models")',
    '"Test Connection"': 'loc.translate("test_connection")',
    '"Speed (0.25-4.0):"': 'loc.translate("speed") + ":"',
    '"Save Settings"': 'loc.translate("save_settings")',
    '"Cancel"': 'loc.translate("cancel")',
    '"Translation"': 'loc.translate("stage_4").split(":")[0]',
    '"Voice"': 'loc.translate("speaker_voices")',
    '"Edge TTS"': '"Edge TTS"',
    '"ElevenLabs"': '"ElevenLabs"',
    '"Kira"': '"Kira"',
    '"Status: Ready"': 'loc.translate("status_idle")',
    '"Status: Missing API Key"': 'loc.translate("status_needs_api_key")',
    '"Status: Not Configured"': 'loc.translate("status_configured")',
    '"Status: Unavailable"': 'loc.translate("status_unavailable")',
    
    # character_browser
    '"Character Browser"': 'loc.translate("character_browser")',
    '"New Character"': 'loc.translate("btn_new_character")',
    '"Edit Profile"': 'loc.translate("btn_edit_profile")',
    '"Assign Voice"': 'loc.translate("assign_voice")',
    '"Delete"': 'loc.translate("btn_delete")',
    
    # voice_browser
    '"Voice Browser"': 'loc.translate("voice_browser")',
    '"Play Preview"': 'loc.translate("btn_play_preview")',
    '"Assign Selected"': 'loc.translate("btn_assign_selected")',
    '"Provider:"': 'loc.translate("lbl_provider")',
    '"Gender:"': 'loc.translate("lbl_gender")',
    
    # emotion_editor
    '"Emotion Editor"': 'loc.translate("emotion_editor")',
    '"Emotion:"': 'loc.translate("lbl_emotion")',
    '"Intensity:"': 'loc.translate("lbl_intensity")',
    '"Apply Override"': 'loc.translate("btn_apply_override")',
    
    # qa_dashboard
    '"QA Dashboard"': 'loc.translate("qa_dashboard")',
    '"Loading QA Report..."': 'loc.translate("msg_loading_qa")',
    '"No QA Report found."': 'loc.translate("msg_no_qa_report")',
    '"Mark Approved"': 'loc.translate("btn_mark_approved")',
    
    # template_browser
    '"Template Browser"': 'loc.translate("template_browser")',
    '"Template & Workflow Browser"': 'loc.translate("template_browser")',
    '"Select a template"': 'loc.translate("placeholder_select_template")',
    '"Use Template"': 'loc.translate("btn_use_template")',
    
    # provider_diagnostics
    '"Provider Diagnostics"': 'loc.translate("provider_diagnostics")',
    '"Real-time view of registered AI Providers and their capability status."': 'loc.translate("desc_diagnostics")',
    '"Open / Configure"': 'loc.translate("btn_open_configure")',
    
    # translation_review
    '"Translation Review"': 'loc.translate("translation_review")',
    '"Translation Memory (Auto-syncs with Review edits)"': 'loc.translate("desc_translation_memory")',
    '"Save All Changes"': 'loc.translate("btn_save_all_changes")',
    '"Source:"': 'loc.translate("lbl_source")',
    '"Target:"': 'loc.translate("lbl_target")',
    
    # other
    '"Extracting audio..."': 'loc.translate("msg_extracting_audio")',
    '"Transcribing..."': 'loc.translate("msg_transcribing")',
    '"Translating..."': 'loc.translate("msg_translating")',
    '"Synthesizing voice..."': 'loc.translate("msg_synthesizing")',
    '"Stitching final video..."': 'loc.translate("msg_stitching")',
    '"Failed"': 'loc.translate("msg_failed")',
    '"Finished Successfully"': 'loc.translate("msg_finished_successfully")',
    '"Ready"': 'loc.translate("lbl_ready")',
    '"Resume Pipeline"': 'loc.translate("btn_resume_pipeline")',
    '"Force Refresh"': 'loc.translate("btn_force_refresh")',
    '"Queue Status: Paused"': 'loc.translate("status_queue_paused")',
    '"Queue Status: Running"': 'loc.translate("status_queue_running")',
    '"Pause Queue"': 'loc.translate("btn_pause_queue")',
    '"Resume Queue"': 'loc.translate("btn_resume_queue")',
    '"Queue for Processing"': 'loc.translate("btn_queue_for_processing")',
    '"Remove from Queue (Dequeue)"': 'loc.translate("btn_remove_from_queue")',
    '"Toggle Freeze"': 'loc.translate("btn_toggle_freeze")'
}

def localize_file(filepath):
    if not os.path.exists(filepath):
        return
        
    with codecs.open(filepath, 'r', 'utf-8') as f:
        content = f.read()
        
    if 'from backend.services.localization_service import LocalizationService' not in content:
        content = 'from backend.services.localization_service import LocalizationService\n' + content
        
    # We will inject loc = LocalizationService() if not present inside def init_ui
    if 'loc = LocalizationService()' not in content and 'def init_ui' in content:
        content = content.replace('def init_ui(self):', 'def init_ui(self):\n        loc = LocalizationService()')
    elif 'loc = LocalizationService()' not in content and 'def __init__' in content:
        content = content.replace('def __init__', 'def __init__') # wait, need correct indentation
        # better to just do it via regex
        pass

    for k, v in replacements.items():
        # Avoid replacing inside loc.translate already
        if f'loc.translate({k})' in content or v in content:
            continue
        content = content.replace(k, v)
        
    with codecs.open(filepath, 'w', 'utf-8') as f:
        f.write(content)
        
files = [
    'desktop_app.py',
    'frontend/ui/settings_window.py',
    'frontend/ui/character_browser_window.py',
    'frontend/ui/voice_browser_window.py',
    'frontend/ui/emotion_editor_window.py',
    'frontend/ui/qa_dashboard_window.py',
    'frontend/ui/template_browser_window.py',
    'frontend/ui/provider_diagnostics_window.py',
    'frontend/ui/translation_review_window.py',
    'frontend/dialogs/project_manager_dialog.py',
    'frontend/dialogs/recovery_dialog.py'
]

for f in files:
    localize_file(f)

print("Localization applied!")
