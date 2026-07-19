# transcript

> One script to transcribe YouTube, TikTok, and Instagram Reels with dependencies managed by `uv`.

Paste any video URL and get a `.txt` transcript in seconds. Platform is auto-detected. YouTube videos with captions are fetched instantly; everything else is transcribed locally with [Whisper](https://github.com/openai/whisper).

---

## Features

- **Auto-detects platform** from the URL — YouTube, TikTok, or Instagram
- **YouTube caption API first** — instant transcripts with no AI overhead when captions exist
- **Whisper fallback** — if a YouTube video has no captions, or for TikTok/Instagram, audio is downloaded and transcribed locally
- **Single-file setup** — `uv` installs the declared Python packages on first run
- **Batch support** — pass multiple URLs at once, even across different platforms
- **Configurable Whisper model** — trade speed for accuracy with `--model`

---

## Requirements

- [uv](https://github.com/astral-sh/uv) — Python package runner (`brew install uv` or see [uv docs](https://docs.astral.sh/uv/getting-started/installation/))
- Internet access for video captions, media downloads, and first-run package or model downloads
- `ffmpeg` for Whisper transcription and media processing (`brew install ffmpeg` on macOS)

Dependencies (`youtube-transcript-api`, `yt-dlp`, `openai-whisper`) are declared inline and installed by `uv` on first run. A YouTube video with captions does not load a Whisper model, but the first `uv run` still resolves the declared packages.

---

## Usage

```bash
# Single URL — platform is auto-detected
uv run transcript.py https://www.youtube.com/watch?v=VIDEO_ID
uv run transcript.py https://www.tiktok.com/@user/video/ID
uv run transcript.py https://www.instagram.com/reel/ID/

# Multiple URLs (mixed platforms are fine)
uv run transcript.py <youtube-url> <tiktok-url> <instagram-url>

# Use a larger Whisper model for better accuracy
uv run transcript.py <url> --model small   # tiny | base | small | medium | large

# Interactive mode — paste URLs line by line, press Enter twice when done
uv run transcript.py
```

Output is saved as a `.txt` file in your current directory, named after the video title.

---

## How It Works

| Platform | Strategy |
|----------|----------|
| YouTube | Tries the caption/subtitle API first (fast, no AI). Falls back to Whisper if no captions are found. |
| TikTok | Downloads audio via `yt-dlp`, transcribes with Whisper. |
| Instagram | Downloads audio via `yt-dlp`, transcribes with Whisper. |

Whisper is loaded lazily — if all your YouTube videos have captions, the model is never loaded.

---

## Whisper Model Sizes

| Model | Speed | Accuracy | Best for |
|-------|-------|----------|----------|
| `tiny` | Fastest | Lower | Quick drafts |
| `base` | Fast | Good | Default, everyday use |
| `small` | Moderate | Better | Accents, technical speech |
| `medium` | Slow | High | High-quality output |
| `large` | Slowest | Best | Maximum accuracy |

---

## Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** this repository
2. **Create a branch** for your change: `git checkout -b my-feature`
3. **Make your changes** and test them locally with `uv run transcript.py`
4. **Open a pull request** with a clear description of what you changed and why

Ideas for contributions:
- Support for additional platforms (e.g. YouTube Shorts direct URLs, Twitter/X, Vimeo)
- Output formats (SRT, JSON with timestamps)
- A `--output-dir` flag to specify where transcripts are saved
- Better filename collision handling

Please keep pull requests focused — one feature or fix per PR.

---

## License

[MIT](LICENSE)

---

## Acknowledgments

- [openai/whisper](https://github.com/openai/whisper) — speech recognition model
- [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) — video/audio downloader
- [jdepoix/youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) — YouTube caption fetching
- [astral-sh/uv](https://github.com/astral-sh/uv) — Python package runner for the script's inline dependencies
