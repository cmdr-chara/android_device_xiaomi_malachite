# Coordinated bring-up status — 2026-09-06

**Release: BLOCKED.** The revival PRs are merged, but no full Android build or physical-device validation has been completed. Use `2026-09-06-merged.json` and `2026-09-06-merged.xml` for the first full Android build. The older `2026-09-06.*` pair is retained only as the pre-merge review snapshot.

## Merged source state

- Device: product/SKU copy wiring, source/workspace checks, and removal of `formattable` from `protect1`, `protect2`, `nvdata`, `nvcfg` and `persist`.
- Xiaomi hardware: bounded UDFPS status reads and deterministic fingerprint lockout initialization.
- MediaTek hardware: validated ION rows plus negative/overflow-safe Mali accounting.
- IMS: inherited-product `LOCAL_PATH` is preserved.
- Kernel source: the two required KMI dependencies are present. Device-module Kconfig diagnostics and MGK quoted-value generation are fixed without changing the verified configuration result.
- Vendor and prebuilt repositories contain audit tooling, while the proprietary payload and checked-in kernel/prebuilt bytes remain the preserved compatibility baseline.

The first Android build intentionally continues to use `TARGET_FORCE_PREBUILT_KERNEL := true`. Source-kernel migration is not implied by the successful kernel compilation.

## Evidence matrix

| Claim | Status | Evidence / boundary |
| --- | --- | --- |
| Integrated source-contract suites | PASS | Device/candidate, Xiaomi HAL, MediaTek HAL, IMS, Kconfig/Kleaf and vendor audit suites completed on their recorded candidate revisions |
| KMI-only source kernel compilation | PASS | Kernel manifest run `33995588360`; 503 build actions completed successfully |
| Kconfig/MGK configuration preservation | PASS | Native pinned Linux 6.1 comparison produced byte-identical `.config` before/after the two configuration-cleanup changes |
| Preserved vendor ELF dependency contracts | PASS | Five selected AArch64 blobs plus regression suite; proprietary bytes were not replaced |
| Prebuilt structural inventory | PASS | Existing Image/DTB/module structure and hashes inspected; no deployment change |
| Post-merge source lock | PASS | `2026-09-06-merged.json` pins all 12 owned repos; its XML pins the seven Android paths used by the first full build |
| Source/prebuilt kernel equivalence | GAP | Required module/configuration/CRC/signing/load-order equivalence is not established; source inventory still misses load-listed names |
| Full Android build and generated target-files | GAP | Not yet produced for the merged candidate |
| Merged VINTF and compiled SELinux | GAP | Must be checked from the real full build |
| Release AVB/signing policy | FAIL | Inherited `--flags 3` and test-key configuration remain; do not interpret a test build as production verified-boot readiness |
| Boot, recovery, encryption and hardware | GAP | Physical device tests not performed |

## Hard-brick packaging guard

`tools/audit_target_files.py` is a read-only post-build gate. It checks the generated target-files ZIP for the exact expected A/B partition set, rejects non-empty `RADIO/` firmware payloads, rejects low-level images such as bootloader/DTBO/modem/security/calibration partitions, checks unsafe ZIP paths, and enforces the configured boot/init_boot/vendor_boot/super size ceilings.

A PASS from this tool means only that the package stayed inside the reviewed high-level Android partition boundary. It does not prove bootability, AVB production policy, firmware compatibility, recovery behavior or daily-driver readiness.

## Next build work

On a sufficiently provisioned Linux host:

1. Sync the surrounding LineageOS `lineage-23.2` tree and apply `2026-09-06-merged.xml` as the local manifest.
2. Preserve `repo manifest -r` and the exact build logs.
3. Build the target-files/ROM using the unchanged prebuilt kernel path.
4. Run `python3 device/xiaomi/malachite/tools/audit_target_files.py <target_files.zip>`.
5. Inspect generated boot/init_boot/vendor_boot/vbmeta/super images, normal/recovery fstabs, dynamic-partition sizing, AVB descriptors/keys/rollback indices, merged VINTF and compiled SELinux.
6. Only after those host-side gates are reviewed should a separately authorized physical-device phase begin.

See `../SAFETY.md` for the dangerous-partition, same-region firmware and recovery boundaries.
