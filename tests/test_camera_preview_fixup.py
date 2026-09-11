"""Fail-closed tests for the Xiaomi Camera still-preview color-space patch."""

from hashlib import sha256
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile
import importlib.util
import struct
import unittest
import zlib


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("camera_fixups", ROOT / "blob_fixups_camera.py")
fixups = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fixups)


def refresh_dex_header(data):
    import hashlib

    data[12:32] = hashlib.sha1(data[32:]).digest()
    data[8:12] = struct.pack("<I", zlib.adler32(data[12:]) & 0xFFFFFFFF)


def sample_dex():
    data = bytearray(b"dex\n039\0" + bytes(24) + b"before-method")
    data.extend(fixups.CAMERA_PREVIEW_PATCH_BEFORE)
    data.extend(b"after-method")
    refresh_dex_header(data)
    return bytes(data)


class CameraPreviewFixupTests(unittest.TestCase):
    def test_dex_patch_changes_only_the_instruction_and_header_authenticators(self):
        original = sample_dex()
        expected = sha256(original).hexdigest()
        patched = fixups.patch_camera_preview_dex(original, expected)

        patch_site = original.index(fixups.CAMERA_PREVIEW_PATCH_BEFORE) + 6
        differences = {
            index for index, values in enumerate(zip(original, patched))
            if values[0] != values[1]
        }
        self.assertLessEqual(differences, set(range(8, 32)) | {patch_site})
        self.assertIn(patch_site, differences)
        self.assertEqual(original[patch_site:patch_site + 2], bytes.fromhex("0a00"))
        self.assertEqual(patched[patch_site:patch_site + 2], bytes.fromhex("1200"))
        self.assertEqual(
            fixups.patch_camera_preview_dex(patched, expected), patched
        )

    def test_apk_patch_updates_the_stored_dex_crc_and_preserves_other_entries(self):
        original_dex = sample_dex()
        archive_bytes = BytesIO()
        with ZipFile(archive_bytes, "w") as archive:
            archive.writestr("AndroidManifest.xml", b"manifest", ZIP_STORED)
            archive.writestr("classes2.dex", original_dex, ZIP_STORED)
            archive.writestr("assets/untouched", b"untouched", ZIP_STORED)

        patched_apk = fixups.patch_camera_preview_apk(
            archive_bytes.getvalue(), sha256(original_dex).hexdigest()
        )
        self.assertEqual(len(patched_apk), len(archive_bytes.getvalue()))
        with ZipFile(BytesIO(patched_apk)) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(archive.read("assets/untouched"), b"untouched")
            patched_dex = archive.read("classes2.dex")
        self.assertEqual(
            patched_dex.count(fixups.CAMERA_PREVIEW_PATCH_AFTER), 1
        )
        self.assertEqual(
            fixups.patch_camera_preview_apk(
                patched_apk, sha256(original_dex).hexdigest()
            ),
            patched_apk,
        )

    def test_changed_dex_is_rejected_before_writing_a_partial_patch(self):
        changed = bytearray(sample_dex())
        changed[40] ^= 1
        refresh_dex_header(changed)
        with self.assertRaisesRegex(ValueError, "Unrecognized Xiaomi Camera"):
            fixups.patch_camera_preview_dex(
                changed, sha256(sample_dex()).hexdigest()
            )


if __name__ == "__main__":
    unittest.main()
