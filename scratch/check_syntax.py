import ast
import sys

with open('frontend/ui/settings_window.py', encoding='utf-8') as f:
    source = f.read()

try:
    ast.parse(source)
    print("SYNTAX OK")
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")
    sys.exit(1)