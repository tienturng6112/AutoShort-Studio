import re
with open('frontend/ui/settings_window.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_update = '''    def update_tts_ui_state(self):
        provider_id = self.tts_provider_combo.currentText()
        
        has_speed = self.cap_mgr.supports(provider_id, "tts", "speed_control")
        if hasattr(self, 'kira_speed_edit'):
            self.kira_speed_edit.setEnabled(has_speed)
            
        if hasattr(self, 'kira_group'):
            self.kira_group.setVisible("Kira" in provider_id)
        if hasattr(self, 'elevenlabs_group'):
            self.elevenlabs_group.setVisible("ElevenLabs" in provider_id)
        if hasattr(self, 'edge_tts_group'):
            self.edge_tts_group.setVisible("Edge TTS" in provider_id)'''

new_update = '''    def update_tts_ui_state(self):
        provider_id = self.tts_provider_combo.currentText()
        
        has_speed = self.cap_mgr.supports(provider_id, "tts", "speed_control")
        if hasattr(self, 'kira_speed_edit'):
            self.kira_speed_edit.setEnabled(has_speed)
            
        if "Edge TTS" in provider_id and hasattr(self, 'edge_tts_group'):
            self.speech_stacked_widget.setCurrentWidget(self.edge_tts_group)
        elif "Gemini Speech" in provider_id and hasattr(self, 'gemini_speech_widget'):
            self.speech_stacked_widget.setCurrentWidget(self.gemini_speech_widget)
        elif "ElevenLabs" in provider_id and hasattr(self, 'elevenlabs_group'):
            self.speech_stacked_widget.setCurrentWidget(self.elevenlabs_group)
        elif "Kira" in provider_id and hasattr(self, 'kira_group'):
            self.speech_stacked_widget.setCurrentWidget(self.kira_group)
        elif "OmniVoice" in provider_id and hasattr(self, 'omnivoice_group'):
            self.speech_stacked_widget.setCurrentWidget(self.omnivoice_group)'''
            
text = text.replace(old_update, new_update)

with open('frontend/ui/settings_window.py', 'w', encoding='utf-8') as f:
    f.write(text)
