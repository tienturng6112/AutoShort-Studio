import os
import sys
import re

def main():
    print("Running Architecture Guard checks...")
    failed = False
    
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
    
    # 1. Prohibited imports pattern
    # Detects: import backend.providers or from backend.providers
    import_pattern = re.compile(r'^\s*(import\s+backend\.providers|from\s+backend\.providers\b)')
    
    # 2. Prohibited instantiations of managers or providers in UI layer
    instantiation_pattern = re.compile(
        r'\b('
        r'DeepLTranslationProvider|'
        r'ChatAnywhereTranslationProvider|'
        r'GeminiTranslationProvider|'
        r'GoogleTranslationProvider|'
        r'GeminiSpeechProvider|'
        r'KiraProvider|'
        r'ElevenLabsProvider|'
        r'EdgeTTSProvider|'
        r'OmniVoiceProvider|'
        r'ChatAnywhereProvider|'
        r'GeminiLLMProvider|'
        r'OpenAILLMProvider|'
        r'ClaudeLLMProvider|'
        r'LLMProviderManager|'
        r'TranslationProviderManager|'
        r'SpeechProviderManager'
        r')\s*\('
    )
    
    ui_dir = os.path.join(frontend_dir, "ui")
    
    for root, dirs, files in os.walk(frontend_dir):
        is_ui_file = root.startswith(ui_dir)
        for file in files:
            if not file.endswith(".py"):
                continue
                
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, frontend_dir)
            
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            for idx, line in enumerate(lines, 1):
                # Check for backend.providers imports in any frontend file
                if import_pattern.search(line):
                    print(f"ERROR: [Import Violation] {rel_path}:{idx} imports backend.providers directly.")
                    print(f"  Line: {line.strip()}")
                    failed = True
                    
                # Check for direct manager/provider instantiation in UI files
                if is_ui_file and instantiation_pattern.search(line):
                    print(f"ERROR: [Instantiation Violation] {rel_path}:{idx} instantiates a provider or provider manager directly.")
                    print(f"  Line: {line.strip()}")
                    failed = True
                    
    if failed:
        print("Architecture Guard FAILED.")
        sys.exit(1)
    else:
        print("Architecture Guard PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    main()
