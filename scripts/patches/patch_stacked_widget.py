import re
with open('frontend/ui/settings_window.py', 'r', encoding='utf-8') as f:
    text = f.read()

if 'QStackedWidget' not in text:
    text = text.replace('from PySide6.QtWidgets import (', 'from PySide6.QtWidgets import (\n    QStackedWidget,')

# 1. Update tts_providers to EXACT order
old_tts_prov = '''        tts_providers = [p.provider_id for p in self.cap_mgr.registry.list_providers() if p.provider_type == "tts"]
        if not tts_providers: tts_providers = ["Edge TTS", "ElevenLabs", "Kira"]'''
new_tts_prov = '''        tts_providers = ["Edge TTS", "Gemini Speech", "ElevenLabs", "Kira", "OmniVoice (Experimental)"]'''
text = text.replace(old_tts_prov, new_tts_prov)

# 2. Add QStackedWidget to tab_prov
old_tab_prov = '''        # --- TAB: PROVIDERS ---
        self.tab_prov = QWidget()
        prov_layout = QVBoxLayout(self.tab_prov)'''
new_tab_prov = '''        # --- TAB: PROVIDERS ---
        self.tab_prov = QWidget()
        prov_layout = QVBoxLayout(self.tab_prov)
        self.speech_stacked_widget = QStackedWidget()
        prov_layout.addWidget(self.speech_stacked_widget)'''
text = text.replace(old_tab_prov, new_tab_prov)

# 3. Replace all prov_layout.addWidget(...) with speech_stacked_widget.addWidget(...)
text = text.replace('prov_layout.addWidget(self.kira_group)', 'self.speech_stacked_widget.addWidget(self.kira_group)')
text = text.replace('prov_layout.addWidget(self.gemini_speech_widget)', 'self.speech_stacked_widget.addWidget(self.gemini_speech_widget)')
text = text.replace('prov_layout.addWidget(self.elevenlabs_group)', 'self.speech_stacked_widget.addWidget(self.elevenlabs_group)')
text = text.replace('prov_layout.addWidget(self.edge_tts_group)', 'self.speech_stacked_widget.addWidget(self.edge_tts_group)')
text = text.replace('prov_layout.addWidget(self.omnivoice_group)', 'self.speech_stacked_widget.addWidget(self.omnivoice_group)')

with open('frontend/ui/settings_window.py', 'w', encoding='utf-8') as f:
    f.write(text)
