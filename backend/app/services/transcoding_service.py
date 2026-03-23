"""Transcoding service — coordinates video transcoding jobs."""

import json
import logging
import subprocess
from typing import Dict, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)

RESOLUTION_MAP: Dict[str, Dict[str, int]] = {
    "360p": {"width": 640, "height": 360, "bitrate": 800_000},
    "480p": {"width": 854, "height": 480, "bitrate": 1_200_000},
    "720p": {"width": 1280, "height": 720, "bitrate": 2_500_000},
    "1080p": {"width": 1920, "height": 1080, "bitrate": 5_000_000},
    "1440p": {"width": 2560, "height": 1440, "bitrate": 8_000_000},
    "2160p": {"width": 3840, "height": 2160, "bitrate": 16_000_000},
}


def probe_video(input_path: str) -> Optional[dict]:
    """Use ffprobe to get video metadata."""
    try:
        cmd = [
            settings.FFPROBE_PATH,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            input_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            logger.error(f"ffprobe failed: {result.stderr}")
            return None
        return json.loads(result.stdout)
    except Exception as e:
        logger.error(f"Failed to probe video: {e}")
        return None


def get_video_duration(probe_data: dict) -> Optional[float]:
    """Extract duration from probe data."""
    try:
        return float(probe_data.get("format", {}).get("duration", 0))
    except (ValueError, TypeError):
        return None


def get_video_resolution(probe_data: dict) -> Optional[tuple]:
    """Extract (width, height) from probe data."""
    for stream in probe_data.get("streams", []):
        if stream.get("codec_type") == "video":
            return stream.get("width"), stream.get("height")
    return None


def get_target_resolutions(source_height: int) -> List[str]:
    """Determine which resolutions to transcode to based on source height."""
    targets = []
    for res_name, res_info in RESOLUTION_MAP.items():
        if res_info["height"] <= source_height:
            targets.append(res_name)
    return targets


def transcode_video(input_path: str, output_path: str, resolution: str) -> bool:
    """Transcode a video to a specific resolution using ffmpeg."""
    res_info = RESOLUTION_MAP.get(resolution)
    if not res_info:
        logger.error(f"Unknown resolution: {resolution}")
        return False

    try:
        cmd = [
            settings.FFMPEG_PATH,
            "-i", input_path,
            "-vf", f"scale={res_info['width']}:{res_info['height']}",
            "-c:v", "libx264",
            "-preset", "medium",
            "-b:v", str(res_info["bitrate"]),
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            "-y",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if result.returncode != 0:
            logger.error(f"Transcoding failed for {resolution}: {result.stderr}")
            return False
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"Transcoding timed out for {resolution}")
        return False
    except Exception as e:
        logger.error(f"Transcoding error: {e}")
        return False


def generate_thumbnail(input_path: str, output_path: str, time_offset: float = 1.0) -> bool:
    """Generate a thumbnail image from a video."""
    try:
        cmd = [
            settings.FFMPEG_PATH,
            "-i", input_path,
            "-ss", str(time_offset),
            "-vframes", "1",
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
            "-y",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Thumbnail generation failed: {e}")
        return False
