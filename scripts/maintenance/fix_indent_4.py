with open('backend/run_pipeline.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 722 <= i <= 800:
        if line.startswith('        ') and not line.startswith('            '):
            if line.strip() and line.strip() != 'else:':
                lines[i] = '        ' + line

with open('backend/run_pipeline.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
