import os
import json
import logging

logger = logging.getLogger("RuntimeAudit")

def audit_settings_window(window) -> dict:
    """Audits the provider state synchronization across settings.json, state, UI widgets, and service manager."""
    report = {
        "translation": {
            "success": True,
            "saved": None,
            "state": None,
            "combo": None,
            "stacked": None,
            "resolved": None,
            "errors": []
        },
        "speech": {
            "success": True,
            "saved": None,
            "state": None,
            "combo": None,
            "stacked": None,
            "resolved": None,
            "errors": []
        }
    }
    
    settings_path = os.path.join("config", "settings.json")
    saved_data = {}
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read settings.json for audit: {e}")

    # ==================== TRANSLATION AUDIT ====================
    try:
        saved_trans = saved_data.get("translation_provider", "chatanywhere").lower()
        state_trans = window._state.translation_provider.lower()
        combo_trans = window.provider_combo.currentText().lower()
        
        # Determine stacked widget matching key
        curr_widget = window.trans_stack.currentWidget()
        stacked_trans = None
        for k, w in window.trans_widgets.items():
            if w == curr_widget:
                stacked_trans = k.lower()
                break
                
        # Resolve via facade service (triggers lazy loading + cache)
        provider_instance = window._translation_svc.get(state_trans)
        resolved_trans = state_trans if provider_instance is not None else None
        
        report["translation"].update({
            "saved": saved_trans,
            "state": state_trans,
            "combo": combo_trans,
            "stacked": stacked_trans,
            "resolved": resolved_trans
        })
        
        # Check alignment
        mismatches = []
        if saved_trans != state_trans:
            mismatches.append(f"Saved ({saved_trans}) != State ({state_trans})")
        if state_trans != combo_trans:
            mismatches.append(f"State ({state_trans}) != ComboBox ({combo_trans})")
        if state_trans != stacked_trans:
            mismatches.append(f"State ({state_trans}) != StackedWidget ({stacked_trans})")
        if state_trans != resolved_trans:
            mismatches.append(f"State ({state_trans}) != Resolved in Manager ({resolved_trans})")
            
        if mismatches:
            report["translation"]["success"] = False
            report["translation"]["errors"] = mismatches
            
    except Exception as e:
        report["translation"]["success"] = False
        report["translation"]["errors"].append(f"Audit execution error: {e}")

    # ==================== SPEECH AUDIT ====================
    try:
        saved_speech = saved_data.get("speech_provider", saved_data.get("tts_provider", "edge")).lower()
        if "edge" in saved_speech:
            saved_speech = "edge"
        elif "elevenlabs" in saved_speech:
            saved_speech = "elevenlabs"
            
        state_speech = window._state.speech_provider.lower()
        
        combo_text = window.tts_provider_combo.currentText()
        combo_mapping = {
            "ElevenLabs": "elevenlabs",
            "Edge TTS": "edge"
        }
        combo_speech = combo_mapping.get(combo_text, "edge").lower()
        
        curr_speech_widget = window.speech_stacked_widget.currentWidget()
        stacked_speech = None
        for k, w in window.speech_widgets.items():
            if w == curr_speech_widget:
                stacked_speech = k.lower()
                break
                
        # Resolve via facade service (triggers lazy loading + cache)
        speech_instance = window._speech_svc.get(state_speech)
        resolved_speech = state_speech if speech_instance is not None else None
        
        report["speech"].update({
            "saved": saved_speech,
            "state": state_speech,
            "combo": combo_speech,
            "stacked": stacked_speech,
            "resolved": resolved_speech
        })
        
        mismatches_speech = []
        if saved_speech != state_speech:
            mismatches_speech.append(f"Saved ({saved_speech}) != State ({state_speech})")
        if state_speech != combo_speech:
            mismatches_speech.append(f"State ({state_speech}) != ComboBox ({combo_speech})")
        if state_speech != stacked_speech:
            mismatches_speech.append(f"State ({state_speech}) != StackedWidget ({stacked_speech})")
        if state_speech != resolved_speech:
            mismatches_speech.append(f"State ({state_speech}) != Resolved in Manager ({resolved_speech})")
            
        if mismatches_speech:
            report["speech"]["success"] = False
            report["speech"]["errors"] = mismatches_speech
            
    except Exception as e:
        report["speech"]["success"] = False
        report["speech"]["errors"].append(f"Audit execution error: {e}")
        
    return report
