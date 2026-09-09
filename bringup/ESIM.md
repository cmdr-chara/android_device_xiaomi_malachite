# eSIM integration on malachite

Status: implementation candidate; modem selection and profile access still need
verification on the phone. Do not infer an accessible eUICC from the framework
feature or the non-removable-slot overlay alone.

## Why a system integration is required

The September 9 baseline reports both active UICC slots as non-eUICC, with no EID.
Google's metadata request completes with `RESULT_MUST_DEACTIVATE_SIM`, while its
activation UI remains on the network-information screen. This is a resolvable
activation result, not proof of an Internet failure.

OpenEUICC supplies an alternative LPA. Its Magisk installer primarily makes the
APK a privileged system application and installs the permission allowlist. This
device instead builds OpenEUICC directly into `system_ext`, without root.

On this Android version, `PhoneInterfaceManager.iccOpenLogicalChannelWithPermission`
also checks that the caller opening the standard ISD-R AID is the selected LPA.
A correctly attributed ADB-shell probe had `MODIFY_PHONE_STATE` but was rejected
by that additional check. Installing another APK or granting that permission
alone does not exercise access to the eSIM chip.

The OpenEUICC integration gives its EuiccService and management/provisioning UI
priority 101. The imported Google package uses 100. This makes the LPA selection
deterministic. OpenEUICC's own privileged allowlist remains in its source tree;
the device grants its requested runtime `READ_PHONE_STATE` permission by default.
Its upstream carrier-app metadata and discovery limitations still apply.

## MediaTek selection

OpenEUICC does not implement Xiaomi's MediaTek physical-SIM/eSIM selection.
`MalachiteEsimSettings` provides a separate entry in Network settings. Merely
opening it reads the current state. Changing the selection requires an explicit
button and confirmation, is refused during a call, and is followed by a state
read. The eSIM shares the second connection with physical SIM 2.

The commands below were checked against the stock malachite `MtkTeleService.apk`
and `mediatek-telephony-common.jar`. The actual vendor ABI is version 2: the stock
Java framework supports version 3, while the installed vendor library still
exports version 2. Version/hash getters and callback hash initializers were
checked directly in the imported `mtkradioex.modem-V2-ndk.so`; its SHA-256 is
`2b0c2ab959c58e44b299fc083ce12cd0723c80678f609d8128ed2a6ac616eede`.

| Contract | Verified stock behavior |
| --- | --- |
| Endpoint | `vendor.mediatek.hardware.mtkradioex.modem.IMtkRadioExModem/slot2` |
| ABI version/hash | `2` / `87512b9a1978fdb596a8d9176854d3761382dc82` |
| Request transaction | 11, `serial`, string array, client ID 0; one-way |
| Client-0 callbacks | transaction 26, response binder then indication binder |
| String response | response transaction 7, `RadioResponseInfo`, string array |
| Acknowledgement | modem transaction 25 |
| Read command | `MIPC_GET_ESIM_STATE` |
| Read states | 0 = physical SIM 2; 1 = eSIM |
| Select command | `MIPC_SET_ESIM_STATE`, `"1"` for eSIM or `"0"` for SIM 2 |
| Select result | only 0/1 accepted, followed by an independent read |
| Response delimiter | comma, verified in stock `com.ot.pubsub.util.t.b` |

The current AOSP phone process does not contain `MtkRIL`. The supplied MediaTek
IMS APK registers the modem's separate `setResponseFunctionsMtkIms` callback
(transaction 27), using client 1. The controller uses client 0; it must not be
combined with another owner of that same vendor client, such as stock MtkRIL.

The narrow handwritten Binder adapter checks the exact version and hash before
registering callbacks or sending commands. Its parcelable is generated from the
public Android radio AIDL definition. Requests are serialized, replies are
matched by serial, waits are bounded, Binder death releases the waiter, and
acknowledgement-required callbacks are acknowledged. Modem payloads and eSIM
identifiers are not logged. No general AT-command or raw-APDU interface is
exported by the application.

The application is platform signed, preinstalled, and uses the system shared
UID. The existing MediaTek SELinux policy already permits `system_app` to use
the telephony HAL. This integration must keep SELinux enforcing; it adds no
root executable, permissive domain, vendor property override, firmware
downgrade, EID write, automatic profile operation, or automatic boot-time switch.
MEP retry statuses 4/5 are unsupported and must not be reported as success.

## Pinned source inputs

| Project | Commit |
| --- | --- |
| `estkme-group/openeuicc` | `9a537a25163c5159899260fb6191a5da35a692bd` |
| `PeterCxy/android_prebuilts_openeuicc-deps` | `540216793010cabc49782bd01844cd8dd28a4c7c` |
| OpenEUICC lpac submodule | `d214738fa0bdb23faf5833d3d798963079a00468` |
| OpenEUICC cJSON submodule | `c859b25da02955fef659d658b8f324b5cde87be3` |

Build the app in `packages/apps/OpenEUICC`, with dependencies in
`prebuilts/openeuicc-deps`. The latter's generated build file uses SDK 37
upstream; the integration patch uses the current platform SDK (36 here).
The other patch raises the two LPA intent priorities to 101. Preserve both
patches when refreshing upstream; re-evaluate the selected-LPA access check,
the upstream service contract, and the dependency/API compatibility together.

For a fresh tree, copy `bringup/openeuicc.xml` into `.repo/local_manifests/`,
sync those two project paths, then apply
`patches/openeuicc/0001-prefer-openeuicc-lpa.patch` in the app project and
`0002-use-platform-sdk.patch` in the dependency project. The manifest enables
submodule sync; use `repo sync --fetch-submodules` or explicitly run
`git submodule update --init` in the app project and verify both recorded
submodule commits. Do not force-checkout either project over unrelated local edits.

The parser can be tested on a host JDK by compiling `EsimStatus.java` together
with `tests/java/org/lineageos/malachite/esim/EsimStatusTest.java` and running
`org.lineageos.malachite.esim.EsimStatusTest`. This covers valid/error statuses,
the verified comma delimiter, and malformed replies; it does not replace a
modem test. `m -j1 OpenEUICC MalachiteEsimSettings` compiled successfully before
the final full-ROM build.

## Verification gates

- Compile both apps and the complete target-files/OTA candidate; inspect the
  packaged permissions, LPA priorities, JNI library and SELinux policy.
- On the installed candidate, confirm the selected LPA, controller permissions,
  SELinux mode, and a bounded `MIPC_GET_ESIM_STATE` reply.
- Confirm a requested selection by reading modem state and observing the
  framework's card state. Do not claim success merely from a switch response.
- Confirm OpenEUICC can read the internal chip without exporting an EID or
  profile identifiers. Let the user perform any carrier-profile download.
- Preserve the prior NFC, secure-video, IMS and physical-SIM behavior; an
  untested carrier activation remains an explicit release limitation.
