
"""
yt-dlp Web — Minimal self-hosted video downloader
Cross-platform: Windows, Linux, macOS
"""

import os
import re
import sys
import asyncio
import tempfile
import shutil
import subprocess
import json
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# ── Config ──────────────────────────────────────────────────────────────

PORT = int(os.environ.get("PORT", 8080))
MAX_SIZE_MB = int(os.environ.get("MAX_SIZE_MB", 500))

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

cookies_setting = os.environ.get("COOKIES_FILE", "cookies.txt")
COOKIES_PATH = Path(cookies_setting)

if not COOKIES_PATH.is_absolute():
    COOKIES_PATH = BASE_DIR / COOKIES_PATH

COOKIES_FILE = str(COOKIES_PATH)


app = FastAPI(
    title="TechAnuruddh Video Downloader",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

if FRONTEND_DIR.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(FRONTEND_DIR)),
        name="static",
    )


# ── Models ──────────────────────────────────────────────────────────────

class InfoRequest(BaseModel):
    url: str


class DownloadRequest(BaseModel):
    url: str
    format_id: str
    ext: str
    audio_bitrate: Optional[str] = "320"
    title: Optional[str] = None


# ── YouTube JavaScript runtime detection ─────────────────────────────────

def _find_deno() -> Optional[str]:
    """Find Deno for yt-dlp's YouTube JavaScript challenge support."""

    deno_path = shutil.which("deno")

    if deno_path and os.path.isfile(deno_path):
        return deno_path

    # Windows: check the known WinGet installation directory.
    local_app_data = os.environ.get("LOCALAPPDATA", "")

    if local_app_data:
        candidate = (
            Path(local_app_data)
            / "Microsoft"
            / "WinGet"
            / "Packages"
            / "DenoLand.Deno_Microsoft.Winget.Source_8wekyb3d8bbwe"
            / "deno.exe"
        )

        if candidate.is_file():
            return str(candidate)

    return None


# ── Helpers ─────────────────────────────────────────────────────────────

def _ytdlp_base_args() -> list:
    """
    Run yt-dlp through the current Python interpreter.
    Configure Deno when available for YouTube extraction.
    Keep cookies support and avoid forcing a problematic player client.
    """

    args = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--no-playlist",
        "--no-warnings",
    ]

    deno_path = _find_deno()

    if deno_path:
        args.extend([
            "--js-runtimes",
            f"deno:{deno_path}",
        ])

    if os.path.isfile(COOKIES_FILE):
        args.extend([
            "--cookies",
            COOKIES_FILE,
        ])

    return args


def _run(args: list, cwd: str = None, timeout_sec: int = 300):
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout_sec,
            encoding="utf-8",
            errors="replace",
        )

        return (
            result.returncode,
            result.stdout,
            result.stderr,
        )

    except subprocess.TimeoutExpired:
        return -1, "", "Download timed out"

    except OSError as exc:
        return -1, "", f"Could not start yt-dlp: {exc}"


def _safe_filename(name: str) -> str:
    """Remove characters that are invalid in common filenames."""

    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    name = name.strip().strip(".")

    return name or "download"


# ── Routes ──────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    for path in (
        FRONTEND_DIR / "index.html",
        BASE_DIR / "index.html",
    ):
        if path.is_file():
            return HTMLResponse(
                content=path.read_text(encoding="utf-8")
            )

    return HTMLResponse(
        "<h1>yt-dlp Web — place index.html in frontend/</h1>"
    )


@app.post("/api/info")
async def get_info(req: InfoRequest):
    url = req.url.strip()

    if not url:
        raise HTTPException(400, detail="Please provide a video URL")

    args = _ytdlp_base_args() + [
        "--dump-json",
        "--skip-download",
        url,
    ]

    code, stdout, stderr = await asyncio.to_thread(
        _run,
        args,
        None,
        180,
    )

    if code != 0:
        message = stderr.strip() or "Could not fetch video info"
        raise HTTPException(400, detail=message[-3000:])

    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        raise HTTPException(
            400,
            detail="Invalid response from yt-dlp",
        )

    formats = []
    seen = set()

    for fmt in data.get("formats", []):
        fid = fmt.get("format_id", "")
        vcodec = fmt.get("vcodec", "none")
        acodec = fmt.get("acodec", "none")
        height = fmt.get("height")
        ext = fmt.get("ext", "")

        if not fid or vcodec == "none" or not height:
            continue

        label = f"{height}p {ext.upper()}"

        if label in seen:
            continue

        seen.add(label)

        # If a format has no audio, request audio alongside it.
        format_id = (
            fid if acodec != "none"
            else f"{fid}+bestaudio"
        )

        formats.append({
            "format_id": format_id,
            "label": label,
            "height": height,
            "ext": "mp4",
            "type": "video",
            "filesize": (
                fmt.get("filesize")
                or fmt.get("filesize_approx")
            ),
        })

    formats.sort(
        key=lambda item: item.get("height", 0),
        reverse=True,
    )

    # MP3 choices
    for bitrate, label in [
        ("320", "MP3 320kbps"),
        ("256", "MP3 256kbps"),
        ("128", "MP3 128kbps"),
    ]:
        formats.append({
            "format_id": "bestaudio/best",
            "label": label,
            "ext": "mp3",
            "type": "audio",
            "audio_bitrate": bitrate,
            "filesize": None,
        })

    return {
        "title": data.get("title", "Unknown"),
        "uploader": data.get("uploader", ""),
        "duration": data.get("duration"),
        "thumbnail": data.get("thumbnail", ""),
        "formats": formats,
    }


