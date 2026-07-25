import re
with open('backend/run_pipeline.py', 'r', encoding='utf-8') as f:
    text = f.read()

match = re.search(r'if not args\.subtitle_only:(.*?)logger\.info\("Stage 7: Exporting results\."\)', text, re.DOTALL)
if match:
    with open('bad_block.txt', 'w', encoding='utf-8') as out:
        out.write("if not args.subtitle_only:" + match.group(1))
