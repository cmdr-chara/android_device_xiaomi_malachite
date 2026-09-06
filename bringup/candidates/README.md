# Coordinated build-review candidate: 2026-09-06

This snapshot selects exact revisions for all twelve owned forks. It is not a ROM release and authorizes no phone operation. The original `../source-lock.json` and `../android.xml` remain unchanged.

## Reproduce the selected sources

For an isolated Android checkout, use `2026-09-06.xml` as the malachite local manifest, following the existing [build prerequisites](../README.md). It replaces only the seven owned Android paths. Preserve a complete `repo manifest -r` for the surrounding Lineage/AOSP checkout: those upstream revisions are not locked by this device-only record.

For the separate kernel checkout, use manifest repository commit `7a7a1cd05f06c5d502d31bbe966e4b2a84a9b71d` and `snapshots/2026-09-06-config-candidate.xml`. This extends the pinned 22-project baseline with the KMI, Kconfig and Kleaf review revisions selected in this JSON. The completed 503-action kernel build used the older KMI-only snapshot; do not transfer its build PASS to this newer source combination.

The Android device revision deliberately points to the existing code-integration commit rather than to this documentation commit, avoiding a self-referential source lock. Its assembly includes the draft persistent-filesystem autoformat opt-out and therefore still needs fs_mgr/recovery review. Source changes to `lineage-23.2` have not been merged.

## Included review units

Device: workspace audit, copy/SKU wiring and persistent-fstab proposal. Xiaomi hardware: bounded UDFPS reads and initialized fingerprint lockout state. MediaTek hardware: ION row validation and Mali size/overflow validation, combined without rewriting either PR. IMS: inherited-product scope preservation. Kernel: two additive KMI dependencies, configuration-preserving declaration cleanup and quoted Starlark value generation.

Vendor userspace blobs, the prebuilt kernel payload, common vendor policy and MediaTek vendor-module baseline retain their original revisions. OS2.0.208.0.VOOMIXM camera userspace, DTBO exclusion, partition layout and inherited AVB configuration are not silently changed. The inherited AVB `--flags 3`/test-key configuration remains a release blocker, not an approved policy.

## Validation and promotion gates

`python3 tools/verify_candidate.py` checks lock/manifest identity and protected baselines offline. `--online --report evidence.json` performs only GitHub GETs to record all twelve commit/tree identities, current branch heads and open PRs. A moving branch head does not replace a pinned commit. The report deliberately retains release status BLOCKED.

The integrated local source suite passed 45 tests when this snapshot was assembled. Native HAL tests and configuration comparisons are separate evidence; none substitutes for a full Android build. Before deployment consideration: compile the exact Android candidate; inspect VINTF/SELinux and generated boot/init_boot/vendor_boot/vbmeta/super images; validate encryption/recovery; complete kernel distribution/ABI/reproducibility comparisons; then request separate authorization for physical testing. The source module inventory still has 35 prebuilt basenames not observed. Do not discard required modules or disable verification to close the gap.

Keep the phone disconnected from experimental workflows. Follow [SAFETY.md](../SAFETY.md), including the dangerous-partition and same-region firmware rules. No flash, erase, format, slot-switch, bootloader, calibration or modem operation is part of this candidate workflow.
