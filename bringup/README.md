# Malachite revival workspace

**Status: source bring-up in progress; no ROM build, phone boot or daily-driver certification.** Start with [ARCHITECTURE.md](ARCHITECTURE.md), [HISTORY.md](HISTORY.md), [SAFETY.md](SAFETY.md) and [VERIFICATION.md](VERIFICATION.md). The baseline is `lineage-23.2`, not an automatic upgrade to newer firmware or blobs.

## What is locked and what is known good

[source-lock.json](source-lock.json) records all twelve project-owned baseline revisions. [android.xml](android.xml) reproduces the seven Android-side forks at those exact commits, replacing only their matching checkout paths. The separate owned [kernel manifest](https://github.com/cmdr-chara/kernel_manifest-6.1/tree/revival/owned-pinned-manifest) contains a fully pinned 22-project kernel snapshot, including upstream toolchains. Standard AOSP, Lineage and Google dependencies stay upstream.

The verified results are source identities, selected-text integrity, structural contracts, kernel source sync and Kleaf target configuration. There is **no freshly tested known-good ROM/image set** from this session. The original source-kernel build reached compilation and failed its KMI-symbol check; the isolated two-symbol repair has a separate candidate manifest and build evidence. The Android product still forces the original hybrid prebuilt kernel.

No `lineage.dependencies` file existed in any of the twelve inspected repositories. The owned local manifest supplies the device-specific workspace rather than introducing ambiguous roomservice ownership. The Android root manifest and all its external dependencies still need a full resolved `repo manifest -r` on the build host. Pinning only these seven projects is not a complete Android source lock.

## Work ownership and integration

The session coordinator owns all writes. Independent repository/ref collection was parallelized with bounded workers after the dependency map existed. No subagent execution capability was available. Shared manifests, source locks and integration decisions have a single writer; no force pushes or merges were performed.

| Work unit | Repository / branch | Gate before integration |
| --- | --- | --- |
| Evidence, workspace and documentation | device tree: `revival/workspace-audit`, PR #1 | Offline/CI contracts, documentation links and recorded evidence; does not certify runtime |
| Product copy wiring | device tree: `revival/device-config-cleanup`, PR #2 | Two reproduced fragment-level defects; full Android build still required |
| Persistent autoformat protection | device tree: `revival/persistent-no-autoformat`, draft PR #3 | Generated normal/recovery fstab and fs_mgr review; later device tests separately authorized |
| Owned kernel manifest / source probes | kernel_manifest-6.1: `revival/owned-pinned-manifest` | Pinned refs/sync, exact target configuration and actual build result |
| Additive KMI repair | android_kernel_xiaomi_mt6878: `revival/kmi-symbol-repair` | Exactly two added symbols, unchanged enforcement; full rebuild and ABI review |

These are isolated candidates, **not one already integrated/tested ROM revision**. Preserve `source-lock.json` as the inspected baseline. For an integration build, record the resulting device-tree commit, every changed owned revision, full external manifest, dirty-worktree status, tool versions, commands and output hashes in a new candidate record. Do not silently repoint the baseline lock, use moving branch heads, or merge safety-sensitive changes because an XML parser passed.

## Available checks

Run from this repository on a host with Python 3.10+ and GNU Make where required:

```sh
python3 -m unittest discover -s tests -v
python3 tools/workspace_manifest.py
```

The product/fstab tests live on their respective review branches until deliberately integrated. The workspace collector requires Git/network access; its output must be a new or empty directory:

```sh
python3 tools/collect_source_evidence.py --output /path/to/new-evidence --jobs 3
python3 tools/verify_source_evidence.py /path/to/new-evidence --output /path/to/new-report.json
```

The baseline verifier intentionally exits nonzero for the inherited AVB flags and persistent-autoformat opt-ins. Inspect the named FAIL rows rather than suppressing its exit status. PASS on XML means well-formed text, not merged VINTF compatibility. The collector selects text and inventory metadata; it is not a buildable checkout and excludes binary payloads. The bounded hosted workflows retain artifacts for seven days, so retain evidence separately when needed.

## Eventual Android build — not executed in this session

Use an isolated Linux build machine with the host packages, RAM and free storage required by the pinned Lineage release, plus Git, git-repo, Git LFS where needed, Python and network access. Record actual host capacity; do not reuse a dirty or unrelated Android tree. Keep a separate checkout of this control/documentation branch so syncing the pinned device baseline does not remove the manifest source you are using.

The Lineage Android manifest `lineage-23.2` was observed at `15cbfd1cf5d88f7cda78e7bde44ae994dd13958e`. Its child project refs still need resolving. Example build-host sequence, with `CONTROL_REPO` set to that separate checkout and the destination initially empty:

```sh
mkdir malachite-android
cd malachite-android
repo init -u https://github.com/LineageOS/android.git \
  -b 15cbfd1cf5d88f7cda78e7bde44ae994dd13958e --git-lfs
mkdir -p .repo/local_manifests
cp "$CONTROL_REPO/bringup/android.xml" .repo/local_manifests/malachite.xml
repo sync -c -j4
repo manifest -r -o manifest.lock.xml
source build/envsetup.sh
breakfast malachite userdebug
m bacon
```

This builds the **inspected baseline**, not an implicit merge of the review branches. `breakfast` resolves the release selector through the checked-out Lineage helper; do not guess a lunch release suffix from another Android version. Capture complete logs and stop at the first reproducible failure. Do not add missing dependencies from arbitrary archived branches, bypass ELF checks/neverallows, set global permissive mode or disable verification to get an image.

Do not use installation helpers such as `eat` or `omnom`. Compilation does not authorize touching a phone. After a successful build, perform the image/SELinux/VINTF/ELF/OTA checks in [SAFETY.md](SAFETY.md) before any request for a narrowly scoped device test.

## Kernel continuation

Keep kernel work in a separate directory. Follow the owned kernel manifest README for the exact snapshot, official repo launcher revision, target and environment. Compare the unmodified snapshot with `snapshots/2026-09-05-kmi-candidate.xml`; the latter changes only the pinned Xiaomi kernel source revision and asserts the expected base revision.

Required outputs for migration review include kernel configuration, Image/DTB hashes and placement, Module.symvers, module inventory/versions/signatures, build logs and the resolved manifest. A configured target, compiled Image, or two added symbols does not establish equivalence with the mixed stock/source prebuilt repository. Leave `TARGET_FORCE_PREBUILT_KERNEL` unchanged until those gates and separately authorized hardware tests pass.
