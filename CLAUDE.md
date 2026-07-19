# CLAUDE.md

Guidance for Claude Code when working with this repository.

## Running the Script

Single-file Python script using `uv` for dependency management (no venv setup needed):

```bash
# With URL arguments
uv run transcript.py https://www.youtube.com/watch?v=VIDEO_ID
uv run transcript.py https://www.tiktok.com/@user/video/ID
uv run transcript.py https://www.instagram.com/reel/ID/

# Multiple URLs (mixed platforms OK)
uv run transcript.py <yt-url> <tiktok-url> <ig-url>

# Custom Whisper model (for TikTok/Instagram or YouTube fallback)
uv run transcript.py <url> --model small

# Interactive mode (no args — paste URLs, press Enter twice)
uv run transcript.py
```

## Architecture

Single script (`transcript.py`) with inline PEP 723 dependency declaration.

### Platform Detection
`detect_platform(url)` inspects the domain and returns `"youtube"`, `"tiktok"`, `"instagram"`, or `None`.

### Per-Platform Strategy
- **YouTube**: `process_youtube()` — tries `youtube-transcript-api` first (fast, no AI). On `NoTranscriptFound` / `TranscriptsDisabled`, falls back to `process_with_whisper()`.
- **TikTok / Instagram**: `process_with_whisper()` — downloads audio via `yt-dlp`, transcribes with OpenAI Whisper.

### Whisper Model
Loaded lazily via `load_whisper(model_name)` — only initialized on the first URL that needs it. If all YouTube URLs have captions, Whisper never loads.

### Key Functions
- `detect_platform(url)` — returns platform string
- `extract_video_id(url)` — parses YouTube video ID
- `fetch_yt_captions(video_id)` — fetches YouTube captions via transcript API
- `download_audio(url, tmp_dir)` — downloads audio via yt-dlp to a temp dir
- `transcribe_audio(audio_path, model)` — Whisper speech-to-text
- `process_youtube(url, output_dir, model_name)` — YouTube with fallback logic
- `process_with_whisper(url, output_dir, model_name)` — Whisper path for TikTok/Instagram/YT fallback
- `process_url(url, output_dir, model_name)` — top-level dispatcher

### Output
Transcripts saved as `.txt` files in the directory where the script is run (`Path(".")`).
- YouTube (captions): `{sanitized_title}.txt`
- All others: `{slugified_title}.txt` (collision-safe with `{slug}-{id[:8]}.txt`)

## Tests

The pure-function and CLI tests do not make network calls or download models:

```bash
python -m unittest -v
python transcript.py --help
```
