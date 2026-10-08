import json
import subprocess
import tempfile
from pathlib import Path

from fastapi import UploadFile

CHUNK_SIZE = 1024 * 1024
MAX_UPLOAD_BYTES = 2 * 1024 * 1024 * 1024
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}


async def inspect_video(upload: UploadFile) -> dict[str, object]:
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Upload a supported video file (MP4, MOV, MKV, WebM, AVI, or M4V).")

    total_bytes = 0
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix) as temp_file:
            while chunk := await upload.read(CHUNK_SIZE):
                total_bytes += len(chunk)
                if total_bytes > MAX_UPLOAD_BYTES:
                    raise ValueError("The video must be smaller than 2 GB.")
                temp_file.write(chunk)

            if total_bytes == 0:
                raise ValueError("The selected video is empty.")

            temp_file.flush()
            return _probe_video(temp_file.name)
    finally:
        await upload.seek(0)


def _probe_video(file_path: str) -> dict[str, object]:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration:stream=codec_type,width,height",
                "-of",
                "json",
                file_path,
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
    except FileNotFoundError as error:
        raise ValueError("FFprobe is not installed on the server.") from error
    except subprocess.CalledProcessError as error:
        raise ValueError("FFprobe could not read this video file.") from error
    except subprocess.TimeoutExpired as error:
        raise ValueError("Video inspection timed out. Try a shorter clip.") from error

    metadata = json.loads(result.stdout)
    streams = metadata.get("streams", [])
    video_stream = next(
        (stream for stream in streams if stream.get("codec_type") == "video"),
        None,
    )
    if video_stream is None:
        raise ValueError("The uploaded file does not contain a video stream.")

    duration = float(metadata.get("format", {}).get("duration", 0))
    return {
        "duration_seconds": round(duration, 2),
        "width": video_stream.get("width"),
        "height": video_stream.get("height"),
        "has_audio": any(stream.get("codec_type") == "audio" for stream in streams),
    }
