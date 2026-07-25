import os
from typing import Any, Dict, List

class TestReport:
    """Generates execution reports summarizing acceptance runs."""

    @classmethod
    def generate_report(
        cls, 
        report_path: str, 
        results: Dict[str, Any], 
        validation_errors: List[str]
    ) -> None:
        """Writes a Markdown report summarizing acceptance results.
        
        Args:
            report_path (str): Target output file path.
            results (Dict[str, Any]): Execution output paths.
            validation_errors (List[str]): List of failures.
        """
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        status = "PASSED" if not validation_errors else "FAILED"
        
        report_md = [
            "# Alpha 0.1 Acceptance Test Execution Report",
            f"\n## Execution Status: **{status}**",
            "\n### Pipeline Details",
            f"* **Project Directory**: `{results.get('project_dir')}`",
            f"* **Video Source**: `{results.get('video_path')}`",
            f"* **Extracted Audio**: `{results.get('audio_path')}`",
            "\n### Validation Errors"
        ]
        
        if validation_errors:
            for err in validation_errors:
                report_md.append(f"- [x] **ERROR**: {err}")
        else:
            report_md.append("- *None (All outputs are valid)*")

        speech_bench = results.get("speech_benchmark")
        tts_bench = results.get("tts_benchmark")

        report_md.append("\n### Telemetry Benchmarks")
        
        if speech_bench:
            report_md.extend([
                "\n#### Speech Recognition (Whisper)",
                f"* **Model**: `{speech_bench.model}`",
                f"* **Device**: `{speech_bench.device}`",
                f"* **Latency**: `{speech_bench.execution_time_seconds:.2f}s`",
                f"* **Realtime Factor (RTF)**: `{speech_bench.realtime_factor:.2f}`",
                f"* **Memory Overhead**: `{speech_bench.memory_usage_mb:.2f} MB`"
            ])
            
        if tts_bench:
            report_md.extend([
                "\n#### Voice Synthesis (EdgeTTS)",
                f"* **Voice**: `{tts_bench.voice}`",
                f"* **Provider**: `{tts_bench.provider}`",
                f"* **Latency**: `{tts_bench.synthesis_time_seconds:.2f}s`",
                f"* **Realtime Factor (RTF)**: `{tts_bench.realtime_factor:.2f}`"
            ])

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_md) + "\n")
