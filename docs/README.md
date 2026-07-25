# AutoShort Studio - Technical Documentation Catalog

Welcome to the documentation catalog for **AutoShort Studio**. This repository houses technical specs, sprint reviews, architectural blueprints, and developmental checklists.

---

## Catalog Structure

```
docs/
├── README.md               # Catalog entrypoint (this file)
│
├── architecture/           # System design & blueprints
│   ├── sprint09_architecture.md
│   └── sprint10_architecture.md
│
├── reviews/                # Sprint reviews & code statistics
│   ├── sprint09_review.md
│   └── sprint10_review.md
│
├── checklists/             # Checklists & limitations
│   ├── sprint09_checklist.md
│   └── sprint10_checklist.md
│
├── testing/                # Test plans & verification
│   ├── alpha01_test_plan.md
│   ├── alpha01_execution.md
│   ├── alpha01_checklist.md
│   ├── alpha01_results.md
│   ├── alpha01_pipeline.md
│   └── alpha01_execution_result.md
│
├── roadmap/                # Roadmap & future milestones
│   └── roadmap.md
│
├── decisions/              # Architecture Decision Records (ADRs)
│
└── api/                    # API design and contracts catalog
```

---

## Core Engines

1. **[Video Import Engine](file:///t:/AutoShort%20Studio/docs/reviews/sprint09_review.md)**: Standard project directories layout, ffmpeg wav conversions, ffprobe queries, yt-dlp integrations.
2. **[LLM Service & Script Generation](file:///t:/AutoShort%20Studio/docs/reviews/sprint09_review.md)**: external prompt templates loading, conversation histories, token tracking, cost estimations.
3. **[Speech Recognition](file:///t:/AutoShort%20Studio/docs/reviews/sprint09_review.md)**: local Whisper transcribers, timed word alignments, segment metrics, progress, and cancellations.
4. **[Translation Engine](file:///t:/AutoShort%20Studio/docs/reviews/sprint09_review.md)**: ChatAnywhere integrations, chunk checkpoints, glossary rules, translation caching.
5. **[Timeline Alignment](file:///t:/AutoShort%20Studio/docs/reviews/sprint09_review.md)**: line CPL splitting, neighboring short merging, timeline overlap adjustments, pause generators.
6. **[Voice Synthesis](file:///t:/AutoShort%20Studio/docs/reviews/sprint10_review.md)**: edge-tts public API streams, silence gap generators, audio merging, loudness normalizations.
7. **[Alpha 0.1 Verification Plan](file:///t:/AutoShort%20Studio/docs/testing/alpha01_test_plan.md)**: End-to-end pipeline test scenarios, success criteria, manual verification, and metrics.
8. **[Alpha 0.1 Execution Guide](file:///t:/AutoShort%20Studio/docs/testing/alpha01_execution.md)**: Prerequisites, execution instructions, expected outputs, and troubleshooting.
9. **[Alpha 0.1 Checklist](file:///t:/AutoShort%20Studio/docs/testing/alpha01_checklist.md)**: Readiness checkpoints tracking.
10. **[Alpha 0.1 Results Template](file:///t:/AutoShort%20Studio/docs/testing/alpha01_results.md)**: Execution logs and telemetry templates.
11. **[Alpha 0.1 Pipeline Driver CLI](file:///t:/AutoShort%20Studio/docs/testing/alpha01_pipeline.md)**: CLI parameters guide and sequential stages logic.
12. **[Alpha 0.1 Execution Results](file:///t:/AutoShort%20Studio/docs/testing/alpha01_execution_result.md)**: Telemetry outcomes and files audit of the E2E verification run.
