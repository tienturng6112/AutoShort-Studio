import os
import sys
import re
from typing import List, Dict

def audit_imports(root_dir: str) -> List[str]:
    print(f"Auditing imports in {root_dir}...")
    errors = []
    
    # Define rules
    legacy_import_patterns = [
        re.compile(r'from backend\.translation\.chatanywhere'),
        re.compile(r'from backend\.translation\.deepl'),
        re.compile(r'from backend\.providers\.chatanywhere'),
        re.compile(r'from backend\.providers\.deepl'),
        re.compile(r'from backend\.tts\.elevenlabs_provider'),
        re.compile(r'from backend\.tts\.gemini_provider')
    ]
    
    direct_provider_patterns = [
        re.compile(r'ChatAnywhereProvider\s*\('),
        re.compile(r'DeepLTranslationProvider\s*\('),
        re.compile(r'GeminiSpeechProvider\s*\('),
        re.compile(r'ElevenLabsProvider\s*\(')
    ]
    
    direct_manager_patterns = [
        re.compile(r'TranslationProviderManager\s*\('),
        re.compile(r'SpeechProviderManager\s*\('),
        re.compile(r'LLMProviderManager\s*\(')
    ]
    
    exclude_dirs = {'.git', '.vscode', '__pycache__', 'venv', 'env', 'projects', 'scripts'}
    allowed_manager_files = {'manager.py', 'llm_service.py', 'speech_facade_service.py', 'translation_facade_service.py', 'run_pipeline.py', 'desktop_app.py', 'test_regression_suite.py'}
    
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if not any(ex in os.path.join(root, d).replace('\\', '/') for ex in exclude_dirs)]
        
        for file in files:
            if not file.endswith(".py"):
                continue
                
            filepath = os.path.join(root, file)
            is_ui = "frontend/ui" in filepath.replace('\\', '/')
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    for i, line in enumerate(lines):
                        line_num = i + 1
                        
                        # Rule 1: Legacy imports
                        for p in legacy_import_patterns:
                            if p.search(line):
                                errors.append(f"{filepath}:{line_num}: Legacy import detected: {line.strip()}")
                                
                        # Rule 2: Direct provider instantiations in UI
                        if is_ui:
                            for p in direct_provider_patterns:
                                if p.search(line):
                                    errors.append(f"{filepath}:{line_num}: Direct provider instantiation in UI: {line.strip()}")
                                    
                        # Rule 3: Direct manager instantiations
                        if file not in allowed_manager_files:
                            for p in direct_manager_patterns:
                                if p.search(line) and not "class " in line and not "def " in line:
                                    errors.append(f"{filepath}:{line_num}: Direct manager instantiation outside allowed files: {line.strip()}")
            
            except Exception as e:
                errors.append(f"Could not read {filepath}: {e}")
                
    return errors

if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    errors = audit_imports(project_root)
    
    if errors:
        print("\nIMPORT AUDIT FAILED:")
        for err in errors:
            print(f"- {err}")
        sys.exit(1)
    else:
        print("\nImport audit passed successfully. No legacy or duplicate instantiations detected.")
        sys.exit(0)
