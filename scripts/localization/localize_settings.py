import re
import codecs

def localize_file(filepath):
    with codecs.open(filepath, 'r', 'utf-8') as f:
        content = f.read()
        
    replacements = {
        '"Settings"': 'loc.translate("settings")',
        '"Interface Language:"': 'loc.translate("interface_language") + ":"',
        '"General"': 'loc.translate("interface_section")',
        '"Translation Provider:"': 'loc.translate("translation_provider") + ":"',
        '"API Key:"': 'loc.translate("api_key") + ":"',
        '"Base URL (Optional):"': 'loc.translate("base_url") + ":"',
        '"Model Name:"': 'loc.translate("model_name") + ":"',
        '"TTS Provider:"': 'loc.translate("tts_provider") + ":"',
        '"Refresh Models"': 'loc.translate("refresh_models")',
        '"Test Connection"': 'loc.translate("test_connection")',
        '"Speed (0.25-4.0):"': 'loc.translate("speed") + ":"',
        '"Save Settings"': 'loc.translate("save_settings")',
        '"Cancel"': 'loc.translate("cancel")',
        '"Translation"': 'loc.translate("stage_4").split(":")[0]',
        '"Voices"': 'loc.translate("speaker_voices")',
        '"Edge TTS"': '"Edge TTS"',
        '"ElevenLabs"': '"ElevenLabs"',
        '"Kira"': '"Kira"',
        '"Status: Ready"': 'loc.translate("status_idle")',
        '"Status: Missing API Key"': 'loc.translate("status_needs_api_key")',
        '"Status: Not Configured"': 'loc.translate("status_configured")',
        '"Status: Unavailable"': 'loc.translate("status_unavailable")'
    }
    
    # We will inject loc = LocalizationService() if not present
    if 'loc = LocalizationService()' not in content and 'def init_ui' in content:
        content = content.replace('def init_ui(self):', 'def init_ui(self):\n        loc = LocalizationService()')
        
    for k, v in replacements.items():
        # Only replace if not already wrapped
        content = content.replace(k, v)
        
    with codecs.open(filepath, 'w', 'utf-8') as f:
        f.write(content)
        
localize_file('frontend/ui/settings_window.py')
print("Settings localized")
