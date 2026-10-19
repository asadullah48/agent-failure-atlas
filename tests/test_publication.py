"""Publication guard: inspect every tracked file, including staged additions."""
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
# A boundary avoids treating the last letter of an HTTP scheme as a drive.
LOCAL_PATH = re.compile(rb"(?i)(?<![a-z0-9_])[a-z]:[\\/]|(?<![a-z0-9_])Users[\\/]Asad(?![a-z0-9_])")


class PublicationTests(unittest.TestCase):
    def test_tracked_files_have_no_absolute_local_paths(self):
        names = subprocess.check_output(
            ["git", "ls-files", "-z"], cwd=ROOT).split(b"\0")
        findings = []
        for raw_name in names:
            if not raw_name:
                continue
            name = raw_name.decode("utf-8")
            data = (ROOT / name).read_bytes()
            for match in LOCAL_PATH.finditer(data):
                line = data[:match.start()].count(b"\n") + 1
                findings.append(f"{name}:{line}")
        self.assertEqual(findings, [], "Absolute local paths in: " + ", ".join(findings))
