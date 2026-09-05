# Firmware, device-test and recovery safety gates

**No physical phone operation is authorized by this repository or by a successful CI run.** The revival session only authorizes repository/build work. No phone was accessed or mutated during this work.

## Separate four different inputs

| Input | Policy |
| --- | --- |
| Proprietary Android userspace | The inspected extraction baseline is OS2.0.208.0.VOOMIXM unless individually noted/pinned. Keep camera dependencies coherent. An OS3 fingerprint is not evidence that OS3 blobs are safe. |
| Device firmware | Record the actual SKU, region, installed build and compatibility requirements before testing. Do not downgrade or mix regional firmware to match an old userspace extraction. |
| Modem/baseband | Treat independently from RIL/IMS userspace. Do not replace it to work around a framework or radio-HAL error. |
| Bootloader/preloader and security state | Out of scope. No update, downgrade, cross-flash, unlock/relock, anti-rollback change, seccfg/eFuse operation or verification bypass. |

A firmware incompatibility needs the exact incompatible component, its producer/consumer and logs. A broad downgrade is not a diagnosis. Keep original and fixed blob hashes, extraction tools and build provenance; never label retained old binaries as security-patched solely because build properties were updated.

## Dangerous-partition boundary

Do not write, erase or format GPT, preloader/bootloader/LK, seccfg, eFuses/OTP, NVRAM/NVDATA/NVCFG, protect partitions, persist, calibration, device keys or IMEI-sensitive data. Do not publish private calibration dumps. Do not run an unreviewed vendor `flash_all` script, repartitioning utility, manufacturing tool or bootloader-relocking script.

Boot, init_boot, vendor_boot, DTB/DTBO, vbmeta and super/logical partitions are **not automatically safe**. They can have firmware, signing, rollback, slot and hardware dependencies. They may enter a later narrowly scoped test only after separate explicit authorization. No current authorization permits flashing, userdata/metadata wipes, slot changes or even rebooting a connected phone.

## Inherited source risks that block release

1. `BoardConfig.mk` enables AVB but supplies `--flags 3` and public test keys. Do not claim verified boot or release readiness. Preserve this as a visible inherited FAIL until a dedicated signing/rollback/descriptor-chain design is validated against generated images. Never add verification disabling to make a test succeed.
2. The baseline fstab opts `protect1`, `protect2`, `nvdata`, `nvcfg` and `persist` into `formattable`. The isolated draft [device PR #3](https://github.com/cmdr-chara/android_device_xiaomi_malachite/pull/3) removes only those five flags. This prevents that opt-in; it is **not complete write protection**. Existing `check` may repair filesystems and vendor services may write. Generated vendor, first-stage and recovery fstabs and mount behavior still require review.
3. Historical DTBO/firmware mismatch was reported to cause hard bricks. Keep the current DTBO packaging/OTA exclusion. A file existing in the prebuilt repository does not establish compatibility with the phone's firmware.

Fastboot recovery cannot be guaranteed merely by avoiding preloader writes. Hardware description, early boot and firmware interactions can fail before Android starts. Preserve bootloader/fastboot recovery wherever technically possible, but do not promise a brick-proof process.

## Build-host gates before any device test

Produce a full immutable Android manifest, exact candidate commit list, build logs and hashes. Verify image sizes/header versions, DTB placement, ramdisk layout, dynamic partition capacity, OTA partition list, AVB descriptors/keys/rollback indices and absence of forbidden firmware payloads. Run merged `checkvintf` for each actual ODM SKU, compiled SELinux/neverallow checks, ELF dependency/fixup checks and module ABI/load-list validation. Inspect the normal and recovery fstabs produced by the build, not just source files.

Do not promote the source kernel into the Android prebuilt repository based only on compilation. Compare Image/DTB/module provenance, configuration, symbol versions, signing and load order with the transitional hybrid prebuilt. Keep the current OS2 camera userspace and prebuilt path as separate controlled baselines.

## Eventual device matrix — all physical results currently GAP

Historical tests in [HISTORY.md](HISTORY.md) are STALE for these candidates. Record exact hardware SKU/panel/fingerprint variant, regional stock build, ROM/kernel candidate hashes, test date and logs for every result. Testing needs separate authorization for the specific device operations involved.

| Gate | Required evidence |
| --- | --- |
| Recovery before experimentation | Exact same-region restoration materials and offline hashes; reviewed restoration scope; verified access path appropriate to that phone; no automatic relock/wipe/firmware downgrade |
| First boot / encryption / policy | Bounded boot attempt, early logs, FBE unlock, metadata behavior, enforcing-policy/denial review; stop on unexpected persistent-partition writes or repair requests |
| Recovery / OTA / slots | Recovery touch and firmware availability, encrypted-data behavior, virtual-A/B snapshot/update/rollback behavior; slot changes or update installation need their own authorization |
| Camera | Global-model HAL startup, each exposed lens, still/video, advertised fps/resolutions, ultrawide/macro stabilization and long recording; capture crashes/tombstones |
| Fingerprint / display / sensors | Enrolment/authentication, FOD/HBM, screen-off/AOD, flicker/brightness/HDR, under-display ALS, proximity/pocket/rotation and suspend transitions |
| Radio / IMS | Both supported SIM paths, data/SMS/voice, carrier IMS registration, VoLTE/VoWiFi and handover; emergency functionality only through approved carrier/lab procedures, never unsolicited live emergency calls |
| Audio / connectivity | Speaker/mic/earpiece, USB DAC/VoIP, Bluetooth calls/music, WPA2/WPA3/mixed/PMF, hotspot/P2P, reconnect and suspend; NFC only on supported SKUs |
| Power / charging / GNSS / DRM | CPU scaling and lockups, thermal limits, idle drain, charge negotiation/limits/offline charge, GPS cold/warm fixes and assistance, lawful DRM playback/provisioning; no L1 claim without evidence |

## Eventual recovery procedure: prerequisites, not executable instructions

Before a separately authorized experiment, maintain an offline inventory of exact stock images and same-region release identifiers, with checksums and the current layout/signing/rollback constraints. Inspect any restoration script rather than trusting its filename. Establish which Android-side components may be restored without touching the prohibited partitions or current low-level firmware, and how logs can be retained without exposing private data.

On failure, stop repeated boot/flash attempts. Classify bootloader, recovery, kernel, first-stage mount, SELinux, framework or HAL failure from available evidence. Do not erase metadata/userdata or change slots as a diagnostic shortcut. If the approved recovery route is unavailable, stop and reassess; do not improvise preloader/GPT/seccfg or cross-region flashing. Any actual restoration, reboot, wipe or partition write requires a fresh, specific authorization and a reviewed device-specific procedure.
