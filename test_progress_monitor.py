import os
import tempfile
import time
import unittest
from pathlib import Path

from downloader import _find_current_download_part, _format_download_rate


class DownloadProgressTests(unittest.TestCase):
    def test_current_download_file_wins_over_stale_partial_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            started_at = time.time()
            stale = Path(temp_dir) / "old.part"
            current = Path(temp_dir) / "current.part"
            stale.write_bytes(b"x" * 100)
            current.touch()
            os.utime(stale, (started_at - 10, started_at - 10))
            os.utime(current, (started_at + 1, started_at + 1))

            self.assertEqual(_find_current_download_part([Path(temp_dir)], started_at), current)

    def test_empty_current_file_is_reported_as_waiting_after_stall(self):
        self.assertEqual(_format_download_rate(0, 3), "Veri bekleniyor (3 sn)")

    def test_active_download_shows_transfer_rate(self):
        self.assertEqual(_format_download_rate(8.25, 0), "8.2 MB/s")


if __name__ == "__main__":
    unittest.main()
