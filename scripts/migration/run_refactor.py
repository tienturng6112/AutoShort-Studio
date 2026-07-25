import os
import shutil
import glob

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

# 1. Create target directories
dirs = [
    'scripts/archive', 'scripts/maintenance', 'scripts/patches',
    'scripts/debugging', 'scripts/localization', 'scripts/migration',
    'scripts/build', 'docs/debug', 'data/voices', 'data/videos'
]
for d in dirs:
    ensure_dir(d)

def move_files(pattern, dest):
    for f in glob.glob(pattern):
        if os.path.isfile(f):
            dest_file = os.path.join(dest, os.path.basename(f))
            if os.path.exists(dest_file):
                os.remove(dest_file)
            shutil.move(f, dest)

# 2. Archive scripts
move_files('desktop_app_*.py', 'scripts/archive/')
move_files('stage7_recovered.py', 'scripts/archive/')

# 3. Maintenance
move_files('fix_*.py', 'scripts/maintenance/')

# 4. Patches
move_files('patch_*.py', 'scripts/patches/')
move_files('patch2.py', 'scripts/patches/')

# 5. Debugging
move_files('extract*.py', 'scripts/debugging/')
move_files('regression_test.py', 'scripts/debugging/')
move_files('search_keys.py', 'scripts/debugging/')
move_files('search_save.py', 'scripts/debugging/')
move_files('add_entry.py', 'scripts/debugging/')
move_files('missing_methods.py', 'scripts/debugging/')
move_files('refactor_pipeline.py', 'scripts/debugging/')
move_files('run_pipeline_decompiled.py', 'scripts/debugging/')

# 6. Localization
move_files('localize*.py', 'scripts/localization/')
move_files('apply_localization.py', 'scripts/localization/')
move_files('update_i18n.py', 'scripts/localization/')

# 7. Migration
move_files('inject*.py', 'scripts/migration/')

# 8. Build
move_files('build_settings.py', 'scripts/build/')

# 9. Debug Dumps
move_files('dump*.txt', 'docs/debug/')
move_files('init_ui_dump.txt', 'docs/debug/')
move_files('recovered.txt', 'docs/debug/')
move_files('settings_code.txt', 'docs/debug/')
move_files('speech_input.txt', 'docs/debug/')
move_files('desktop_app_missing_code.txt', 'docs/debug/')
move_files('desktop_app_recovered.txt', 'docs/debug/')
move_files('*.txt', 'docs/debug/') # wait, don't move requirements.txt!
# Let's restore requirements.txt if it got moved
if os.path.exists('docs/debug/requirements.txt'):
    shutil.move('docs/debug/requirements.txt', '.')

# 10. Data files
if os.path.exists('characters.json'):
    dest = 'data/characters.json'
    if os.path.exists(dest): os.remove(dest)
    shutil.move('characters.json', dest)

def move_dir_contents(src, dest):
    if os.path.exists(src):
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dest, item)
            if os.path.isdir(s):
                if not os.path.exists(d): shutil.move(s, dest)
            else:
                if not os.path.exists(d): shutil.move(s, dest)

move_dir_contents('voices', 'data/voices')
move_dir_contents('videos', 'data/videos')

if os.path.exists('voices') and not os.listdir('voices'): os.rmdir('voices')
if os.path.exists('videos') and not os.listdir('videos'): os.rmdir('videos')

print("Directory refactoring completed.")
