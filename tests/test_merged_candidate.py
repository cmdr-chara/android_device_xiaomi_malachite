import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "bringup" / "candidates" / "2026-09-06-merged.json"
MANIFEST = ROOT / "bringup" / "candidates" / "2026-09-06-merged.xml"
BASELINE = ROOT / "bringup" / "source-lock.json"


class MergedCandidateTests(unittest.TestCase):
    def setUp(self):
        self.candidate = json.loads(LOCK.read_text())
        self.baseline = json.loads(BASELINE.read_text())

    def test_exact_twelve_repository_identity(self):
        candidate = self.candidate["projects"]
        baseline = {p["repository"]: p for p in self.baseline["projects"]}
        self.assertEqual(len(candidate), 12)
        self.assertEqual({p["repository"] for p in candidate}, set(baseline))
        for project in candidate:
            original = baseline[project["repository"]]
            self.assertEqual(project["workspace"], original["workspace"])
            self.assertEqual(project["path"], original["path"])
            self.assertEqual(project["role"], original["role"])
            self.assertRegex(project["revision"], r"^[0-9a-f]{40}$")

    def test_candidate_is_build_only(self):
        self.assertEqual(self.candidate["purpose"], "first-full-android-build")
        claim = self.candidate["claim"].lower()
        self.assertIn("not boot", claim)
        self.assertIn("not", claim)

    def test_android_manifest_matches_lock(self):
        root = ET.parse(MANIFEST).getroot()
        actual = [
            (node.attrib["name"], node.attrib["path"], node.attrib["revision"], node.attrib["upstream"])
            for node in root.findall("project")
        ]
        expected = [
            (p["repository"], p["path"], p["revision"], "refs/heads/" + p["branch"])
            for p in self.candidate["projects"] if p["workspace"] == "android"
        ]
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 7)

    def test_first_build_keeps_prebuilt_kernel_path(self):
        board = (ROOT / "BoardConfig.mk").read_text()
        self.assertIn("TARGET_FORCE_PREBUILT_KERNEL := true", board)
        self.assertIn("TARGET_PREBUILT_KERNEL := $(DEVICE_PATH)-kernel/Image.lz4", board)
        self.assertNotIn("BOARD_PREBUILT_DTBOIMAGE", board)


if __name__ == "__main__":
    unittest.main()
