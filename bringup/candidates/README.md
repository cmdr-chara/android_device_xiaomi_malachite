# Malachite build candidates

Two snapshots are kept deliberately:

- `2026-09-06.json` / `2026-09-06.xml` — historical pre-merge review snapshot. Keep for evidence; do not use it for a fresh build.
- `2026-09-06-merged.json` / `2026-09-06-merged.xml` — exact post-merge inputs for the first full Android build.

Neither snapshot is boot, hardware, AVB-release, or daily-driver certification. No phone operation is authorized by these files.

## First full Android build

Use `2026-09-06-merged.xml` as the malachite local manifest in an otherwise complete LineageOS `lineage-23.2` checkout. It replaces exactly seven owned Android paths with immutable revisions. Preserve the surrounding `repo manifest -r`; upstream Lineage/AOSP/toolchain projects are outside this device-only lock.

The device-tree revision intentionally points to `9f4b67e8a6859b3b0a939c5a99efa75e840e2581`. That commit contains all merged runtime changes plus the read-only target-files audit. Later commits in this branch only add lock/tests/documentation, avoiding a self-referential source pin.

For this first Android build, keep the existing prebuilt kernel path. `TARGET_FORCE_PREBUILT_KERNEL := true` remains intentional. Do not switch Android packaging to the source kernel merely because the separate KMI candidate compiled successfully.

## Post-build hard-brick packaging check

After a successful target-files build, run:

```sh
python3 device/xiaomi/malachite/tools/audit_target_files.py <path-to-target_files.zip>
```

The audit fails if the package adds an unexpected A/B partition, contains a non-empty `RADIO/` payload, packages a forbidden low-level image such as DTBO/modem/bootloader/calibration/security data, contains unsafe ZIP paths, or exceeds the configured boot/init_boot/vendor_boot/super image limits.

The expected A/B set is limited to the current Android/dynamic partitions plus boot, init_boot, vendor_boot and vbmeta chain. The guard intentionally treats AVB `--flags 3` and test-key references as warnings because they are already-known release blockers; a packaging PASS is **not** AVB production approval or bootability proof.

## Preserved compatibility boundaries

Keep the OS2.0.208.0.VOOMIXM camera userspace baseline, DTBO deployment exclusion, current partition layout and firmware separation. Do not downgrade/mix regional firmware, replace modem/bootloader components, remove required module load entries, or disable verification to make a build/test pass.

The persistent filesystems `protect1`, `protect2`, `nvdata`, `nvcfg` and `persist` no longer opt into `formattable`; generated normal/recovery fstabs still need inspection after the build. Existing `check` remains filesystem-repair behavior, not complete write protection.

## Still required after build

Inspect generated boot/init_boot/vendor_boot/vbmeta/super artifacts, actual target-files/OTA partition membership, normal/recovery fstabs, merged VINTF for each relevant SKU, compiled SELinux/neverallow results, proprietary ELF/fixup compatibility, encryption/recovery behavior and AVB descriptors/signing/rollback configuration.

The source/prebuilt kernel migration remains a separate project: the source inventory still does not account for every prebuilt/load-listed module and does not yet prove ABI/CRC/signing/load-order equivalence.

See `STATUS.md` and `../SAFETY.md` for the evidence matrix and physical-device boundary.
