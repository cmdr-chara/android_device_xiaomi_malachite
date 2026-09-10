"""Fail closed when the OS3 camera allocation ABI or blob identity changes."""

from hashlib import sha256
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("camera_fixups", ROOT / "blob_fixups_camera.py")
fixups = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fixups)


class CameraGraphicBufferFixupTests(unittest.TestCase):
    def setUp(self):
        self.original = b"prefix!!" + fixups.OLD_ALLOCATION + b"untouched bytes!" + fixups.OLD_ALLOCATION
        self.offsets = (8, 28)
        self.digest = sha256(self.original).hexdigest()

    def test_only_verified_allocations_change_and_reapplication_is_identical(self):
        patched = fixups.patch_graphic_buffer_allocations(self.original, self.digest, self.offsets)
        self.assertEqual(len(patched), len(self.original))
        self.assertEqual(patched[:8], self.original[:8])
        self.assertEqual(patched[12:28], self.original[12:28])
        for offset in self.offsets:
            self.assertEqual(patched[offset:offset + 4], fixups.NEW_ALLOCATION)
        self.assertEqual(
            fixups.patch_graphic_buffer_allocations(patched, self.digest, self.offsets), patched)

    def test_rejects_changed_blob_even_when_instructions_still_match(self):
        changed = b"X" + self.original[1:]
        with self.assertRaisesRegex(ValueError, "Unrecognized camera blob"):
            fixups.patch_graphic_buffer_allocations(changed, self.digest, self.offsets)

    def test_rejects_wrong_instruction_and_truncation(self):
        for data in (self.original[:8] + b"oops" + self.original[12:], self.original[:30]):
            with self.subTest(data=data), self.assertRaisesRegex(ValueError, "instruction"):
                fixups.patch_graphic_buffer_allocations(data, self.digest, self.offsets)

    def test_callback_does_not_modify_an_unrecognized_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unrecognized.so"
            path.write_bytes(self.original)
            with self.assertRaises(ValueError):
                fixups.blob_fixup_camera_graphic_buffer_size(
                    None, SimpleNamespace(dst="vendor/lib64/libcom.xiaomi.grallocutils.so"), path)
            self.assertEqual(path.read_bytes(), self.original)


if __name__ == "__main__":
    unittest.main()
