from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from ffmpeg_service import inspect_video

app = FastAPI(title="Burma Movie Recap API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "Burma Movie Recap API"}


@app.post("/api/recap")
async def prepare_recap(
    title: str = Form(..., min_length=1, max_length=200),
    language: str = Form("my"),
    video: UploadFile = File(...),
) -> dict[str, object]:
    if not video.filename:
        raise HTTPException(status_code=400, detail="Choose a video file to continue.")

    try:
        video_info = await inspect_video(video)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    finally:
        await video.close()

    return {
        "status": "prepared",
        "title": title.strip(),
        "language": language,
        "video": video_info,
        "message": "Video details are ready. Connect a recap-generation service to create the narration.",
    }
