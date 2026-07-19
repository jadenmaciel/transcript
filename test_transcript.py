import contextlib
import io
import subprocess
import sys
import unittest
from pathlib import Path

import transcript


class TranscriptTests(unittest.TestCase):
    def test_detects_supported_platforms(self):
        self.assertEqual(transcript.detect_platform("https://youtube.com/watch?v=abc"), "youtube")
        self.assertEqual(transcript.detect_platform("https://youtu.be/abc"), "youtube")
        self.assertEqual(transcript.detect_platform("https://tiktok.com/@user/video/1"), "tiktok")
        self.assertEqual(transcript.detect_platform("https://instagram.com/reel/1"), "instagram")

    def test_rejects_unsupported_platform(self):
        self.assertIsNone(transcript.detect_platform("https://example.com/video"))

    def test_extracts_youtube_video_ids(self):
        video_id = "abcDEF_123-"
        self.assertEqual(transcript.extract_video_id(f"https://youtube.com/watch?v={video_id}"), video_id)
        self.assertEqual(transcript.extract_video_id(f"https://youtu.be/{video_id}"), video_id)
        self.assertEqual(transcript.extract_video_id(f"https://youtube.com/shorts/{video_id}"), video_id)
        self.assertEqual(transcript.extract_video_id(video_id), video_id)
        self.assertIsNone(transcript.extract_video_id("not-a-video-id"))

    def test_sanitizes_filenames(self):
        self.assertEqual(transcript.sanitize_filename('  A  <bad>: "title"?  '), "A bad title")
        self.assertEqual(transcript.sanitize_filename("<>"), "transcript")
        self.assertEqual(len(transcript.sanitize_filename("x" * 250)), 200)

    def test_unsupported_url_does_not_start_network_work(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            transcript.process_url("https://example.com/video", Path("."), "base")
        self.assertIn("Unrecognized platform", output.getvalue())

    def test_cli_help_runs_without_downloading_dependencies(self):
        result = subprocess.run(
            [sys.executable, "transcript.py", "--help"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Transcribe YouTube", result.stdout)


if __name__ == "__main__":
    unittest.main()
