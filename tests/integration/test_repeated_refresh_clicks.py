import sys
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QCoreApplication

# Initialize QApplication before any QWidgets
app = QApplication.instance() or QApplication(sys.argv)

from frontend.ui.settings_window import SettingsWindow

def test_repeated_refresh_clicks():
    window = SettingsWindow()
    
    # Switch to Kira
    window._state.speech_provider = "kira"
    
    # Trigger refresh
    window._refresh_speech_voices("kira", window.kira_group)
    worker1 = window._sv_worker
    assert worker1 is not None
    assert worker1.isRunning()
    
    # Wait for the worker to finish so we don't leak threads
    while worker1.isRunning():
        QCoreApplication.processEvents()
        
    assert not worker1.isRunning()
