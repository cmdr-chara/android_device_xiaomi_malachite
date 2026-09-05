"""Offline source-lock/local-manifest relationship checks."""
import copy
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from collect_source_evidence import load_lock
from workspace_manifest import render


class WorkspaceManifestTests(unittest.TestCase):
    def setUp(self):
        self.lock = load_lock(ROOT / "bringup/source-lock.json")
        self.root = ET.fromstring(render(self.lock))

    def test_checked_in_manifest_is_current(self):
        self.assertEqual((ROOT / "bringup/android.xml").read_text(), render(self.lock))

    def test_exact_seven_owned_android_revisions(self):
        actual = {(p.get("name"), p.get("path"), p.get("revision")) for p in self.root.findall("project")}
        expected = {(p["repository"], p["path"], p["revision"]) for p in self.lock["projects"] if p["workspace"] == "android"}
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 7)

    def test_removals_only_cover_replaced_paths(self):
        removals = self.root.findall("remove-project")
        self.assertEqual({p.get("path") for p in removals}, {p.get("path") for p in self.root.findall("project")})
        self.assertTrue(all(p.get("optional") == "true" and p.get("name") is None for p in removals))

    def test_no_kernel_workspace_or_toolchain_replacement(self):
        paths = {p.get("path") for p in self.root.findall("project")}
        self.assertFalse(any(p.startswith(("kernel/", "kernel-", "prebuilts/", "build/")) for p in paths))
        self.assertIsNone(self.root.find("default"))
        self.assertIsNone(self.root.find("superproject"))

    def test_duplicate_android_path_rejected(self):
        lock = copy.deepcopy(self.lock)
        lock["projects"][1]["path"] = lock["projects"][0]["path"]
        with self.assertRaises(ValueError):
            render(lock)


if __name__ == "__main__":
    unittest.main()
