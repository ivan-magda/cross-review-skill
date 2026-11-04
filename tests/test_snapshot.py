"""Real-Git checks for content changes hidden by an unchanged status listing."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skills/cross-review/scripts/snapshot.py"


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cross-review-snapshot-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Snapshot test")
        self.tracked = self.repo / "tracked.txt"
        self.tracked.write_text("base\n")
        self.git("add", ".")
        self.git("-c", "commit.gpgsign=false", "commit", "-qm", "base")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args])

    def snapshot_bytes(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(self.repo)], capture_output=True
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        return result.stdout

    def snapshot(self):
        return json.loads(self.snapshot_bytes())

    def test_already_modified_file_edit_changes_snapshot_despite_same_status(self):
        # Omitting the unstaged diff would miss this M-to-M edit.
        self.tracked.write_text("first edit\n")
        before = self.snapshot()
        self.tracked.write_text("second edit\n")
        after = self.snapshot()
        self.assertEqual(before["status_porcelain_v1_z"], after["status_porcelain_v1_z"])
        self.assertNotEqual(before["unstaged_diff_sha256"], after["unstaged_diff_sha256"])

    def test_index_and_untracked_content_are_observed_independently(self):
        # A worktree-only snapshot loses staged content and untracked rewrites.
        self.tracked.write_text("staged first\n")
        self.git("add", "tracked.txt")
        self.tracked.write_text("unstaged\n")
        untracked = self.repo / "new.txt"
        untracked.write_text("first\n")
        before = self.snapshot()
        self.tracked.write_text("staged second\n")
        self.git("add", "tracked.txt")
        self.tracked.write_text("unstaged\n")
        staged = self.snapshot()
        self.assertEqual(before["status_porcelain_v1_z"], staged["status_porcelain_v1_z"])
        self.assertNotEqual(before["index_diff_sha256"], staged["index_diff_sha256"])
        self.assertNotEqual(before["unstaged_diff_sha256"], staged["unstaged_diff_sha256"])
        untracked.write_text("second\n")
        after = self.snapshot()
        self.assertEqual(staged["status_porcelain_v1_z"], after["status_porcelain_v1_z"])
        self.assertNotEqual(staged["untracked"], after["untracked"])
        self.assertEqual(before["head"], self.git("rev-parse", "HEAD").decode().strip())

    def test_stable_snapshot_preserves_weird_names_and_hashes_symlink_target(self):
        # Splitting on newlines or following symlinks breaks this contract.
        weird = "odd\tline\nname"
        (self.repo / weird).write_bytes(b"binary\x00content\xff")
        outside = self.root / "outside.txt"
        outside.write_text("outside first\n")
        link = self.repo / "link"
        os.symlink("../outside.txt", link)
        before_bytes = self.snapshot_bytes()
        self.assertEqual(before_bytes, self.snapshot_bytes())
        before = json.loads(before_bytes)
        self.assertEqual({item["path"] for item in before["untracked"]}, {weird, "link"})
        outside.write_text("outside second\n")
        self.assertEqual(before_bytes, self.snapshot_bytes())
        link.unlink()
        os.symlink("../missing.txt", link)
        after = self.snapshot()
        self.assertEqual(before["status_porcelain_v1_z"], after["status_porcelain_v1_z"])
        self.assertNotEqual(before["untracked"], after["untracked"])

    def test_untracked_nested_repository_is_marked_without_reading_its_contents(self):
        # Git emits nested/ as a directory; treating every entry as a file aborts.
        self.git("init", "-q", "nested")
        nested_file = self.repo / "nested" / "file.txt"
        nested_file.write_text("nested base\n")
        self.git("-C", "nested", "add", ".")
        self.git(
            "-C", "nested", "-c", "user.name=Snapshot test",
            "-c", "user.email=test@example.invalid", "-c", "commit.gpgsign=false",
            "commit", "-qm", "nested base",
        )
        before = self.snapshot()
        self.assertEqual(before["untracked"], [{"path": "nested/", "type": "nested-repository"}])
        nested_file.write_text("nested edit outside coverage\n")
        self.assertEqual(before, self.snapshot())


if __name__ == "__main__":
    unittest.main()
