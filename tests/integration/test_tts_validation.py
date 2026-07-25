import os
import sys
import asyncio
import pytest

from backend.tts.kira_provider import KiraProvider

@pytest.mark.asyncio
async def test_tts_error_translator_401():
    print("--- Running TTS Error Translator Regression Test (401) ---")
    provider = KiraProvider(api_key="sk-invalid-test-key", model="kira-3.0-flash-tts")
    
    output_path = "temp_test_tts_output.wav"
    try:
        await provider.generate("Hello", "aoede", output_path)
        print("FAILED: Expected an exception due to invalid API key, but succeeded.")
        sys.exit(1)
    except RuntimeError as e:
        error_msg = str(e)
        if "Lỗi TTS: API Key không hợp lệ" not in error_msg:
            print(f"FAILED: Did not find friendly 401 error message. Got: {error_msg}")
            sys.exit(1)
        
        if "{" in error_msg and "}" in error_msg:
            print(f"FAILED: Exception message contains raw JSON. Got: {error_msg}")
            sys.exit(1)
            
        print("PASSED: 401 correctly translated to friendly message without raw JSON.")
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)

if __name__ == "__main__":
    asyncio.run(test_tts_error_translator_401())
