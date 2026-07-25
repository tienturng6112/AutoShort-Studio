import pytest
from unittest.mock import patch, MagicMock
import subprocess
from backend.media.metadata_extractor import MetadataExtractor

def test_extract_metadata_valid_video():
    """Test extracting metadata with a valid video output from ffprobe."""
    mock_stdout = """{
        "streams": [
            {
                "codec_type": "video",
                "r_frame_rate": "30/1",
                "width": 1920,
                "height": 1080,
                "codec_name": "h264",
                "bit_rate": "500000"
            },
            {
                "codec_type": "audio",
                "index": 1,
                "codec_name": "aac",
                "channels": 2
            }
        ],
        "format": {
            "duration": "10.0"
        }
    }"""
    
    with patch("shutil.which", return_value="/usr/bin/ffprobe"), \
         patch("subprocess.run") as mock_run:
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = mock_stdout
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        metadata = MetadataExtractor.extract_metadata("valid.mp4")
        
        assert metadata["duration"] == 10.0
        assert metadata["fps"] == 30.0
        assert metadata["width"] == 1920
        assert metadata["height"] == 1080
        assert metadata["codec"] == "h264"
        assert len(metadata["audio_streams"]) == 1
        assert metadata["audio_streams"][0]["codec"] == "aac"
        assert metadata["audio_streams"][0]["channels"] == 2

def test_extract_metadata_missing_ffprobe():
    """Test behavior when ffprobe is missing on the system path."""
    with patch("shutil.which", return_value=None):
        with pytest.raises(RuntimeError) as exc_info:
            MetadataExtractor.extract_metadata("valid.mp4")
        assert "FFmpeg / ffprobe is not installed or not found." in str(exc_info.value)

def test_extract_metadata_invalid_video():
    """Test behavior when ffprobe returns non-zero code due to invalid file."""
    with patch("shutil.which", return_value="/usr/bin/ffprobe"), \
         patch("subprocess.run") as mock_run:
        
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Invalid data found when processing input"
        mock_run.return_value = mock_result
        
        with pytest.raises(RuntimeError) as exc_info:
            MetadataExtractor.extract_metadata("invalid.mp4")
        assert "ffprobe execution failure" in str(exc_info.value)

def test_extract_metadata_empty_stdout():
    """Test behavior when ffprobe execution succeeds but stdout is empty."""
    with patch("shutil.which", return_value="/usr/bin/ffprobe"), \
         patch("subprocess.run") as mock_run:
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        with pytest.raises(RuntimeError) as exc_info:
            MetadataExtractor.extract_metadata("empty.mp4")
        assert "ffprobe output is empty." in str(exc_info.value)
