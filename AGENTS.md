# Malachite device-tree agent instructions

## Integration contracts

- Resolve the actual working branch, device-tree revision, and selected Android/kernel manifests before making integration claims. Historical bring-up notes describe their recorded candidates, not every later branch or build.
- This tree coordinates device configuration with separate vendor, kernel/prebuilt, hardware, framework, and app repositories. Record changed producer/consumer revisions together; do not silently repoint historical source locks or mix moving heads.
- Keep proprietary userspace, firmware, modem, and bootloader/security state distinct. A changed fingerprint, dependency name, or successful source test does not prove binary or hardware compatibility.
- Preserve current partition/OTA exclusions, AVB/signing requirements, SELinux enforcement, thermal/charging protections, and calibration-bearing data. Do not bypass these to get a build or boot.
- Switching source/prebuilt kernels, replacing blobs, or changing firmware/DTBO assumptions requires explicit scope and the corresponding integration evidence, not a speculative cleanup.

## Guidance and validation

Use [bringup/README.md](bringup/README.md) for workspace entry points, [bringup/SAFETY.md](bringup/SAFETY.md) for safety-sensitive changes, and [bringup/VERIFICATION.md](bringup/VERIFICATION.md) for the applicable evidence gates. Consult only the topic needed; verify dated statements against the selected candidate.

Run `python3 -m unittest discover -s tests -v` for source-contract changes with the fixtures required by the current branch. A missing vendor/tool prerequisite is a reported gap, not a reason to remove assertions. Source tests, full Android builds, generated-image audits, and physical-device tests are separate evidence levels.

Completion requires the requested source work, affected cross-repository contracts, and documentation to be accounted for with exact verification results. Repository/build authorization does not authorize flashing, rebooting, slot changes, wipes, calibration access, or other physical-phone operations.
