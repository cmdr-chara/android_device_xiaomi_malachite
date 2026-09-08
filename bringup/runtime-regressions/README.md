# Runtime regression investigation and camera recovery candidate

**Release decision: BLOCKED for hardware claims.** This bundle is an Aperture
source patch and a five-issue investigation, not five validated device fixes.
No firmware, kernel/prebuilt modules, NFC tuning, DRM, SELinux, or existing
proprietary payload is changed. The preserved OS2 userspace policy still applies.

## Camera change and integration

The reviewed app is `LineageOS/android_packages_apps_Aperture` at
`cf1bc0a72524318d0e06ebe938a20b170f1eb878`. Its video frame-rate field is nullable
(AUTO), but the binding predicate requires membership in a non-null fixed-rate
set. The new executable regression check reproduces rejection of AUTO on the
original source. Initial configuration also converted AUTO to the first fixed
rate, which is inappropriate when a fixed rate is not supported with HDR.

The patch preserves AUTO, allows it at bind time, and exposes it in the rate
cycle. On an HDR `IllegalArgumentException` while configuring use cases, or a
CameraX `ERROR_STREAM_CONFIG`, it attempts one SDR fallback at a supported
quality, with automatic frame rate and stabilization off. The four video options
are committed together before rebinding so the failed HDR preference is not
replayed on the next launch. Other preferences and saved media are untouched.
A toast explains the fallback. SDR failures are not retried, and permission,
other device, and encoder errors retain their separate handling.

This is **crash-recovery mitigation, not proof of functioning HDR encoding**.
A vendor native abort before CameraX delivers an error, an app other than
Aperture, or a different upstream version is not covered by this patch. HDR is
not globally disabled. Full on-device HDR recording remains an open outcome.

The device tree cannot override another repository's Kotlin source with a
resource-only overlay. The consumer change is therefore supplied as an exact,
hash-checked patch rather than an unused overlay flag. It is NOT applied merely
by syncing or merging this device-tree change.

In a host Android checkout with Aperture at the reviewed revision:

```sh
python3 device/xiaomi/malachite/tools/apply_aperture_recovery.py \
  --aperture-root packages/apps/Aperture
python3 device/xiaomi/malachite/tools/apply_aperture_recovery.py \
  --aperture-root packages/apps/Aperture --apply
m Aperture
```

The first command is read-only. The second refuses another revision, dirty or
mismatched input, symlinks, and patch tampering. Reapplying identical output is a
no-op. CI applies the patch to the actual pinned app, checks the before/after
behavior, and attempts a complete debug APK build and lint. A debug build is
not a platform ROM/Soong build or permission/signature/runtime certification.

Rollback only the host patch, after checking the reverse patch applies:

```sh
git -C packages/apps/Aperture apply -R --check \
  "$PWD/device/xiaomi/malachite/bringup/runtime-regressions/aperture-hdr-recovery.patch"
git -C packages/apps/Aperture apply -R \
  "$PWD/device/xiaomi/malachite/bringup/runtime-regressions/aperture-hdr-recovery.patch"
```

Do not reset or clean the checkout, flash anything, or erase app data as part of
this source operation. Successful fallback resets only the named video options;
previous failed video settings are not automatically restored by rollback.

## Investigation outcomes

