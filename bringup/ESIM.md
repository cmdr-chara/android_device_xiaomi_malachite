# Native eSIM connection selection

This candidate implements the missing shared SIM 2/eSIM connection selection
inside the existing Settings and TeleService packages. It retains the imported
Google eUICC manager. OpenEUICC and MalachiteEsimSettings are not product packages;
the former experimental integration is preserved in device commit a1cd5e9.

## Observed failure and boundary

The installed framework initially reports two removable UICC slots and no EID.
The Google manager returns activation result 10010 and Settings opens its mobile
network information screen. This observation alone does not prove a network
failure. The stock MediaTek software separately selects the eUICC connection.

OpenEUICC was studied to distinguish its privileged LPA/channel access from
hardware selection. It does not implement Xiaomi's MediaTek SIM/eSIM selection.
Android's selected-LPA access checks remain unchanged. The existing Google LPA
keeps its service priority, platform permissions, implementation and profile UI.

Settings exposes SIM 2 and eSIM in both the current and legacy SIM screens.
Its intent reaches the existing permission-protected eUICC dispatcher. On this
device, provisioning and management first enter a non-exported activity within
TeleService. Selecting a connection requires explicit confirmation. It is refused
for restricted users and during calls; the restrictions are checked again just
before the modem write. Opening the screen only reads state. No boot-time switch
or autonomous carrier-profile operation is performed.

After selection, an independent modem read must confirm the requested state.
Before forwarding provisioning/management to the existing LUI, the framework
must report an active eUICC in physical slot 1 with an EID. The wait is bounded.
The UI can return to physical SIM 2 even if the selected eUICC is unavailable.
Rotation retains an in-flight operation without retaining an Activity or profile
identifiers. The existing LUI resolution and caller result forwarding remain.

## Verified vendor contract

The command layout was checked against stock malachite MtkTeleService and
mediatek-telephony-common. The installed vendor library uses ABI version 2,
even though the stock Java framework supports version 3. Version/hash getters
and callback hash initializers were checked in mtkradioex.modem-V2-ndk.so,
SHA-256 2b0c2ab959c58e44b299fc083ce12cd0723c80678f609d8128ed2a6ac616eede.

| Contract | Stock behavior |
| --- | --- |
| Endpoint | vendor.mediatek.hardware.mtkradioex.modem.IMtkRadioExModem/slot2 |
| ABI version/hash | 2 / 87512b9a1978fdb596a8d9176854d3761382dc82 |
| Request transaction | 11; serial, string array, client ID 0; one-way |
| Client-0 callbacks | transaction 26; response binder, indication binder |
| String response | transaction 7; RadioResponseInfo, string array |
| Acknowledgement | modem transaction 25 |
| Read | MIPC_GET_ESIM_STATE; 0 = SIM 2, 1 = eSIM |
| Select | MIPC_SET_ESIM_STATE; string 1 = eSIM, 0 = SIM 2 |
| Accepted select result | 0/1 only, followed by an independent state read |
| Response delimiter | comma; verified in stock com.ot.pubsub.util.t.b |

The AOSP phone process does not contain MtkRIL. The supplied MediaTek IMS APK
uses the separate client-1 callback registration (transaction 27). This narrow
client belongs to the radio UID in TeleService and uses client 0. It must not
coexist with another owner of client 0, such as stock MtkRIL.

The adapter checks the exact ABI before registration or commands. Its response
parcelable comes from the public Android radio AIDL dependency of TeleService.
Requests are serialized, matched by serial and bounded by timeouts. Binder
death releases a pending waiter, and acknowledgement-required callbacks are
acknowledged. MEP statuses 4/5 are unsupported and never reported as success.
There is no exported raw-APDU or general modem-command interface. Logs contain
bounded status/error names, not EIDs, activation codes or profile identifiers.

The existing radio-domain MediaTek SELinux policy permits this HAL connection.
No policy weakening, root executable, vendor firmware change, EID write or
regional feature override is part of the change. Both framework integrations
are disabled by default and enabled by device resource overlays; the unmasked
eUICC feature and administrator restrictions are additionally required.

## Reproducing the candidate

Apply patches/native-esim/0001-TeleService-native-esim.patch in
packages/services/Telephony at baseline 95e95093d0e9cca76b86906d414a7da6b95d45fe,
and patches/native-esim/0002-Settings-native-esim.patch in packages/apps/Settings
at baseline 9a102220cb80941628685585b6818e5715271cf0. Use git apply --check first;
do not overwrite unrelated local changes. No OpenEUICC dependency is required
for the product. Retained research checkouts in an existing workspace are unused.

Build TeleService, Settings, TeleServiceResOverlayMalachite and
SettingsResOverlayMalachite, then the full target-files and OTA. Run installclean
before packaging when coming from the experimental build to remove stale APKs.
The parser test at tests/java/com/android/phone/euicc/EsimStatusTest.java compiles
with TeleService's src/com/android/phone/euicc/EsimStatus.java on the host JDK.
It covers malformed replies and valid/error statuses, not modem hardware access.

## Verification status and remaining gates

The four component targets compiled successfully on 9 September 2026. The host
parser test passed. A read-only shell transport probe failed before sending a
modem command; it does not establish the behavior of the privileged radio UID.
The first native OTA still requires installation and a real hardware test.

Inspect the final target-files for native classes, platform signatures, internal
activity boundaries, enabled overlays, unchanged Google LPA, and absence of the
two added experimental apps and their permissions. Preserve the previously
verified NFC, secure-video, VINTF and SELinux inputs. On the installed candidate,
check read/selection/readback, framework eUICC recognition, LPA access, return to
the original SIM selection, and physical SIM/IMS regressions. Carrier activation
must remain unverified until the user performs it with their own profile.
