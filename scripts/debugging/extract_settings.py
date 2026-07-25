import os

def extract_settings():
    with open("desktop_app.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    start_idx = -1
    end_idx = -1
    for i, line in enumerate(lines):
        if line.startswith("class TestConnectionWorker(QThread):"):
            start_idx = i
        if line.startswith("class MainWindow(QMainWindow):"):
            end_idx = i
            break
            
    if start_idx != -1 and end_idx != -1:
        extracted = lines[start_idx:end_idx]
        with open("settings_code.txt", "w", encoding="utf-8") as f:
            f.writelines(extracted)
            
        print(f"Extracted {len(extracted)} lines.")
        
extract_settings()
