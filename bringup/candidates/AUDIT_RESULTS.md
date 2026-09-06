# Coordinated candidate evidence: 2026-09-06

This is an operator record, not a ROM release. All twelve `lineage-23.2` branch
heads were checked against the original source lock and remain unchanged.
No phone was accessed, rebooted, flashed or otherwise mutated.

## Exact evidence

[Source audit run 33998938037](https://github.com/cmdr-chara/android_device_xiaomi_malachite/actions/runs/33998938037)
ran coordinator commit `6d957cc33d1dc1c1caff2e51f5070cffdee39158`, based on
`6ac1507a40cfb9c2b97ebc64332825e9540d04be`. Its immutable component inputs are
[2026-09-06.json](2026-09-06.json); the Android manifest remains
[2026-09-06.xml](2026-09-06.xml). The device component is intentionally pinned to
`6da4bf9433d00cb2cee7bc54331c237290dad8be`, not this documentation commit.

The downloaded artifact `9978905159` was verified against ZIP SHA-256
`f8d729d5ce8547700689a46d3f8b7557226f032f18575724c18440a4e2c87a0f`.
The complete static audit was rerun locally and produced the identical report.
The workflow's failure is the real inherited AVB release-policy failure below;
it is not a failed source fetch, a compilation result or a permission problem.

## Verification matrix

| Claim | State | Actually observed |
| --- | --- | --- |
| Twelve pinned repositories and live refs | PASS | Exact commit/tree identities collected; historical baseline heads unchanged |
| Export integrity | PASS | 3,267 selected files verified against byte counts, SHA-256 and Git blob identity |
| XML syntax | PASS | 333 XML files parsed; not a merged VINTF compatibility check |
| Device Python syntax | PASS | 11 component Python files parsed |
| Coordinator regressions | PASS | 51 tests passed in the retrieved coordinator source and locally |
| MediaTek native regressions | PASS | Combined ION and Mali ASan/UBSan harnesses passed at ba498cb5887617203bba8ec4ddec97170258631d |
| Xiaomi native regressions | PASS | Combined UDFPS and lockout ASan/UBSan harnesses passed at 17e9fcf64448c8c27b727ad7aadb78467750cc4a |
| IMS product wiring | PASS | Three GNU Make/XML tests passed at 34872804425207cc01f37d6c494db7fa1965a585 |
| Vendor filename coverage | PASS | 1,610 list entries, 1,609 unique destinations and 59 literal fixup targets present; ELF/fixup execution not proven |
| Existing prebuilt load membership | PASS | 60 system, 208 vendor, 215 ramdisk and 214 recovery entries found in their expected trees |
| Partition source relationships | PASS | Eight logical partitions; filesystem/slot/first-stage flags consistent; 4 MiB declared super headroom |
| Persistent autoformat proposal | PASS | Five protected filesystem entries no longer opt into formatting; fsck/vendor writes and runtime mount behavior remain outside this claim |
| AVB release policy | FAIL | Inherited `BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS += --flags 3`; signed chains/keys/rollback still require review |
| Android build and merged VINTF | GAP | No full Kati/Soong build or checkvintf result |
| Compiled SELinux and image layout | GAP | No compiled-policy or generated-image certification |
| Blob ELF compatibility and actual fixups | GAP | No camera/runtime or binary linkage certification |
| Boot, recovery, encryption and hardware | GAP | Physical testing requires separate authorization |

The native harnesses compile production code with Android-only stubs. They are
not complete HAL/Binder builds. Duplicate `mtk_dramc.ko` load entries remain
reported in recovery/ramdisk lists, not removed without evidence.

## Kernel progress and remaining compatibility gap

The earlier KMI-only candidate **did complete 503 build actions** in
[run 33995588360](https://github.com/cmdr-chara/kernel_manifest-6.1/actions/runs/33995588360).
That build used manifest `b48599ccd2758a15809347c321f98f5286b63574` and kernel
`fc1616578c449fc0bf4a6a061046e2992347f3c6`. It did not execute the distribution-copy
program or prove equivalence with the current Android prebuilts.

The subsequent Kconfig and Kleaf repairs passed the native configuration
experiment in [run 33998173925](https://github.com/cmdr-chara/kernel_manifest-6.1/actions/runs/33998173925).
The before/after Linux 6.1 `.config` files are byte-identical, 246,778 bytes,
SHA-256 `5e192377b16b0807adea0136acbb3ca4175399ff66d57d846f3138e098262339`.
Native Starlark tests reproduced the three escaped-value failures on the
baseline and passed all four cases after the fix. This is not a complete
rebuild of the newer configuration-preserving source combination.

There are two different module coverage counts, not conflicting reports:
**35 of all 502 distinct prebuilt module basenames** are absent from the source
inventory; **15 of the 478 names explicitly consumed by load lists** are absent.
The source inventory reports 817 distinct names but includes intermediate and
staging copies. The read-only guard and exact per-list gaps are in
[prebuilt PR #2](https://github.com/cmdr-chara/android_device_xiaomi_malachite-kernel/pull/2).
No load entries or binaries were removed to make coverage green.

## Next build gate

Use the coordinated Android manifest in a full isolated Lineage checkout;
record the complete upstream `repo manifest -r`, compile the product and inspect
VINTF, SELinux, boot/init_boot/vendor_boot, vbmeta and dynamic-partition outputs.
The current Chat filesystem has approximately 30 GiB available and no full
Android checkout. Hosted source/kernel probes do not substitute for that build.

Keep the forced prebuilt kernel for that Android integration build. In parallel,
resolve the fifteen consumed-module gaps, collect a complete source distribution,
check symbols/CRCs/signing and compare two clean builds before proposing a
replacement. Preserve the OS2 camera userspace, regional firmware boundaries,
DTBO exclusion and [phone safety policy](../SAFETY.md). No physical test or
verification bypass is authorized by this record.
