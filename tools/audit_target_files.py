#!/usr/bin/env python3
"""Read-only safety audit for malachite target-files archives.

The goal is intentionally narrow: reject unexpected OTA partitions and any
low-level firmware payload before a physical-device test is considered. This
script does not certify AVB policy, runtime compatibility, or bootability.
"""

from __future__ import annotations

import argparse
import json
import posixpath
import sys
import zipfile
from pathlib import PurePosixPath

EXPECTED_AB_PARTITIONS = {
    "boot",
    "init_boot",
    "odm",
    "odm_dlkm",
    "product",
    "system",
    "system_dlkm",
    "system_ext",
    "vendor",
    "vendor_boot",
    "vendor_dlkm",
    "vbmeta",
    "vbmeta_system",
    "vbmeta_vendor",
}

FORBIDDEN_PARTITIONS = {
    "preloader",
    "lk",
    "lk1",
    "lk2",
    "bootloader",
    "bootloader2",
    "pgpt",
    "sgpt",
    "gpt",
    "seccfg",
    "nvram",
    "nvdata",
    "nvcfg",
    "protect1",
    "protect2",
    "persist",
    "proinfo",
    "frp",
    "efuse",
    "otp",
    "modem",
    "md1dsp",
    "md1arm7",
    "md3img",
    "tee1",
    "tee2",
    "scp1",
    "scp2",
    "sspm1",
    "sspm2",
    "dpm1",
    "dpm2",
    "mcupm1",
    "mcupm2",
    "ccu",
    "vcp",
    "gpueb",
    "mcf_ota",
    "mvpu_algo1",
    "mvpu_algo2",
    "apusys1",
    "apusys2",
    "spmfw",
    "pi_img",
    "boot_para",
    "dtbo",
    "odmdtbo",
    "logo",
    "para",
    "expdb",
    "connsys_wifi",
    "connsys_bt",
}

MAX_IMAGE_BYTES = {
    "boot": 67_108_864,
    "init_boot": 8_388_608,
    "vendor_boot": 67_108_864,
    "super": 9_125_756_928,
}


def _safe_name(name: str) -> bool:
    path = PurePosixPath(name)
    return bool(name) and not path.is_absolute() and ".." not in path.parts and "\\" not in name


def _partition_from_image_name(name: str) -> str | None:
    base = posixpath.basename(name)
    if not base.endswith(".img"):
        return None
    return base[:-4]


def audit(path: str) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    observed_images: dict[str, int] = {}

    try:
        archive = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as exc:
        return {"status": "FAIL", "errors": [f"cannot open target-files archive: {exc}"], "warnings": []}

    with archive:
        infos = archive.infolist()
        names = [i.filename for i in infos]
        if len(names) != len(set(names)):
            errors.append("archive contains duplicate entry names")

        unsafe = sorted(name for name in names if not _safe_name(name))
        if unsafe:
            errors.append(f"archive contains unsafe paths: {unsafe[:8]}")

        try:
            raw_ab = archive.read("META/ab_partitions.txt").decode("utf-8")
        except KeyError:
            errors.append("META/ab_partitions.txt is missing")
            ab_partitions: set[str] = set()
        except UnicodeDecodeError:
            errors.append("META/ab_partitions.txt is not UTF-8")
            ab_partitions = set()
        else:
            ab_partitions = {line.strip() for line in raw_ab.splitlines() if line.strip()}
            forbidden_ab = sorted(ab_partitions & FORBIDDEN_PARTITIONS)
            unexpected_ab = sorted(ab_partitions - EXPECTED_AB_PARTITIONS)
            missing_ab = sorted(EXPECTED_AB_PARTITIONS - ab_partitions)
            if forbidden_ab:
                errors.append(f"forbidden A/B partitions present: {forbidden_ab}")
            if unexpected_ab:
                errors.append(f"unexpected A/B partitions present: {unexpected_ab}")
            if missing_ab:
                errors.append(f"expected A/B partitions missing: {missing_ab}")

        radio_files = sorted(
            i.filename for i in infos if i.filename.startswith("RADIO/") and not i.is_dir()
        )
        if radio_files:
            errors.append(f"RADIO payload is non-empty: {radio_files[:12]}")

        for info in infos:
            if info.is_dir():
                continue
            if not (info.filename.startswith("IMAGES/") or info.filename.startswith("PREBUILT_IMAGES/")):
                continue
            partition = _partition_from_image_name(info.filename)
            if partition is None:
                continue
            observed_images[partition] = info.file_size
            if partition in FORBIDDEN_PARTITIONS:
                errors.append(f"forbidden image packaged: {info.filename}")
            limit = MAX_IMAGE_BYTES.get(partition)
            if limit is not None and info.file_size > limit:
                errors.append(
                    f"{partition}.img exceeds configured partition size: {info.file_size} > {limit}"
                )

        try:
            misc = archive.read("META/misc_info.txt").decode("utf-8", errors="replace")
        except KeyError:
            warnings.append("META/misc_info.txt is missing; AVB policy was not inspected")
        else:
            if "--flags 3" in misc:
                warnings.append("AVB vbmeta flags 3 remain present; release signing policy is still BLOCKED")
            if "testkey_rsa4096.pem" in misc:
                warnings.append("AVB test key reference remains present; release signing policy is still BLOCKED")

    status = "PASS" if not errors else "FAIL"
    return {
        "status": status,
        "ab_partitions": sorted(ab_partitions),
        "observed_images": observed_images,
        "errors": errors,
        "warnings": warnings,
        "scope": "hard-brick-risk packaging guard only; not bootability or release certification",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target_files", help="Path to a generated target-files ZIP")
    args = parser.parse_args()
    result = audit(args.target_files)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
