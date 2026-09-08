import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "bringup" / "candidates"
PREVIOUS_LOCK = CANDIDATES / "2026-09-06-merged.json"
LOCK = CANDIDATES / "2026-09-08-build-fixes.json"
MANIFEST = CANDIDATES / "2026-09-08-build-fixes.xml"

XIAOMI_REPOSITORY = "cmdr-chara/android_hardware_xiaomi"
EXPECTED_XIAOMI_BRANCH = "revival/build-fixes-20260908"
EXPECTED_XIAOMI_REVISION = "f51cd439b3465f6de05d8873aa15aa996bf0308b"


class BuildFixCandidateTests(unittest.TestCase):
    def setUp(self):
        self.previous = json.loads(PREVIOUS_LOCK.read_text())
        self.candidate = json.loads(LOCK.read_text())

    def test_only_xiaomi_hardware_pin_changes(self):
        previous = {p["repository"]: p for p in self.previous["projects"]}
        candidate = {p["repository"]: p for p in self.candidate["projects"]}
        self.assertEqual(candidate.keys(), previous.keys())

        for repository, project in candidate.items():
            if repository == XIAOMI_REPOSITORY:
                self.assertEqual(project["branch"], EXPECTED_XIAOMI_BRANCH)
                self.assertEqual(project["revision"], EXPECTED_XIAOMI_REVISION)
                expected = dict(previous[repository])
                expected["branch"] = EXPECTED_XIAOMI_BRANCH
                expected["revision"] = EXPECTED_XIAOMI_REVISION
                self.assertEqual(project, expected)
            else:
                self.assertEqual(project, previous[repository])

    def test_candidate_is_build_only(self):
        self.assertEqual(self.candidate["purpose"], "first-full-android-build")
        self.assertEqual(self.candidate["recorded_on"], "2026-09-08")
        claim = self.candidate["claim"].lower()
        self.assertIn("not boot", claim)
        self.assertIn("avb", claim)

    def test_android_manifest_matches_lock(self):
        root = ET.parse(MANIFEST).getroot()
        actual = [
            (node.attrib["name"], node.attrib["path"], node.attrib["revision"], node.attrib["upstream"])
            for node in root.findall("project")
        ]
        expected = [
            (p["repository"], p["path"], p["revision"], "refs/heads/" + p["branch"])
            for p in self.candidate["projects"]
            if p["workspace"] == "android"
        ]
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 7)


if __name__ == "__main__":
    unittest.main()
