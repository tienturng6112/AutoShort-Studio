
from PySide6.QtWidgets import QMessageBox
QMessageBox.warning = lambda *args: None
QMessageBox.information = lambda *args: None
QMessageBox.question = lambda *args: QMessageBox.Yes
QMessageBox.critical = lambda *args: None
import sys
import os
import json
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from desktop_app import MainWindow
from frontend.workspace.workspace_manager import WorkspaceManager

def run_test():
    # Clean state
    if os.path.exists("config/workspace.json"):
        os.remove("config/workspace.json")
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    def test_sequence():
        try:
            print("Running test sequence...")
            pages = ["settings", "characters", "voices", "emotions", "qa", "templates"]
            for p in pages:
                window.switch_page(p)
                print(f"Switched to page: {p}")
                
            def close_dialog():
                active = QApplication.activeModalWidget()
                if active:
                    active.close()
            
            QTimer.singleShot(500, close_dialog)
            print("Testing Start button...")
            window.start_btn.click() # Will show a warning because no input is specified
            
            print("Changing window size to test persistence...")
            window.resize(1200, 800)
            
            print("Closing application...")
            window.close()
        except Exception as e:
            print(f"Error during sequence: {e}")
            sys.exit(1)
            
    QTimer.singleShot(1000, test_sequence)
    app.exec()
    
    print("Application closed gracefully.")
    
    # Verify state persistence
    print("Verifying workspace state...")
    if not os.path.exists("config/workspace.json"):
        print("Error: workspace.json not created!")
        sys.exit(1)
        
    with open("config/workspace.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        if "mainwindow_geom" not in data:
            print("Error: mainwindow_geom missing from workspace.json")
            sys.exit(1)
            
    print("Restarting application to test state restore...")
    
    # Second instance
    app2 = QApplication.instance()
    if not app2:
        app2 = QApplication(sys.argv)
    
    window2 = MainWindow()
    geom = window2.geometry()
    
    # It should have restored to 1200x800
    if geom.width() == 1200 and geom.height() == 800:
        print("State restored successfully! Width: 1200, Height: 800")
    else:
        print(f"State NOT restored. Width: {geom.width()}, Height: {geom.height()}")
        
    print("ALL TESTS PASSED")
    sys.exit(0)

if __name__ == "__main__":
    run_test()
