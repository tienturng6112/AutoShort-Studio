import re

with open('frontend/ui/settings_window.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith('                                    with open(ov_path, "r", encoding="utf-8") as f:'):
        new_lines.append(line.replace('                                    with open', '                                with open'))
    elif line.startswith('                        with open(ov_path, "w", encoding="utf-8") as f:'):
        new_lines.append(line.replace('                        with open', '                    with open'))
    else:
        new_lines.append(line)

with open('frontend/ui/settings_window.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
