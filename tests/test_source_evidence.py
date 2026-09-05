"""Offline regression tests: no network, GitHub writes, or device access."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("collector", ROOT / "tools/collect_source_evidence.py")
collector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(collector)


class SourceEvidenceTests(unittest.TestCase):
    def test_twelve_pinned_forks(self):
        lock = collector.load_lock(ROOT / "bringup/source-lock.json")
        self.assertEqual(len(lock["projects"]), 12)
        self.assertEqual({p["branch"] for p in lock["projects"]}, {"lineage-23.2"})

    def check_invalid_lock(self, mutate):
        lock = json.loads((ROOT / "bringup/source-lock.json").read_text())
        mutate(lock)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lock.json"
            path.write_text(json.dumps(lock))
            with self.assertRaises(ValueError):
                collector.load_lock(path)

    def test_rejects_moving_revision(self):
        self.check_invalid_lock(lambda lock: lock["projects"][0].update(revision="lineage-23.2"))

    def test_rejects_external_owner(self):
        self.check_invalid_lock(lambda lock: lock["projects"][0].update(repository="other/device"))

    def test_rejects_duplicate_repository(self):
        self.check_invalid_lock(lambda lock: lock["projects"].__setitem__(1, copy.deepcopy(lock["projects"][0])))

    def test_rejects_missing_repository(self):
        self.check_invalid_lock(lambda lock: lock["projects"].pop())

    def test_rejects_unsafe_workspace_path(self):
        self.check_invalid_lock(lambda lock: lock["projects"][0].update(path="../outside"))

    def test_safe_relative_path(self):
        self.assertEqual(str(collector.safe_path("device/xiaomi/malachite")), "device/xiaomi/malachite")

    def test_rejects_unsafe_export_paths(self):
        for path in ("", ".", "/etc/passwd", "../x", "a/../x", ".git/config", "a//b", "..\\x", "C:/x"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                collector.safe_path(path)

    def test_prebuilt_binaries_not_exported(self):
        for path in ("Image.lz4", "dtbo.img", "vendor_dlkm/wlan.ko"):
            self.assertFalse(collector.selected("prebuilt", path))
        self.assertTrue(collector.selected("prebuilt", "modules.load.vendor"))

    def test_preserves_policy_and_ownership_evidence(self):
        for role in ("kernel", "vendor", "prebuilt", "device-modules"):
            self.assertTrue(collector.selected(role, "nested/AGENTS.md"))
            self.assertTrue(collector.selected(role, ".github/CODEOWNERS"))
        self.assertTrue(collector.selected("sepolicy", "base/vendor/hal_fingerprint.te"))

    def test_kernel_slice_is_explicit(self):
        self.assertTrue(collector.selected("kernel", "build.config.constants"))
        self.assertTrue(collector.selected("kernel", "arch/arm64/configs/gki_defconfig"))
        self.assertFalse(collector.selected("kernel", "drivers/usb/core/hub.c"))
        self.assertTrue(collector.selected("device-modules", "drivers/gpu/BUILD.bazel"))
        self.assertTrue(collector.selected("device-modules", "arch/arm64/boot/dts/mediatek/malachite.dts"))

    def test_build_templates_are_not_mistaken_for_modules(self):
        for name in ("kleaf/BUILD.ko", "kleaf/BUILD.internal", "kleaf/bazel.WORKSPACE"):
            self.assertTrue(collector.selected("kleaf", name))
        self.assertFalse(collector.selected("prebuilt", "vendor_ramdisk/BUILD.ko"))

    def test_fstab_and_interface_sources_are_exported(self):
        self.assertTrue(collector.selected("device", "init/fstab.mt6878"))
        self.assertTrue(collector.selected("hardware", "interfaces/1.0/IFoo.hal"))
        self.assertTrue(collector.selected("hardware", "src/Helper.kt"))

    def test_vendor_excludes_binary_payloads(self):
        self.assertFalse(collector.selected("vendor", "proprietary/vendor/lib64/libcam.so"))
        self.assertTrue(collector.selected("vendor", "proprietary/vendor/etc/vintf/manifest/camera.xml"))


if __name__ == "__main__":
    unittest.main()