@app.post("/api/download")
async def download(
    req: DownloadRequest,
    background_tasks: BackgroundTasks,
):
    url = req.url.strip()

    if not url:
        raise HTTPException(400, detail="Please provide a video URL")

    tmp_dir = tempfile.mkdtemp(prefix="techanuruddh_dl_")

    try:
        url_lower = url.lower()

        is_facebook = (
            "facebook.com" in url_lower
            or "fb.watch" in url_lower
        )

        if req.ext.lower() == "mp3":
            args = _ytdlp_base_args() + [
                "-f",
                "bestaudio/best",
                "--extract-audio",
                "--audio-format",
                "mp3",
                "--audio-quality",
                f"{req.audio_bitrate or '320'}K",
                "-o",
                os.path.join(tmp_dir, "%(title)s.%(ext)s"),
                url,
            ]

        else:
            format_id = req.format_id

            # Preserve the Facebook-specific video + audio fallback.
            if is_facebook:
                format_id = "bestvideo*+bestaudio/best"

            args = _ytdlp_base_args() + [
                "-f",
                format_id,
                "--merge-output-format",
                "mp4",
                "-o",
                os.path.join(tmp_dir, "%(title)s.%(ext)s"),
                url,
            ]

        code, stdout, stderr = await asyncio.to_thread(
            _run,
            args,
            tmp_dir,
            600,
        )

        if code != 0:
            message = stderr.strip() or "Download failed"
            raise HTTPException(
                400,
                detail=message[-3000:],
            )

        files = [
            path
            for path in Path(tmp_dir).iterdir()
            if path.is_file()
            and not path.name.endswith((".part", ".ytdl"))
        ]

        if not files:
            raise HTTPException(
                500,
                detail="No output file generated",
            )

        # Prefer the largest generated media file.
        out_file = max(
            files,
            key=lambda path: path.stat().st_size,
        )

        size_mb = out_file.stat().st_size / (1024 * 1024)

        if size_mb > MAX_SIZE_MB:
            raise HTTPException(
                400,
                detail=(
                    f"File too large ({size_mb:.0f} MB). "
                    f"Limit is {MAX_SIZE_MB} MB."
                ),
            )

        if req.title and req.title.strip():
            safe_title = _safe_filename(req.title)
            ext = out_file.suffix.lstrip(".") or req.ext
            final_filename = f"{safe_title}.{ext}"
        else:
            final_filename = _safe_filename(out_file.name)

        encoded = quote(final_filename)

        ascii_filename = (
            final_filename.encode("ascii", "replace")
            .decode("ascii")
        )

        cd_header = (
            f'attachment; filename="{ascii_filename}"; '
            f"filename*=UTF-8''{encoded}"
        )

        return FileResponse(
            path=str(out_file),
            media_type="application/octet-stream",
            filename=None,
            headers={
                "Content-Disposition": cd_header,
            },
            background=__import__(
                "starlette.background",
                fromlist=["BackgroundTask"],
            ).BackgroundTask(
                shutil.rmtree,
                tmp_dir,
                ignore_errors=True,
            ),
        )

    except HTTPException:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise

    except Exception as exc:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise HTTPException(
            500,
            detail=str(exc),
        )


@app.get("/api/health")
async def health():
    args = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--version",
    ]

    code, out, err = await asyncio.to_thread(
        _run,
        args,
        None,
        10,
    )

    deno_path = _find_deno()

    return {
        "status": "ok",
        "ytdlp_version": out.strip() if code == 0 else "not found",
        "deno_available": bool(deno_path),
    }


if __name__ == "__main__":
    import uvicorn

    print(f"\n  yt-dlp Web running at http://localhost:{PORT}\n")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=False,
    )
