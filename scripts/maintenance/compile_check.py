import os
import sys
import py_compile
from typing import List

def check_compilation(root_dir: str) -> List[str]:
    print(f"Checking compilation in {root_dir}...")
    errors = []
    
    # Exclude directories that shouldn't be compiled
    exclude_dirs = {'.git', '.vscode', '__pycache__', 'venv', 'env', 'projects', 'scripts/archive', 'scripts/build'}
    
    for root, dirs, files in os.walk(root_dir):
        # Modify dirs in-place to skip excluded directories
        dirs[:] = [d for d in dirs if not any(ex in os.path.join(root, d).replace('\\', '/') for ex in exclude_dirs)]
        
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                try:
                    py_compile.compile(filepath, doraise=True)
                except py_compile.PyCompileError as e:
                    errors.append(f"Compilation error in {filepath}:\n{e}")
                except Exception as e:
                    errors.append(f"Unexpected error compiling {filepath}: {e}")
                    
    return errors

if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    errors = check_compilation(project_root)
    
    if errors:
        print("\nCOMPILATION FAILED:")
        for err in errors:
            print(f"- {err}")
        sys.exit(1)
    else:
        print("\nAll files compiled successfully. No syntax errors detected.")
        sys.exit(0)
