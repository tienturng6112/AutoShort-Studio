with open('backend/run_pipeline.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_tts_block = False
for i, line in enumerate(lines):
    if line.strip() == 'if not args.subtitle_only:':
        in_tts_block = True
    elif line.strip() == 'logger.info("Stage 7: Exporting results.")':
        in_tts_block = False
        
    if in_tts_block and i > 615:
        if line.startswith('                '):
            lines[i] = line.replace('                ', '            ', 1)
        elif line.startswith('        ') and not line.startswith('            '):
            if line.strip() != 'if not args.subtitle_only:':
                lines[i] = '    ' + line
            
with open('backend/run_pipeline.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
