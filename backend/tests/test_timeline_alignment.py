import os
import tempfile
import pytest
from backend.alignment.alignment_service import TimelineAlignmentService
from backend.alignment.merger import SegmentMerger
from backend.alignment.optimizer import TimelineOptimizer
from backend.alignment.pause_generator import PauseGenerator
from backend.alignment.reading_speed import ReadingSpeedAnalyzer
from backend.alignment.splitter import SegmentSplitter
from backend.alignment.validator import TranscriptValidator
from backend.speech.models import Segment, Transcript, Word

def test_reading_speed_analyzer() -> None:
    analyzer = ReadingSpeedAnalyzer()
    
    # 10 chars, 2 seconds -> CPS = 5.0
    assert analyzer.calculate_cps("Hello word", 2.0) == 5.0
    
    # 2 words, 2 seconds -> WPM = 60.0
    assert analyzer.calculate_wpm("Hello word", 2.0) == 60.0

    profile = analyzer.get_profile("vi")
    assert profile.target_cps == 12.0


def test_segment_splitter() -> None:
    # 1. Text-only segment split
    splitter = SegmentSplitter(max_cpl=15)
    seg = Segment(id=1, start=0.0, end=4.0, text="This is a very long segment text", words=[], confidence=0.9)
    
    parts = splitter.split_segment(seg)
    assert len(parts) == 3
    assert len(parts[0].text) <= 15
    assert parts[0].start == 0.0
    assert parts[-1].end == 4.0

    # 2. Word-boundary segment split
    words = [
        Word(word="Hello", start=0.0, end=1.0, probability=0.9),
        Word(word="world!", start=1.0, end=2.0, probability=0.9),
        Word(word="Howdy?", start=2.0, end=3.0, probability=0.9)
    ]
    seg_words = Segment(id=1, start=0.0, end=3.0, text="Hello world! Howdy?", words=words, confidence=0.9)
    
    parts_words = splitter.split_segment(seg_words)
    assert len(parts_words) >= 1
    assert parts_words[0].words[0].word == "Hello"


def test_segment_merger() -> None:
    merger = SegmentMerger(min_duration=1.5, max_merge_chars=20)
    
    # Short segment and normal segment (mergeable)
    seg1 = Segment(id=1, start=0.0, end=1.0, text="Short", words=[], confidence=0.9)
    seg2 = Segment(id=2, start=1.0, end=3.0, text="Segment", words=[], confidence=0.9)
    
    merged = merger.merge_segments([seg1, seg2])
    assert len(merged) == 1
    assert merged[0].text == "Short Segment"
    assert merged[0].start == 0.0
    assert merged[0].end == 3.0


def test_timeline_optimizer() -> None:
    optimizer = TimelineOptimizer(min_duration=0.2)
    
    # Overlapping and zero-duration segments
    seg1 = Segment(id=1, start=0.0, end=2.0, text="One", words=[], confidence=0.9)
    seg2 = Segment(id=2, start=1.5, end=3.0, text="Two", words=[], confidence=0.9)  # Overlaps
    seg3 = Segment(id=3, start=3.0, end=3.0, text="Three", words=[], confidence=0.9)  # Zero-duration
    
    opts = optimizer.optimize_timestamps([seg1, seg2, seg3])
    assert len(opts) == 3
    assert opts[1].start >= opts[0].end
    assert opts[2].end > opts[2].start


def test_pause_generator() -> None:
    generator = PauseGenerator(pause_duration=0.5)
    
    seg1 = Segment(id=1, start=0.0, end=1.0, text="One", words=[], confidence=0.9)
    seg2 = Segment(id=2, start=1.0, end=2.0, text="Two", words=[], confidence=0.9)
    
    paused = generator.insert_pauses([seg1, seg2])
    assert len(paused) == 2
    assert paused[1].start == 1.5
    assert paused[1].end == 2.5


def test_transcript_validator() -> None:
    validator = TranscriptValidator(max_cps=10.0, max_cpl=15)
    
    # Invalid: overlap, duplicate ID, fast speed
    seg1 = Segment(id=1, start=0.0, end=1.0, text="This is too long for the CPL limit", words=[], confidence=0.9)
    seg2 = Segment(id=1, start=0.5, end=0.8, text="Overlap and fast", words=[], confidence=0.9)
    transcript = Transcript(text="", language="en", language_probability=0.9, duration=1.0, segments=[seg1, seg2])
    
    errors = validator.validate(transcript)
    assert len(errors) > 0
    assert any("overlap" in e for e in errors)
    assert any("duplicate" in e for e in errors)


@pytest.mark.asyncio
async def test_alignment_service_pipeline() -> None:
    with tempfile.TemporaryDirectory() as tmp_root:
        service = TimelineAlignmentService(max_cpl=15, min_duration=1.0, min_segment_gap=0.3)
        
        seg1 = Segment(id=0, start=0.0, end=0.8, text="TooShort", words=[], confidence=0.9)
        seg2 = Segment(id=1, start=0.8, end=1.5, text="LongSegmentHereToCheckSplitting", words=[], confidence=0.9)
        transcript = Transcript(text="", language="en", language_probability=0.9, duration=1.5, segments=[seg1, seg2])
        
        res = await service.align_transcript(transcript, output_dir=tmp_root)
        
        assert len(res.segments) > 0
        assert res.segments[0].id == 0
        
        assert os.path.exists(os.path.join(tmp_root, "aligned_transcript.json"))
        assert os.path.exists(os.path.join(tmp_root, "aligned_transcript.srt"))
