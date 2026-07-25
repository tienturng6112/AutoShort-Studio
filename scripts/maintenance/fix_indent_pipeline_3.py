with open('backend/run_pipeline.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_tts = False
for line in lines:
    if line.strip() == 'if not args.subtitle_only:':
        in_tts = True
        new_lines.append(line)
        continue
    elif line.strip() == 'logger.info("Stage 7: Exporting results.")':
        in_tts = False
        new_lines.append(line)
        continue
        
    if in_tts and 'tts_type = settings.get("speech_provider"' in line:
        # Starting point of the bad indentation
        pass
    
    if in_tts:
        # We know exactly how it should be indented.
        # But this is brittle. The easiest way is to use autopep8 or similar, but since we don't have it,
        # we can just fix the specific lines.
        if line.startswith('tts_type = settings.get('):
            line = '            ' + line
        elif line.startswith('        if tts_type == "gemini_tts":'):
            line = '            ' + line.lstrip() + '\n'
        elif line.startswith('            from backend.providers.speech.gemini_tts'):
            line = '                ' + line.lstrip() + '\n'
        elif line.startswith('            config = settings.get'):
            line = '                ' + line.lstrip() + '\n'
        elif line.startswith('            tts_provider = GeminiTTSProvider'):
            line = '                ' + line.lstrip() + '\n'
        elif line.startswith('        elif tts_type == "elevenlabs":'):
            line = '            ' + line.lstrip() + '\n'
        elif line.startswith('            from backend.providers.speech.elevenlabs'):
            line = '                ' + line.lstrip() + '\n'
        elif line.startswith('            tts_provider = KiraProvider'):
            line = '                ' + line.lstrip() + '\n'
        elif line.startswith('        else:'):
            line = '            ' + line.lstrip() + '\n'
        elif line.startswith('            from backend.providers.speech.edge'):
            line = '                ' + line.lstrip() + '\n'
        elif line.startswith('            tts_provider = EdgeTTSProvider'):
            line = '                ' + line.lstrip() + '\n'
        elif line.startswith('        speech_manager.register'):
            line = '            ' + line.lstrip() + '\n'
        elif line.startswith('        voice_cache = '):
            line = '            ' + line.lstrip() + '\n'
        elif line.startswith('        voice_service = '):
            line = '            ' + line.lstrip() + '\n'
        elif line.startswith('        # Use VoiceManager'):
            line = '            ' + line.lstrip() + '\n'
        elif line.startswith('        from backend.voice.voice_manager'):
            line = '            ' + line.lstrip() + '\n'
        elif line.startswith('        voice_manager = '):
            line = '            ' + line.lstrip() + '\n'
        elif line.startswith('        # We need to run'):
            line = '            ' + line.lstrip() + '\n'
        elif line.startswith('        await voice_manager.refresh'):
            line = '            ' + line.lstrip() + '\n'
        elif line.startswith('                target_lang = '):
            line = '            ' + line.lstrip() + '\n'
        elif line.startswith('                voice_name = '):
            line = '            ' + line.lstrip() + '\n'
        elif line.startswith('                try:'):
            line = '            ' + line.lstrip() + '\n'
        elif line.startswith('                    lang_prefix = '):
            line = '                ' + line.lstrip() + '\n'
        elif line.startswith('                    voices = '):
            line = '                ' + line.lstrip() + '\n'
        elif line.startswith('                    target_voices = '):
            line = '                ' + line.lstrip() + '\n'
        elif line.startswith('                    if target_voices:'):
            line = '                ' + line.lstrip() + '\n'
        elif line.startswith('                        voice_name = '):
            line = '                    ' + line.lstrip() + '\n'
        elif line.startswith('                except Exception as e:'):
            line = '            ' + line.lstrip() + '\n'
        elif line.startswith('                    logger.warning'):
            line = '                ' + line.lstrip() + '\n'
        elif line.startswith('                aligned_transcript, voice_wav_dest, voice_mp3_dest = await voice_service.generate_voice'):
            line = '            ' + line.lstrip() + '\n'
        elif line.startswith('                # Diarization'):
            line = '            ' + line.lstrip() + '\n'
        elif line.startswith('                if args.diarize:'):
            line = '            ' + line.lstrip() + '\n'
        elif line.startswith('                    logger.info'):
            line = '                ' + line.lstrip() + '\n'
        elif line.startswith('                    aligned_transcript = await diarization_service.diarize'):
            line = '                ' + line.lstrip() + '\n'
        elif line.startswith('                logger.info("Voice synthesis completed")'):
            line = '            ' + line.lstrip() + '\n'
            
    new_lines.append(line)

with open('backend/run_pipeline.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
