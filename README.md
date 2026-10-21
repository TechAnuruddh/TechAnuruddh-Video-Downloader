# TechAnuruddh Video Downloader

Live Link Video Download:= https://techanuruddh-video-downloader.onrender.com/ 

A clean, self-hosted video and audio downloader powered by **Python, FastAPI, and yt-dlp**.

Download supported video and audio formats through a simple, modern interface. Run locally on your own computer, with no advertisements or database required.

**Built and customized by TechAnuruddh.**

---

## Features

- 🎬 **Video Downloads** — Select available resolutions and supported video formats.
- 🎵 **Audio Downloads** — Convert supported audio streams to MP3 at available bitrates.
- 🌐 **Multi-platform Support** — yt-dlp supports YouTube and many other websites, subject to platform restrictions.
- 🖥️ **Cross-platform** — Run on Windows, macOS, and Linux.
- ⚡ **Lightweight Backend** — FastAPI-powered Python application.
- 🔒 **Self-hosted** — Process downloads on your own server or computer.
- 🛠️ **FFmpeg Integration** — Merge separate audio/video streams and enable audio conversion.

## Tech Stack

- **Backend:** Python, FastAPI
- **Download Engine:** yt-dlp
- **Media Processing:** FFmpeg
- **Frontend:** HTML, CSS, JavaScript
- **Environment:** Python virtual environment

## Requirements

- Python 3.9 or newer
- FFmpeg installed and accessible through PATH
- Internet connection
- Dependencies listed in `requirements.txt`

## Installation on Windows

### 1. Clone the repository

```powershell
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

Replace the repository URL with your actual GitHub repository.

### 2. Create a virtual environment

```powershell
py -3.12 -m venv .venv
```

### 3. Activate it

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
pip install -r requirements.txt
```

### 5. Start the application

```powershell
python main.py
```

Open the following address in your browser:

**http://localhost:8080**

Keep the terminal open while using the application.

## FFmpeg Setup

Download FFmpeg from the official website:

https://ffmpeg.org/download.html

On Windows, extract the downloaded build and add its `bin` directory to PATH. Restart the terminal afterward.

Verify the installation:

```powershell
ffmpeg -version
```

## Configuration

The application supports these environment variables, according to the original project configuration:

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8080` | Server port |
| `MAX_SIZE_MB` | `500` | Maximum configured download size in MB |
| `COOKIES_FILE` | `cookies.txt` | Optional cookies file path |

Actual behavior depends on the backend implementation.

## Run on a Different Port

```powershell
$env:PORT = "9000"
python main.py
```

Then open `http://localhost:9000`.

## Project Structure

```text
TechAnuruddh-Video-Downloader/
├── frontend/
│   └── index.html
├── main.py
├── requirements.txt
├── README.md
└── .gitignore
```

The actual project may contain additional files.

## Important Notes

- Only download content you own or are authorized to download.
- Follow the applicable website terms and copyright laws.
- Do not publish personal cookies, authentication tokens, API keys, or other secrets.
- A public GitHub repository shares source code; hosting the application requires a separate deployment.
- Public deployment may require additional security, resource limits, and abuse protection.

## Credits

This project is based on the open-source [yt-dlp](https://github.com/yt-dlp/yt-dlp) project and the original [yt-dlp-web repository](https://github.com/samrtulethtb/yt-dlp-web).

**Customized and branded by TechAnuruddh.**

## License

Retain and follow the original project's MIT license and attribution requirements. See the repository's `LICENSE` file for details.



Run Command:= cd C:\Users\hp\Downloads\yt-dlp-web-main\yt-dlp-web-main; .\.venv\Scripts\Activate.ps1; $env:Path = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Gyan.FFmpeg.Shared_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build-shared\bin;$env:Path"; python main.py
