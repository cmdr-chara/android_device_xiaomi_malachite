# NFC stack and validation

The NFC candidate uses the unmodified malachite OS2.0.208.0.VOOMIXM AIDL
service and its matching libraries. `proprietary-files.txt` pins every imported
NFC executable/library by SHA-1. Regenerate vendor modules through
`extract-files.py`; do not edit the generated Android.bp by hand.

The service implements frozen `android.hardware.nfc` AIDL V1, linked to the
interface library built from source, and `vendor.tms.tmsnfc_aidl` V1. Both are
declared only in the three NFC-capable SKU manifests. The single init service
is disabled until the CN/Global hardware selection enables it. India remains
without an NFC provider. The old HIDL service and registration are removed;
`vendor.tms.tmsnfc@1.0.so` remains because stock COS helpers still depend on it.

This transition is a candidate remedy for repeated NFC startup failures. On
the zircon HIDL baseline, two observed boots caused 18 and 24 service aborts
before NFC stabilized. A controller CORE_RESET notification with reason
`0xa0` enters emergency recovery. Its underlying cause is unresolved; the
cross-device binary provenance alone is not proof of causation.

Stock emergency recovery can call `_exit(0)`, so zero tombstones does not prove
stability. Before promoting this candidate, observe two complete boot windows
longer than the original failure interval, count HAL process restarts and
controller resets, and exercise NFC off/on and screen transitions. A passing
startup test still does not certify tag, CieID, or IsyBank transactions.

The framework's optional lookup of `/data/vendor/nfc/libnfc-nci-update.conf`
may encounter a directory-search denial; normal NFA storage is `/data/nfc`.
Do not grant broad framework access to vendor NFC data solely to silence that
optional lookup. Diagnose any actual operation failure independently.

Host checks: `python3 -m unittest discover -s tests -v`, Android ELF dependency
checks, init verification, SELinux compilation, and `check-vintf-all`. The
`test_nfc_stack.py` cross-file contracts reject the former HIDL configuration.
Device testing and its artifact identities must accompany the host results.
