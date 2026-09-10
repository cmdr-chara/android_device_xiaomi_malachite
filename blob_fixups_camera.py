# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0

"""Verified GraphicBuffer allocation sites in malachite OS3 camera blobs."""

from hashlib import sha256
from pathlib import Path


# OS3.0.10.0.WOOMIXM compiled these constructors with sizeof(GraphicBuffer)
# == 0x100. The platform libui DependencyMonitor increases it to 0xd30.
# These are FILE offsets, verified against the executable ELF LOAD segments
# and the following operator new / GraphicBuffer constructor calls.
GRAPHIC_BUFFER_FIXUPS = {
    "vendor/lib64/libcom.xiaomi.grallocutils.so": (
        "15c7204cf14143100a1d2259eaa761dd408df1cf8e1b4074231c268abb6f264c",
        (0x2108, 0x2220, 0x2480),
    ),
    "odm/lib64/camera/plugins/com.xiaomi.plugin.filter.so": (
        "362b3aca6e19be2d2faa868cba9862767e70c510016e356b173ceea936772663",
        (0xA880, 0xA8CC),
    ),
    "odm/lib64/camera/plugins/com.xiaomi.plugin.videofilter.so": (
        "5a4d083006e163de96e600b4eb28a8790af1909c937abd1cafe71445eeca7258",
        (0xAF38, 0xAFA0),
    ),
}

OLD_ALLOCATION = bytes.fromhex("00208052")  # mov w0, #0x100
NEW_ALLOCATION = bytes.fromhex("00a68152")  # mov w0, #0xd30


def patch_graphic_buffer_allocations(data, expected_sha256, offsets):
    """Return a complete verified patch; tolerate only an exact prior patch."""
    original = bytearray(data)
    for offset in offsets:
        instruction = original[offset:offset + 4]
        if instruction not in (OLD_ALLOCATION, NEW_ALLOCATION):
            raise ValueError(f"Unexpected GraphicBuffer instruction at {offset:#x}")
        original[offset:offset + 4] = OLD_ALLOCATION
    if sha256(original).hexdigest() != expected_sha256:
        raise ValueError("Unrecognized camera blob: review its GraphicBuffer ABI before patching")
    for offset in offsets:
        original[offset:offset + 4] = NEW_ALLOCATION
    return bytes(original)


def blob_fixup_camera_graphic_buffer_size(ctx, file, file_path, *args, **kwargs):
    expected_sha256, offsets = GRAPHIC_BUFFER_FIXUPS[file.dst]
    path = Path(file_path)
    patched = patch_graphic_buffer_allocations(path.read_bytes(), expected_sha256, offsets)
    path.write_bytes(patched)
