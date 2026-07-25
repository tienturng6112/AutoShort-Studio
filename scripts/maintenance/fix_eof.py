with open('backend/run_pipeline.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if line.strip() == 'report = {':
        lines = lines[:i]
        lines.append('        report = {\n')
        lines.append('            "status": "success",\n')
        lines.append('            "total_duration_seconds": video_dur\n')
        lines.append('        }\n')
        lines.append('        return report\n')
        lines.append('\n')
        lines.append('    except Exception as e:\n')
        lines.append('        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)\n')
        lines.append('        try:\n')
        lines.append('            state_manager.update_execution_state("Failed", progress=0, current_stage=f"Error: {str(e)}")\n')
        lines.append('        except Exception:\n')
        lines.append('            pass\n')
        lines.append('        raise e\n')
        break

with open('backend/run_pipeline.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
