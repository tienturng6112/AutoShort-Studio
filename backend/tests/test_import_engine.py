import json
import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch
import pytest
from backend.media.audio_extractor import AudioExtractor
from backend.media.import_cache import ImportCache
from backend.media.local_importer import LocalImporter
from backend.media.metadata_extractor import MetadataExtractor
from backend.media.youtube_importer import YoutubeImporter
from backend.services.project_service import ProjectService

def test_project_service_creation() -> None:
    with tempfile.TemporaryDirectory() as tmp_root:
        service = ProjectService(projects_root=tmp_root)
        project_id = "test_project_123"
        name = "My Test Project"
        
        data = service.create_project(project_id, name)
        assert data["id"] == project_id
        assert data["name"] == name
        assert data["status"] == "draft"
        
        project_dir = service.get_project_dir(project_id)
        assert os.path.exists(os.path.join(project_dir, "project.json"))
        
        # Verify default subdirs exist
        for sd in ["video", "audio", "subtitle", "translation", "tts", "render", "cache", "metadata", "logs"]:
            assert os.path.exists(os.path.join(project_dir, sd))


def test_import_cache_operations() -> None:
    with tempfile.TemporaryDirectory() as tmp_root:
        cache_file = os.path.join(tmp_root, "cache.json")
        cache = ImportCache(cache_file_path=cache_file)
        
        # Mock imported file existence
        dummy_file = os.path.join(tmp_root, "imported.mp4")
        with open(dummy_file, "w") as f:
            f.write("data")
            
        assert cache.get("http://youtube.com/xyz") is None
        
        cache.set("http://youtube.com/xyz", dummy_file)
        assert cache.get("http://youtube.com/xyz") == dummy_file
        
        # Test file missing from disk deletes entry behavior
        os.remove(dummy_file)
        assert cache.get("http://youtube.com/xyz") is None


@pytest.mark.asyncio
async def test_local_importer() -> None:
    with tempfile.TemporaryDirectory() as tmp_root:
        source_dir = os.path.join(tmp_root, "source")
        dest_dir = os.path.join(tmp_root, "dest")
        os.makedirs(source_dir, exist_ok=True)
        
        # Create a dummy source file
        source_file = os.path.join(source_dir, "video.mp4")
        with open(source_file, "w", encoding="utf-8") as f:
            f.write("dummy media content")
            
        importer = LocalImporter()
        res = await importer.import_media(source_file, dest_dir)
        
        assert os.path.exists(res)
        assert os.path.basename(res) == "video.mp4"
        assert os.path.dirname(res) == os.path.abspath(dest_dir)
        
        # Verify nonexistent file raises error
        with pytest.raises(FileNotFoundError):
            await importer.import_media(os.path.join(source_dir, "nonexistent.mp4"), dest_dir)


@pytest.mark.asyncio
@patch("backend.media.youtube_importer.subprocess.run")
async def test_youtube_importer(mock_run: MagicMock) -> None:
    importer = YoutubeImporter()
    res = await importer.import_media("http://youtube.com/watch?v=123", "dest/project")
    assert "youtube_download.mp4" in res
    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert "yt-dlp" in args[0]


@patch("backend.media.metadata_extractor.subprocess.run")
def test_metadata_extraction(mock_run: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.stdout = json.dumps({
        "format": {
            "duration": "15.5",
            "bit_rate": "250000"
        },
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "hevc",
                "width": 1280,
                "height": 720,
                "r_frame_rate": "60/1",
                "bit_rate": "200000"
            },
            {
                "codec_type": "audio",
                "codec_name": "opus",
                "channels": 2
            }
        ]
    })
    mock_run.return_value = mock_response

    meta = MetadataExtractor.extract_metadata("dummy_video.mp4")
    assert meta["duration"] == 15.5
    assert meta["fps"] == 60.0
    assert meta["width"] == 1280
    assert meta["height"] == 720
    assert meta["codec"] == "hevc"
    assert meta["bitrate"] == 250000
    assert len(meta["audio_streams"]) == 1
    assert meta["audio_streams"][0]["codec"] == "opus"


@patch("backend.media.audio_extractor.subprocess.run")
def test_audio_extraction(mock_run: MagicMock) -> None:
    wav = AudioExtractor.extract_audio("dummy_video.mp4", "temp/extracted_audio.wav")
    assert wav == "temp/extracted_audio.wav"
    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert "ffmpeg" in args[0]
    assert "pcm_s16le" in args[0]
    assert "16000" in args[0]
