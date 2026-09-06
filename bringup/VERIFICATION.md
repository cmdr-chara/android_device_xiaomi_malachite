# Verification record — 2026-09-05

**PASS** means the named check actually ran successfully. **FAIL** is an observed defect or policy violation. **GAP** means the required evidence was not obtained. **STALE** means historical evidence does not certify the current candidate. None of these source checks is a boot certification.

## Executed checks

| Check | Result | Evidence and limit |
| --- | --- | --- |
| Twelve baseline repository identities | PASS | Full immutable revisions in `source-lock.json`; public fork/branch/tree metadata collected for all twelve |
| Export integrity | PASS | 3,211 selected files checked against both SHA-256 and Git blob identity; artifact SHA-256 also verified |
| XML / device Python syntax | PASS | 329 collected XML files parsed; both device Python files passed AST parsing. Not schema/merged-VINTF or executable extraction validation |
| Device history coverage | PASS | All 808 commits reachable from the pinned device HEAD collected; other repositories have bounded recent history, not a claimed exhaustive audit of every kernel commit |
| Prebuilt load-list membership | PASS | 60 system, 208 vendor, 215 vendor-ramdisk and 214 recovery entries all exist in their declared tree directories. Duplicate `mtk_dramc.ko` entries remain visible; ABI/insertion is untested |
| Partition declarations | PASS | Eight dynamic filesystem types agree with fstab; slot/AVB/first-stage flags present; declared group fits super with 4 MiB remaining. Actual image/phone layout is GAP |
| Workspace unit tests | PASS | 25 local tests covering lock/collector/path safety, generated Android manifest and evidence integrity |
| Product cleanup regression tests | PASS | Seven local tests; the original eUICC duplicate and mutable hotword source path fail the GNU Make fragment tests before the two-hunk change. Android helpers/inheritance are stubbed, not a full Kati build |
| Persistent-fstab regression tests | PASS | Three local tests; the original persistent autoformat opt-in test fails, the draft removes only five flags, and data/dynamic flags are retained |
| Kernel manifest unit tests | PASS | Fourteen local tests covering ownership/pins/paths/linkfiles and resolved-identity/superproject schema |
| Kernel remote refs | PASS | All 22 projects and the upstream superproject resolved; upstream dependencies remain upstream |
| Actual pinned kernel sync | PASS | All 22 checked-out revisions matched the recorded kernel snapshot |
| Actual Kleaf configuration | PASS | Customer user target configured: 106 packages, 118,007 targets, **zero compile actions**. This was `cquery`, not a kernel build |
| Original source-kernel compilation | FAIL | Run 33990250234 failed `KernelBuildCheckSymbolViolations`: `__skb_pad` required by rtl8150; `__tty_port_tty_hangup` required by RFCOMM/CDC-ACM/USB-serial modules. This was not a host timeout |
| Additive KMI source repair | PASS (source delta only) | Kernel commit `339756b49b9d6da792a749bee04aa113b2c26f03` adds exactly those two list entries. Existing entries/enforcement preserved; final branch workflow is read-only |
| Repaired kernel distribution build / ABI review | GAP until its completed evidence is recorded | Separate `snapshots/2026-09-05-kmi-candidate.xml` pins kernel `fc1616578c449fc0bf4a6a061046e2992347f3c6`. Follow the kernel manifest build-result record; do not transfer baseline/cquery PASS to this build |

## Explicit unresolved gates

| Gate | Result | Required next evidence |
| --- | --- | --- |
| AVB release policy | FAIL | Inherited `--flags 3` and public test keys are not a verified release chain. Signed descriptors, key policy and rollback indices need dedicated validation |
| Baseline persistent autoformat policy | FAIL | Five calibration-bearing/persistent filesystems are formattable. Draft PR #3 is not merged and is not complete protection from fsck/vendor-service writes |
| Full Android compilation | GAP | No complete Android checkout or ROM build was performed. Build the pinned prebuilt-kernel baseline, then a separately recorded integration candidate |
| VINTF all SKUs | GAP | Run platform `checkvintf` against generated framework/vendor/ODM manifests, including the radio override/SKU combinations |
| Compiled SELinux | GAP | Check policy closure, neverallows, labels and the debug-only permissive `osi` domain. No global permissive/neverallow bypass was added |
| Binary blobs and extraction | GAP | ELF dependencies, ABI/shim compatibility, GraphicBuffer patch offsets/match counts, original/fixed hashes and extraction idempotence require actual binary/tool execution |
| Generated images and OTA | GAP | Header sizes, actual partition capacity, ramdisk/DTB placement, AVB chains, payload exclusions, recovery packaging and virtual-A/B behavior |
| Source/prebuilt kernel equivalence | GAP | Compare configuration, Image/DTB/module hashes, KMI/symbol versions, signatures and load ordering. The prebuilt is a selective stock/source mixture, not an output-equivalence reference already reproduced |
| Physical POCO tests | GAP | No ADB, fastboot or phone operation performed. Use the separately authorized matrix in `SAFETY.md` |
| Historical hardware success reports | STALE | Retained fixes and former tests in `HISTORY.md` are not new proof for a different SKU/build. Dolby was removed, not fixed |

## Retained evidence identifiers

- Source collection: device Actions run **33990392279**, artifact **9976463148**, archive SHA-256 `82b2088e46bc23fd4ceb6cfd05e19514c677cc1a09ca028c3fe97179b8e297b0`.
- Kernel ref resolution: manifest Actions run **33989636041**, artifact **9976218399**, archive SHA-256 `51ab066640c7e4301335adcb7ed1dad18ed3b0782f2c400c2711ec808d4faee4`.
- Kernel sync/cquery: manifest Actions run **33989907603**, artifact **9976325754**, archive SHA-256 `d68a9388f516f91cbe4b43b1c967c72ea53a121a2d37a6d672a29d1e2a76f3be`.
- Original kernel compilation failure: manifest Actions run **33990250234**, artifact **9976646745**, archive SHA-256 `3a32c2c828808a9a90db4a7cfc41925df2f8301f13827073c2550434e7f646b6`.

The collector artifact deliberately contains selected text, inventory and bounded history, not every source or binary. The first artifact omitted hidden files; that failure was corrected before accepting the later complete selected-file inventory. Source audit exit status remains nonzero for the two inherited safety FAILs. Review every named result instead of treating one green CI badge as release readiness.
