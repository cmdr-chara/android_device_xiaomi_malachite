# Coordinated bring-up status — 2026-09-06

**Release: BLOCKED. No physical device operation has been performed or authorized by these workflows.** Use `2026-09-06.json` and `2026-09-06.xml` for the source-review candidate. Original `lineage-23.2` revisions remain the preserved historical baseline, not a boot certification.

## Implemented review units

- Device integration: product/SKU copy wiring, workspace/source checks, and the separately gated persistent-filesystem autoformat opt-out. This last change still needs platform fs_mgr and recovery validation.
- Xiaomi hardware: bounded UDFPS status reads and initialized fingerprint lockout state.
- MediaTek hardware: validated ION rows and overflow/negative-size protection for Mali page accounting. The joint integration revision is `ba498cb5887617203bba8ec4ddec97170258631d`; individual PRs preserve both histories.
- IMS: preserve the inheriting product's LOCAL_PATH and retain the existing APK/feature contracts.
- Kernel source: two required KMI entries added without weakening checks. Device modules: remove duplicate Kconfig prompts and malformed haptic text. MGK rules: quote generated Starlark values correctly.
- Audit tooling: immutable candidate manifest/lock, read-only twelve-repository identity checker, proprietary filename/fixup coverage, prebuilt ELF/load-list inspection, source-output name comparison and real vendor ELF dependency checks.

Vendor Android blobs, prebuilt kernel payload, common vendor SELinux and MediaTek vendor-module source remain at the original selected revisions. No binary baseline refresh or firmware downgrade was made.

## Evidence matrix

| Claim | Status | Exact evidence / boundary |
| --- | --- | --- |
| Integrated device/candidate source contracts | PASS | 51 tests locally and in PR run [33998754880](https://github.com/cmdr-chara/android_device_xiaomi_malachite/actions/runs/33998754880), source `6ac1507a40cfb9c2b97ebc64332825e9540d04be` |
| All twelve pinned commit/tree identities | PASS | Same run's GET-only revision report; all twelve original branch HEADs unchanged at inspection |
| Combined ION/Mali native contracts | PASS | [33997988211](https://github.com/cmdr-chara/android_hardware_mediatek/actions/runs/33997988211), integration `ba498cb5887617203bba8ec4ddec97170258631d`; production-method native sanitizer harnesses, not a complete Android HAL build |
| KMI-only source kernel compilation | PASS | [33995588360](https://github.com/cmdr-chara/kernel_manifest-6.1/actions/runs/33995588360), manifest `b48599ccd2758a15809347c321f98f5286b63574`, kernel `fc1616578c449fc0bf4a6a061046e2992347f3c6`; 503 completed actions |
| Kconfig/MGK configuration preservation | PASS | [33998518574](https://github.com/cmdr-chara/kernel_manifest-6.1/actions/runs/33998518574); both real pinned Linux 6.1 configurations byte-identical; targeted duplicate-prompt/unsupported-character diagnostics eliminated |
| Native Starlark value escaping | PASS | [33998814129](https://github.com/cmdr-chara/kernel_manifest-6.1/actions/runs/33998814129); plain, quote, backslash and newline cases; last three reproduce baseline failures and pass on candidate |
| Proprietary destination/fixup filename coverage | PASS | 1,610 entries / 1,609 distinct destinations / 59 fixup targets; see vendor-inventory.json and VENDOR_INVENTORY.md |
| Five preserved vendor ELF dependency contracts | PASS | [33999461192](https://github.com/cmdr-chara/proprietary_vendor_xiaomi_malachite/actions/runs/33999461192), tool `d689c2ee59be2f48f431fe6c7cbf7a9e45ef55a4`; eight tests plus five actual blobs, hashes independently matched baseline Git tree |
| Source/prebuilt equivalence | GAP | 35 of 502 prebuilt module basenames not observed among 817 source-output basenames; 15 distinct missing names are used by current load lists |
| New configuration-candidate image/module build | GAP | A configuration-only comparison does not transfer the earlier KMI-only full-build PASS |
| Full Android build, merged VINTF/SELinux, image layout | GAP | No complete Lineage/AOSP checkout and target-files build validated for this candidate |
| Release AVB/signing policy | FAIL | Inherited --flags 3/test-key configuration remains unchanged and is not an acceptable verified-boot readiness claim |
| Boot, encrypted data/recovery, OTA and hardware | GAP | Physical device tests not performed |

The first configuration collector incorrectly expected direct files rather than Kleaf tree artifacts; it was corrected and rerun. The first vendor CI lacked LLD; the missing host fixture dependency was installed, with tests retained. Neither failure was hidden or converted into a hardware success claim.

## Remaining build work

Build the exact Android review candidate on a sufficiently provisioned Linux host using the unchanged prebuilt payload. Retain the complete surrounding `repo manifest -r`, target-files and build logs. Inspect generated boot/init_boot/vendor_boot/vbmeta/super images, partition sizing, normal/recovery fstabs, encryption configuration, merged VINTF, compiled SELinux and AVB/signing before considering device deployment.

Separately finish the kernel distribution-copy and ABI comparison. Trace required-but-unobserved module names to their real Kbuild/configuration producers; do not delete load entries merely to satisfy inventory coverage. Existing prebuilts expose 6.1.57/6.1.115/6.1.166 vermagic families while the source output is 6.1.167 with a maybe-dirty suffix. Investigate configuration, CRCs, signing, stamp/provenance and repeatability with two clean builds before replacing anything.

## Physical-device gate

Later testing needs the exact model/SKU and current same-region firmware identity, recovery/restore evidence and separate explicit authorization. Validate boot/encryption/recovery, all camera lenses/video, IMS/radio/SIMs, UDFPS/AOD/display, sensors, audio, Wi-Fi/Bluetooth/NFC, charging/thermal, GNSS and DRM. No flashing, wipe, slot switch, reboot, bootloader/modem/calibration write or verification bypass is authorized now. See [SAFETY.md](../SAFETY.md).

**Next highest-value action:** a full Android build of the locked review candidate with the preserved prebuilt kernel, before any phone testing.
