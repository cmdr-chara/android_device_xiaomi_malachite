import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "audit_target_files.py"
spec = importlib.util.spec_from_file_location("audit_target_files", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def make_zip(entries):
    tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    tmp.close()
    with zipfile.ZipFile(tmp.name, "w", compression=zipfile.ZIP_STORED) as zf:
        for name, value in entries:
            zf.writestr(name, value)
    return tmp.name


SAFE_AB = "\n".join(sorted(mod.EXPECTED_AB_PARTITIONS)) + "\n"


class TargetFilesAuditTests(unittest.TestCase):
    def test_safe_archive_passes(self):
        path = make_zip([
            ("META/ab_partitions.txt", SAFE_AB),
            ("META/misc_info.txt", "avb_enable=true\navb_vbmeta_args=--flags 3\n"),
            ("IMAGES/boot.img", b"x" * 1024),
            ("IMAGES/init_boot.img", b"x" * 1024),
            ("IMAGES/vendor_boot.img", b"x" * 1024),
        ])
        result = mod.audit(path)
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(any("flags 3" in item for item in result["warnings"]))

    def test_forbidden_ab_partition_fails(self):
        path = make_zip([("META/ab_partitions.txt", SAFE_AB + "dtbo\n")])
        result = mod.audit(path)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("forbidden A/B" in item for item in result["errors"]))

    def test_unexpected_partition_fails(self):
        path = make_zip([("META/ab_partitions.txt", SAFE_AB + "vendor_kernel_boot\n")])
        result = mod.audit(path)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("unexpected A/B" in item for item in result["errors"]))

    def test_missing_expected_partition_fails(self):
        reduced = "\n".join(sorted(mod.EXPECTED_AB_PARTITIONS - {"vendor_boot"})) + "\n"
        path = make_zip([("META/ab_partitions.txt", reduced)])
        result = mod.audit(path)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("expected A/B" in item for item in result["errors"]))

    def test_radio_payload_fails(self):
        path = make_zip([
            ("META/ab_partitions.txt", SAFE_AB),
            ("RADIO/modem.img", b"firmware"),
        ])
        result = mod.audit(path)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("RADIO payload" in item for item in result["errors"]))

    def test_forbidden_image_fails(self):
        path = make_zip([
            ("META/ab_partitions.txt", SAFE_AB),
            ("IMAGES/dtbo.img", b"x"),
        ])
        result = mod.audit(path)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("forbidden image" in item for item in result["errors"]))

    def test_oversized_boot_fails(self):
        path = make_zip([
            ("META/ab_partitions.txt", SAFE_AB),
            ("IMAGES/boot.img", b"x" * (mod.MAX_IMAGE_BYTES["boot"] + 1)),
        ])
        result = mod.audit(path)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("exceeds configured" in item for item in result["errors"]))

    def test_unsafe_zip_path_fails(self):
        path = make_zip([
            ("META/ab_partitions.txt", SAFE_AB),
            ("../RADIO/modem.img", b"x"),
        ])
        result = mod.audit(path)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("unsafe paths" in item for item in result["errors"]))


if __name__ == "__main__":
    unittest.main()
