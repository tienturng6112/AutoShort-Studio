import os
import subprocess
import tempfile
import shutil
import sys

def create_dummy_srt(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("1\n00:00:00,000 --> 00:00:01,000\nTest\n")

def test_ffmpeg_subtitles():
    print("--- Running FFmpeg Path Escaping Regression Tests ---")
    
    workspace = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    test_dir = os.path.join(workspace, "temp", "ffmpeg_tests")
    os.makedirs(test_dir, exist_ok=True)
    
    # Generate a dummy 1 second black video
    dummy_vid = os.path.join(test_dir, "dummy.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=640x360:d=1", "-c:v", "libx264", dummy_vid], capture_output=True, check=True)
    
    test_cases = [
        {"name": "Relative paths", "path": "temp/ffmpeg_tests/rel_path.srt"},
        {"name": "Absolute Windows paths", "path": os.path.join(test_dir, "abs_path.srt")},
        {"name": "Spaces in paths", "path": os.path.join(test_dir, "folder with spaces", "sub.srt")},
        {"name": "Unicode paths", "path": os.path.join(test_dir, "folder_🌟", "sub.srt")},
        {"name": "Chinese filenames", "path": os.path.join(test_dir, "中文测试.srt")},
        {"name": "Vietnamese filenames", "path": os.path.join(test_dir, "tiếng_việt.srt")}
    ]
    
    failed = 0
    for i, case in enumerate(test_cases):
        srt_path = case["path"]
        # Ensure it's absolute if not explicitly relative test
        if "rel_path" not in srt_path and not os.path.isabs(srt_path):
            srt_path = os.path.abspath(srt_path)
            
        create_dummy_srt(srt_path)
        
        # Apply the escaping fix
        sub_path_fw = srt_path.replace("\\", "/").replace(":", "\\:")
        
        out_vid = os.path.join(test_dir, f"out_{i}.mp4")
        if os.path.exists(out_vid):
            os.remove(out_vid)
            
        cmd = [
            "ffmpeg", "-y",
            "-i", dummy_vid,
            "-c:v", "libx264",
            "-vf", f"subtitles='{sub_path_fw}'",
            out_vid
        ]
        
        try:
            cwd_path = workspace if "rel_path" in srt_path else None
            result = subprocess.run(cmd, capture_output=True, cwd=cwd_path)
            if result.returncode != 0:
                print(f"FAILED [{case['name']}]: {result.stderr.decode('utf-8', errors='replace')}")
                failed += 1
            else:
                if not os.path.exists(out_vid):
                    print(f"FAILED [{case['name']}]: Output video not generated.")
                    failed += 1
                else:
                    print(f"PASSED [{case['name']}]")
        except Exception as e:
            print(f"FAILED [{case['name']}]: Exception {e}")
            failed += 1
            
    if failed == 0:
        print("All regression tests passed successfully!")
    else:
        print(f"{failed} tests failed.")
        sys.exit(1)

if __name__ == "__main__":
    test_ffmpeg_subtitles()
