import sys

with open('backend/run_pipeline.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if line.strip() == '# 6. Voice Synthesis':
        skip = True
        new_lines.append(line)
        
        # Insert the correct block
        correct_block = """        tts_bench = None
        if not skip_tts:
            logger.info("Stage 6: Voice Synthesis started.")
            state_manager.update_execution_state("Running", progress=75, current_stage="Stage 6: Voice Synthesis")

            render_dir = os.path.join(project_dir, "render")
            tts_dir = os.path.join(project_dir, "tts")
            os.makedirs(render_dir, exist_ok=True)
            os.makedirs(tts_dir, exist_ok=True)

            if not state_manager.is_completed("stage_6"):
                if "settings" not in locals() or not settings:
                    settings_path = os.path.join("config", "settings.json")
                    settings = {}
                    if os.path.exists(settings_path):
                        try:
                            with open(settings_path, "r", encoding="utf-8") as f:
                                settings = json.load(f)
                        except Exception as e:
                            logger.warning(f"Could not load settings.json in Stage 6: {str(e)}")
                            
                tts_type = settings.get("speech_provider", "edge").lower()
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

                voice_cache = VoiceCache(cache_dir=os.path.join(project_dir, "cache", "voice_cache"))
                voice_service = VoiceService(tts_provider, voice_cache, temp_dir=os.path.join(project_dir, "cache"))

                # Use VoiceManager to get voices
                from backend.voice.voice_manager import VoiceManager
                voice_manager = VoiceManager(cap_mgr, os.path.join(project_dir, "config", "voice_cache.json"))

                # We need to run refresh in the current event loop since run_pipeline is async
                await voice_manager.refresh(tts_type)

                target_lang = aligned_transcript.language.lower() if aligned_transcript.language else args.target_language.lower()
                voice_name = "en-US-GuyNeural"

                try:
                    lang_prefix = target_lang.split("-")[0] if target_lang else "en"
                    voices = voice_manager.list_voices(provider_id=tts_type)
                    target_voices = [v for v in voices if lang_prefix in v.language]
                    if target_voices:
                        voice_name = target_voices[0].name
                except Exception as e:
                    logger.warning(f"Failed to fetch voices: {e}")

                aligned_transcript, voice_wav_dest, voice_mp3_dest = await voice_service.generate_voice(
                    transcript=aligned_transcript,
                    voice_name=voice_name,
                    output_dir=tts_dir
                )

                # Diarization
                if args.diarize:
                    logger.info("Stage 6.5: Voice Diarization.")
                    aligned_transcript = await diarization_service.diarize(
                        aligned_transcript, voice_wav_dest, tts_dir)

                logger.info("Voice synthesis completed")
                state_manager.mark_completed("stage_6")
            else:
                logger.info("Stage 6: Skipped (Already completed).")
                with open(os.path.join(tts_dir, "aligned_transcript.json"), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    aligned_transcript = Transcript(**data)
        else:
            logger.info("Stage 6: Voice Synthesis skipped (Subtitle Only mode).")
"""
        new_lines.append(correct_block)
        continue
        
    if line.strip() == '# 7. Compose Final Video':
        skip = False
        
    if not skip:
        new_lines.append(line)

with open('backend/run_pipeline.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
