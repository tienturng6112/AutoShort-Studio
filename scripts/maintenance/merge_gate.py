import os
import sys
import subprocess

def run_script(script_path: str) -> bool:
    print(f"\n{'='*50}\nRunning {os.path.basename(script_path)}...\n{'='*50}")
    result = subprocess.run([sys.executable, script_path], cwd=os.path.dirname(os.path.dirname(os.path.dirname(script_path))))
    return result.returncode == 0

def main():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    scripts = [
        os.path.join(project_root, "scripts", "maintenance", "compile_check.py"),
        os.path.join(project_root, "scripts", "maintenance", "import_audit.py"),
        os.path.join(project_root, "scripts", "maintenance", "architecture_guard.py")
    ]
    
    for script in scripts:
        if not os.path.exists(script):
            print(f"ERROR: Required gate script not found: {script}")
            sys.exit(1)
            
        success = run_script(script)
        if not success:
            print(f"\n[MERGE GATE REJECTED] Validation failed at {os.path.basename(script)}")
            sys.exit(1)
            
    print("\n" + "="*50)
    print("[MERGE GATE PASSED] All validation checks completed successfully.")
    print("="*50)
    sys.exit(0)

if __name__ == "__main__":
    main()
