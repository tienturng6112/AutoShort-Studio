import os
import sys

workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, workspace_root)

def validate_imports():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Import core components
    print("Testing desktop_app.py...")
    import desktop_app
    
    print("Testing run_pipeline.py...")
    import backend.run_pipeline
    
    print("Testing recovery_dialog.py...")
    import frontend.dialogs.recovery_dialog
    
    print("Testing project_manager_dialog.py...")
    import frontend.dialogs.project_manager_dialog
    
    print("Testing queue service...")
    import backend.services.queue_service
    
    print("Testing pipeline state manager...")
    import backend.services.pipeline_state_manager

    print("ALL IMPORTS PASSED SUCCESSFULLY.")

if __name__ == "__main__":
    try:
        validate_imports()
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)
