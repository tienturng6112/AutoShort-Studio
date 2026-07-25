# Workspace Rules & Constraints

## Backend Pipeline Freeze
The core media backend pipeline is stable. Do NOT modify the following components unless a reproducible bug is explicitly reported:
- Media pipeline execution driver
- FFmpeg parameters or wrappers
- Metadata extraction (`MetadataExtractor`)
- Subtitle rendering modules
- Composition & stitching drivers
- Audio extraction (`AudioExtractor`)

## Permitted Focus Areas
Future development and tasks must focus strictly on:
1. **ChatAnywhere integration** (translation client backend / api keys)
2. **Speech Recognition** (Whisper integration and speech providers)
3. **Translation providers** (LLM providers / translations)
4. **TTS providers** (voice generation engines)
5. **Desktop UX** (PySide6 application GUI layout, behaviors, and components)
6. **Packaging** (bundling, distributing, and deployment scripts)

Do not redesign the architecture under any circumstances.


## Project Maintenance Policy

Effective immediately:

1. Do not create new Python files in the project root unless they are official application entry points.
2. Place all maintenance scripts under \scripts/\ using the following structure:
   - \scripts/migration/   - \scripts/patch/   - \scripts/search/   - \scripts/maintenance/   - \scripts/archive/3. Place reports under \docs/reports/\.
4. Place architecture documents under \docs/architecture/\.
5. Temporary scripts must never remain in the project root after implementation.
6. After completing a feature:
   - Remove obsolete temporary scripts.
   - Remove duplicate patch scripts.
   - Remove unused debug files.
7. Do not create filenames such as \*_final.py\, \*_new.py\, \*_copy.py\, \*_v2.py\. Use descriptive names instead.
8. Keep the project root clean. Only these files are allowed in the root:
   - \desktop_app.py   - \start.py\ (or \start.bat\)
   - equirements.txt   - \README.md   - \LICENSE   - \.gitignore9. Update imports and file paths whenever files are moved.
10. Verify the application launches successfully after the cleanup.

