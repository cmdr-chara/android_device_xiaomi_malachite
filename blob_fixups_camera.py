# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0

"""Verified GraphicBuffer allocation sites in malachite OS3 camera blobs."""

from hashlib import sha1, sha256
from io import BytesIO
from pathlib import Path
from struct import pack, unpack_from
from zipfile import ZIP_STORED, ZipFile
from zlib import adler32, crc32


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


# Xiaomi Camera 6.2.000660.6 enables a P3/P3 EGL preview whenever Android
# reports a wide-gamut panel. The malachite composer cannot mix color spaces,
# so that preview bypasses the required conversion and renders red as pink.
# Replace only the move-result after isScreenWideColorGamut() with const/4 v0,0;
# the existing branch then returns the app's canonical sRGB/sRGB description.
CAMERA_PREVIEW_DEX_SHA256 = (
    "30f74ea2488299105c7bc9e352c7fcd6cb3a3134435bba5ce8fd6a906e61d1b3"
)
CAMERA_PREVIEW_PATCH_BEFORE = bytes.fromhex(
    "6e1063200000"  # invoke-virtual isScreenWideColorGamut()
    "0a00"          # move-result v0
    "38000f00"      # if-eqz v0, return_srgb
    "54205f00"
    "62016300"
    "33100900"
    "62006400"
    "54216000"
    "33010300"
    "1102"
    "62026100"
    "1102"
)
CAMERA_PREVIEW_PATCH_AFTER = (
    CAMERA_PREVIEW_PATCH_BEFORE[:6]
    + bytes.fromhex("1200")  # const/4 v0, 0
    + CAMERA_PREVIEW_PATCH_BEFORE[8:]
)


def _refresh_dex_header(data):
    data[12:32] = sha1(data[32:]).digest()
    data[8:12] = pack("<I", adler32(data[12:]) & 0xFFFFFFFF)


def patch_camera_preview_dex(data, expected_sha256=CAMERA_PREVIEW_DEX_SHA256):
    """Patch the verified still-preview method and preserve every other byte."""
    if data[:8] != b"dex\n039\0":
        raise ValueError("Unexpected Xiaomi Camera classes2.dex format")

    before_count = data.count(CAMERA_PREVIEW_PATCH_BEFORE)
    after_count = data.count(CAMERA_PREVIEW_PATCH_AFTER)
    if before_count + after_count != 1:
        raise ValueError(
            "Expected one Xiaomi Camera preview color-space instruction sequence"
        )

    normalized = bytearray(data)
    if after_count:
        offset = normalized.index(CAMERA_PREVIEW_PATCH_AFTER)
        normalized[offset:offset + len(CAMERA_PREVIEW_PATCH_AFTER)] = (
            CAMERA_PREVIEW_PATCH_BEFORE
        )
        _refresh_dex_header(normalized)
    else:
        offset = normalized.index(CAMERA_PREVIEW_PATCH_BEFORE)

    if sha256(normalized).hexdigest() != expected_sha256:
        raise ValueError("Unrecognized Xiaomi Camera classes2.dex")

    normalized[offset:offset + len(CAMERA_PREVIEW_PATCH_BEFORE)] = (
        CAMERA_PREVIEW_PATCH_AFTER
    )
    _refresh_dex_header(normalized)
    return bytes(normalized)


def patch_camera_preview_apk(data, expected_sha256=CAMERA_PREVIEW_DEX_SHA256):
    """Patch the stored classes2.dex entry without rewriting unrelated entries."""
    with ZipFile(BytesIO(data)) as archive:
        entries = [info for info in archive.infolist() if info.filename == "classes2.dex"]
        if len(entries) != 1:
            raise ValueError("Expected exactly one classes2.dex in Xiaomi Camera")
        entry = entries[0]
        if entry.compress_type != ZIP_STORED or entry.flag_bits & 0x08:
            raise ValueError("Xiaomi Camera classes2.dex must be stored without a descriptor")
        original_dex = archive.read(entry)

    patched_dex = patch_camera_preview_dex(original_dex, expected_sha256)
    if len(patched_dex) != len(original_dex):
        raise ValueError("Xiaomi Camera DEX patch changed the entry size")

    patched = bytearray(data)
    if patched[entry.header_offset:entry.header_offset + 4] != b"PK\x03\x04":
        raise ValueError("Invalid Xiaomi Camera ZIP local header")
    name_length, extra_length = unpack_from("<HH", patched, entry.header_offset + 26)
    data_offset = entry.header_offset + 30 + name_length + extra_length
    if patched[data_offset:data_offset + len(original_dex)] != original_dex:
        raise ValueError("Xiaomi Camera classes2.dex local entry mismatch")
    patched[data_offset:data_offset + len(patched_dex)] = patched_dex

    dex_crc = crc32(patched_dex) & 0xFFFFFFFF
    patched[entry.header_offset + 14:entry.header_offset + 18] = pack("<I", dex_crc)

    eocd = patched.rfind(b"PK\x05\x06")
    if eocd < 0:
        raise ValueError("Missing Xiaomi Camera ZIP end record")
    entry_count = unpack_from("<H", patched, eocd + 10)[0]
    central_offset = unpack_from("<I", patched, eocd + 16)[0]
    cursor = central_offset
    central_matches = 0
    for _ in range(entry_count):
        if patched[cursor:cursor + 4] != b"PK\x01\x02":
            raise ValueError("Invalid Xiaomi Camera ZIP central directory")
        central_name_length, central_extra_length, comment_length = unpack_from(
            "<HHH", patched, cursor + 28
        )
        local_offset = unpack_from("<I", patched, cursor + 42)[0]
        name = bytes(patched[cursor + 46:cursor + 46 + central_name_length])
        if name == b"classes2.dex" and local_offset == entry.header_offset:
            patched[cursor + 16:cursor + 20] = pack("<I", dex_crc)
            central_matches += 1
        cursor += 46 + central_name_length + central_extra_length + comment_length
    if central_matches != 1:
        raise ValueError("Could not identify Xiaomi Camera classes2.dex central entry")

    with ZipFile(BytesIO(patched)) as archive:
        if archive.read("classes2.dex") != patched_dex:
            raise ValueError("Xiaomi Camera classes2.dex ZIP verification failed")
    return bytes(patched)


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


def blob_fixup_camera_preview_srgb(ctx, file, file_path, *args, **kwargs):
    path = Path(file_path)
    path.write_bytes(patch_camera_preview_apk(path.read_bytes()))
