#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["youtube-transcript-api", "yt-dlp", "openai-whisper"]
# ///

import re
import sys
import argparse
import tempfile
import urllib.request
from pathlib import Path

_whisper_model = None  # lazy-loaded


def detect_platform(url: str) -> str | None:
    url = url.strip().lower()
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    if "tiktok.com" in url:
        return "tiktok"
    if "instagram.com" in url:
        return "instagram"
    return None


# ── YouTube helpers ──────────────────────────────────────────────────────────

def extract_video_id(url: str) -> str | None:
    patterns = [r"(?:v=|youtu\.be/|/embed/|/shorts/)([A-Za-z0-9_-]{11})"]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url.strip()):
        return url.strip()
    return None


def fetch_video_title(video_id: str) -> str | None:
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8")
        match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
        if match:
            return match.group(1)
        match = re.search(r'<title>([^<]+)</title>', html)
        if match:
            return re.sub(r'\s*-\s*YouTube$', '', match.group(1)).strip()
    except Exception:
        pass
    return None


def sanitize_filename(title: str) -> str:
    title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title[:200] or "transcript"


def fetch_yt_captions(video_id: str) -> str:
    from youtube_transcript_api import YouTubeTranscriptApi

    transcript = YouTubeTranscriptApi().fetch(video_id)
    return " ".join(snippet.text for snippet in transcript.snippets)


# ── Whisper / yt-dlp helpers ─────────────────────────────────────────────────

def slugify(text: str, max_len: int = 60) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text).strip("-")
    return text[:max_len].rstrip("-")


def load_whisper(model_name: str):
    global _whisper_model
    if _whisper_model is None:
        import whisper
        print(f"  Loading Whisper '{model_name}' model...")
        _whisper_model = whisper.load_model(model_name)
    return _whisper_model


def download_audio(url: str, tmp_dir: Path) -> tuple[Path, str, str]:
    import yt_dlp

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(tmp_dir / "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_id = info["id"]
        downloads = info.get("requested_downloads") or []
        if downloads and "filepath" in downloads[0]:
            audio_path = Path(downloads[0]["filepath"])
        else:
            matches = list(tmp_dir.glob(f"{video_id}.*"))
            if not matches:
                raise FileNotFoundError(f"No downloaded file found for {video_id}")
            audio_path = matches[0]
        return audio_path, video_id, info.get("title", video_id)


def transcribe_audio(audio_path: Path, model) -> str:
    result = model.transcribe(str(audio_path))
    return result["text"].strip()


# ── Per-platform processing ───────────────────────────────────────────────────

def process_youtube(url: str, output_dir: Path, model_name: str) -> None:
    from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled

    video_id = extract_video_id(url)
    if not video_id:
        print(f"  [SKIP] Could not parse YouTube video ID from: {url}")
        return

    # Try caption API first
    try:
        print(f"  Fetching captions for {video_id}...")
        text = fetch_yt_captions(video_id)
        title = fetch_video_title(video_id)
        filename = sanitize_filename(title) if title else video_id
        out_path = output_dir / f"{filename}.txt"
        out_path.write_text(text, encoding="utf-8")
        print(f"  [OK]   Saved to {out_path}")
        return
    except (TranscriptsDisabled, NoTranscriptFound):
        print(f"  No captions found for {video_id}, falling back to Whisper...")
    except Exception as e:
        print(f"  Caption fetch failed ({e}), falling back to Whisper...")

    # Fall back to Whisper
    process_with_whisper(url, output_dir, model_name)


def process_with_whisper(url: str, output_dir: Path, model_name: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        print(f"  Downloading audio from {url}...")
        try:
            audio_path, video_id, title = download_audio(url, tmp_dir)
        except Exception as e:
            print(f"  [FAIL] Download error: {e}")
            return

        print(f"  Transcribing {video_id}...")
        try:
            model = load_whisper(model_name)
            text = transcribe_audio(audio_path, model)
            slug = slugify(title) or video_id
            out_path = output_dir / f"{slug}.txt"
            if out_path.exists():
                out_path = output_dir / f"{slug}-{video_id[:8]}.txt"
            out_path.write_text(text, encoding="utf-8")
            print(f"  [OK]   Saved to {out_path}")
        except Exception as e:
            print(f"  [FAIL] Transcription error: {e}")


def process_url(url: str, output_dir: Path, model_name: str) -> None:
    platform = detect_platform(url)
    if platform == "youtube":
        process_youtube(url, output_dir, model_name)
    elif platform in ("tiktok", "instagram"):
        process_with_whisper(url, output_dir, model_name)
    else:
        print(f"  [SKIP] Unrecognized platform for URL: {url}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transcribe YouTube, TikTok, or Instagram Reel videos to text.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Platform is auto-detected from the URL.\n"
            "YouTube: uses caption API first, falls back to Whisper.\n"
            "TikTok / Instagram: always uses Whisper.\n\n"
            "Whisper models: tiny | base | small | medium | large  (larger = more accurate, slower)"
        ),
    )
    parser.add_argument("urls", nargs="*", help="Video URLs to transcribe")
    parser.add_argument("--model", default="base", help="Whisper model size (default: base)")
    args = parser.parse_args()

    output_dir = Path(".")

    if args.urls:
        urls = args.urls
    else:
        print("Paste video URLs (YouTube, TikTok, Instagram — one per line).")
        print("Press Enter twice when done:\n")
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
        urls = [ln for ln in lines if ln.strip()]

    if not urls:
        print("No URLs provided. Exiting.")
        sys.exit(1)

    print(f"\nProcessing {len(urls)} URL(s)...\n")
    for url in urls:
        url = url.strip()
        if url:
            process_url(url, output_dir, args.model)
    print("\nDone.")


if __name__ == "__main__":
    main()
