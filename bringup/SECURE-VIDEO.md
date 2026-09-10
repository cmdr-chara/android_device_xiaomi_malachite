# Secure video feature gate

The verified malachite OS2.0.208 vendor properties enable
`ro.vendor.mtk_sec_video_path_support=1`. The shipped MTK decoder library
reads this property with a default of `0` and rejects a requested secure mode
when its numeric value is zero. Keep the property consistent with the AVC,
HEVC and VP9 secure decoder entries in both codec configuration files.

The baseline Lineage build lacks this property and exposes no secure video
decoder through `MediaCodecList.ALL_CODECS`. A direct MediaCodec request
using a `.secure` name can fall back to the ordinary component: always inspect
`getCanonicalName()`, capability metadata, and runtime configuration, not just
`getName()` or successful allocation. L1 provisioning and session opening
succeeded independently on that baseline.

This change restores the stock feature gate. On-device validation must confirm
secure list entries, canonical component identity, and decoder startup using
L1 MediaCrypto and a protected output surface. A startup test without queued
media does not establish decryption, Netflix licensing, or HD playback. The
separate L3 provisioning context is not modified or treated as a proven defect.

The cross-file contract test fails if secure decoders are advertised while
their driver gate is absent or disabled. Preserve the verified NFC stack and
OS2.0.208 firmware while testing this bounded correction.