| Issue | Evidence | State / next proof required |
| --- | --- | --- |
| Display 30 Hz / dimming | Four current O16U panel ELFs have `mode_60hz`, `mode_90hz`, `mode_120hz`; virtual fallback has `mode_120hz`. No `mode_30hz` was found. | Previous claim that these current prebuilts reintroduce a 30 Hz mode was not supported. Need the installed build/module identity and physical display mode versus compositor/render rate around failure. No speculative minimum-refresh service or kernel replacement. |
| CIE/isybank NFC | Donor TMS service and NCI library are present; the library references `PRESENCE_CHECK_ALGORITHM` and vendor/ODM configuration paths. Configured algorithm 2 alone does not demonstrate a bad presence check. | Initial vibration does not prove authenticated APDU exchange. Need timestamped state/error evidence and same-card comparison with CieID. Do not change RF tuning, eSE routing, or presence algorithm from this symptom alone. |
| SoundTrigger / hotword | ROM has the hotword audio route, enrollment permissions, VOW kernel modules and `/dev/vow` policy, but no SoundTrigger implementation in the vendor inventory or device manifest. Stock OS3 has `android.hardware.soundtrigger3-impl.so` and `sound_trigger.primary.default.so`. | Missing provider is a concrete integration gap. A manifest-only fix cannot load an absent HAL. Need a compatible OS2 provider/model/DSP set or an explicitly validated isolated port. Stock OS3 libraries were inspected, not imported into the preserved OS2 baseline. |
| Netflix L1 | Widevine APEX and `liboemcrypto` are included. ClearKey is a separate provider. | Need actual MediaDrm provisioning/security-level evidence, service startup errors, and Netflix Playback Specification. Package presence cannot establish L1 or Netflix HD eligibility. No key, boot-state, integrity or Netflix spoofing. |
| Camera HDR | Persisted HDR replay, unhandled bind rejection, and exit-on-stream-config path inspected. AUTO rejection reproduced from actual source predicate. | Source recovery candidate supplied. Device HDR stream/encoder diagnosis and successful repeated capture still GAP. |

## Evidence provenance

Read-only collection: device workflow run **34241204317**, successful at source
`490193e09fc3a9bdf8f68307d814f512c4db731c`. Artifact **10062038541** ZIP SHA-256:
`e27e88ab073ca75d30c89c57c1d80f85fb3cd18d5bca2849d090894eaa920eee`.
All 611 collected files were independently checked against recorded SHA-256,
size, and Git blob identity after download.

Inputs: device runtime source `eeca91f98fe0fc49c841a35c1ddee4e9be8224b4`;
prebuilts `651c2ab2585db09cfa6f0b5f9267ced8d0086210`; vendor
`cf17911ec4f8480fb5dd82c6b375ec295c224270`; stock comparison
`ChkDumps/redmi_malachite_dump@879c5cd727b6a01b2bf9ba488a6fdacdd5d1d529`.
Stock comparison is OS3.0.10.0.WOOMIXM, not the OS2 baseline.

Stock legacy SoundTrigger driver: 78,840 bytes; Git blob
`7ed3ba1bad52fd67e9690caf62a29e04fba088a1`; SHA-256
`c746172790c21b17ebb1d261d8c9757aced22ae010d2514d18ce7dc28b33acb4`.
It imports VOW/model and MiSight interfaces and dynamically loads performance
and audio-parameter libraries. Names alone do not prove ABI compatibility.
Its inspected `/dev/vow` opens use `O_RDONLY`; do not broaden DAC permissions
based on an assumed `O_RDWR` requirement.

Primary implementation references: Android's SoundTrigger and Audio HAL
architecture (`source.android.com/docs/core/audio/sound-trigger` and
`source.android.com/docs/core/audio/implement`); CameraX CameraInfo and
VideoCapture API contracts (`developer.android.com`); Netflix's official
Android HD/Widevine troubleshooting (`help.netflix.com/en/node/23939`).

## Required device acceptance (owner: device maintainer)

Camera: reproduce the original failing HDR mode, verify an explained SDR
fallback, reopen without data clearing, record/play SDR, and verify photo/QR,
front/back cameras, microphone, AUTO/fixed rate, stabilization and permissions.
Test a supported HDR device/mode too: the patch must not disable successful HDR.
Capture a tombstone if the vendor process aborts before error delivery.

For the other four issues, provide the smallest read-only evidence described
in the table on the actual failing build. Do not publish document numbers,
CAN/PIN, raw APDUs, audio recordings, account identifiers, DRM certificates,
keys, or unreviewed bugreports. No phone-side commands were executed here.
