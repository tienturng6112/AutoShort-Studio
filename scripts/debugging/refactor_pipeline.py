import re
import sys

with open('backend/run_pipeline.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the syntax error at lines 800-802 first
syntax_error = '''        else:
            logger.info("Stage 6.5: Skipped (Already completed).")
        else:
            logger.info("Stage 6: Voice Synthesis skipped (Subtitle Only mode).")'''
fixed_syntax = '''        else:
            logger.info("Stage 6.5: Skipped (Already completed).")
    else:
        logger.info("Stage 6: Voice Synthesis skipped (Subtitle Only mode).")'''
text = text.replace(syntax_error, fixed_syntax)


# Refactor Providers
# Replace lines from `provider_type = settings.get("translation_provider", "ChatAnywhere")` to the end of `if translation_provider is None:`
block1_regex = r'provider_type = settings\.get\("translation_provider", "ChatAnywhere"\).*?if translation_provider is None:\s+error_msg = "Không có nhà cung cấp dịch thuật nào được cấu hình\. Vui lòng kiểm tra API Key\."\s+logger\.error\(error_msg\)\s+raise RuntimeError\(error_msg\)'

new_block1 = """# --- NEW PROVIDER ARCHITECTURE ---
            # 1. Initialize Managers
            from backend.providers.llm.manager import LLMProviderManager
            from backend.providers.translation.manager import TranslationProviderManager
            from backend.providers.speech.manager import SpeechProviderManager
            
            llm_manager = LLMProviderManager()
            trans_manager = TranslationProviderManager()
            speech_manager = SpeechProviderManager()
            
            # 2. Init LLM Provider
            llm_type = settings.get("llm_provider", "chatanywhere").lower()
            if llm_type == "chatanywhere":
                from backend.providers.llm.chatanywhere.chatanywhere_provider import ChatAnywhereProvider
                config = settings.get("providers", {}).get("chatanywhere", {})
                llm_prov = ChatAnywhereProvider("chatanywhere", config.get("api_key"), config.get("base_url"))
                llm_manager.register("chatanywhere", llm_prov)
            
            # Wrap LLM provider in LLMService
            from backend.services.llm_service import LLMService
            # We must create a mock manager for LLMService to stay compatible with existing code, 
            # or just pass the provider. LLMService expects a manager with get_active_provider().
            class LegacyLLMManagerAdapter:
                def __init__(self, p): self.p = p
                def get_active_provider(self): return self.p
            llm_service = LLMService(LegacyLLMManagerAdapter(llm_manager.get(llm_type)))
            
            # 3. Init Translation Provider
            trans_type = settings.get("translation_provider", "deepl").lower()
            translation_provider = None
            if trans_type == "deepl":
                from backend.providers.translation.deepl.deepl_provider import DeepLTranslationProvider
                config = settings.get("providers", {}).get("deepl", {})
                translation_provider = DeepLTranslationProvider(api_key=config.get("api_key"), context=transcript.text if transcript else None)
                trans_manager.register("deepl", translation_provider)
            elif trans_type == "chatanywhere":
                from backend.providers.translation.chatanywhere.chatanywhere_provider import ChatAnywhereTranslationProvider
                config = settings.get("providers", {}).get("chatanywhere", {})
                model = config.get("model", "gpt-4o-mini")
                translation_provider = ChatAnywhereTranslationProvider(llm_service, model=model)
                trans_manager.register("chatanywhere", translation_provider)
                
            if translation_provider is None:
                raise RuntimeError("No Translation provider configured.")
                
            provider_type = trans_type.capitalize()
            trans_cache = TranslationCache(cache_file_path=os.path.join(project_dir, "cache", "translation_cache.json"))
            glossary = GlossaryManager()
            state_file_path = os.path.join(project_dir, "cache", "translation_state.json")
"""

text = re.sub(block1_regex, new_block1, text, flags=re.DOTALL)

# Refactor ConversationAnalyzer (lines 439-450)
analyzer_regex = r'def build_conversation_analyzer\(translation_prov\):.*?if not api_key:\s+return None.*?return ConversationAnalyzerService\(llm_service, model=model\)'
new_analyzer = """def build_conversation_analyzer(translation_prov):
                use_analyzer = settings.get("use_conversation_analyzer", True)
                if not use_analyzer:
                    return None
                from backend.translation.conversation_analyzer import ConversationAnalyzerService
                if llm_manager.get(llm_type):
                    return ConversationAnalyzerService(llm_service, model=settings.get("providers", {}).get(llm_type, {}).get("model", "gpt-4o-mini"))
                return None"""
text = re.sub(analyzer_regex, new_analyzer, text, flags=re.DOTALL)

# Remove the ugly try/except fallback to ChatAnywhere around lines 510-520
fallback_regex = r'except Exception as e:\s+if provider_type == "DeepL":.*?if hasattr\(translation_service, "average_quality_score"\):\s+score = translation_service\.average_quality_score\s+print\(f"\[Fallback Translation Quality Score\] \{score:\.1f\}%", flush=True\)\s+else:\s+raise e'
new_fallback = """except Exception as e:
                raise e"""
text = re.sub(fallback_regex, new_fallback, text, flags=re.DOTALL)

# Refactor TTS instantiation (lines 666-674)
tts_regex = r'tts_type = settings\.get\("tts_provider", "Edge TTS"\).*?tts_provider = TTSProviderFactory\.create\(tts_type, settings\)'
new_tts = """tts_type = settings.get("speech_provider", "edge").lower()
        if tts_type == "gemini_tts":
            from backend.providers.speech.gemini_tts.gemini_tts_provider import GeminiTTSProvider
            config = settings.get("providers", {}).get("gemini_tts", {})
            tts_provider = GeminiTTSProvider(api_key=config.get("api_key"), cache_dir=os.path.join(project_dir, "cache", "speech"))
        elif tts_type == "elevenlabs":
            from backend.providers.speech.elevenlabs.kira_provider import KiraProvider
            config = settings.get("providers", {}).get("elevenlabs", {})
            tts_provider = KiraProvider(api_key=config.get("api_key"), model=config.get("model", "eleven_multilingual_v2"))
        else:
            from backend.providers.speech.edge.edge_tts_provider import EdgeTTSProvider
            tts_provider = EdgeTTSProvider()
            
        speech_manager.register(tts_type, tts_provider)
        """
text = re.sub(tts_regex, new_tts, text, flags=re.DOTALL)

with open('backend/run_pipeline.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("run_pipeline.py refactored successfully.")
