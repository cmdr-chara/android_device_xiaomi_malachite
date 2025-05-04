#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: 2024 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

from extract_utils.fixups_blob import (
    blob_fixup,
    blob_fixups_user_type,
)

from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)

namespace_imports = [
    'device/xiaomi/malachite',
    'hardware/mediatek',
    'hardware/xiaomi',
]

blob_fixups: blob_fixups_user_type = {
    'vendor/bin/hw/android.hardware.security.keymint@3.0-service.mitee': blob_fixup()
        .replace_needed('android.hardware.security.keymint-V3-ndk.so', 'android.hardware.security.keymint-V4-ndk.so'),

    'vendor/lib64/hw/vendor.mediatek.hardware.pq_aidl-impl.so': blob_fixup()
        .add_needed('libui_shim.so'),

    'vendor/lib64/lib3a.ae.stat.so': blob_fixup()
        .add_needed('liblog.so'),

    ('odm/lib64/camera/plugins/com.xiaomi.plugin.capdepth.so', 'vendor/lib64/libalNN.so', 'vendor/lib64/libmiphone_preview_bokeh.so', 'vendor/lib64/libmiphone_preview_mdbokeh.so'): blob_fixup()
        .replace_needed('libomp.so', 'libomp_vendor.so'),

    'vendor/lib64/vendor.mediatek.hardware.bluetooth.audio-V1-ndk.so': blob_fixup()
        .replace_needed('android.hardware.audio.common-V1-ndk.so', 'android.hardware.audio.common-V2-ndk.so'),

    ('vendor/bin/hw/android.hardware.graphics.allocator-V2-service-mediatek.mt6878',
     'vendor/lib64/egl/libGLES_mali.so',
     'vendor/lib64/hw/android.hardware.graphics.allocator-V2-mediatek.so',
     'vendor/lib64/hw/android.hardware.graphics.mapper@4.0-impl-mediatek.so',
     'vendor/lib64/hw/mapper.mediatek.so',
     'vendor/lib64/libaimemc.so',
     'vendor/lib64/libcodec2_fsr.so',
     'vendor/lib64/libcodec2_vpp_AIMEMC_plugin.so',
     'vendor/lib64/libcodec2_vpp_AISR_plugin.so',
     'vendor/lib64/libmtkcam_grallocutils.so',
     'vendor/lib64/libmtkcam_grallocutils_aidlv1helper.so',
     'vendor/lib64/vendor.mediatek.hardware.camera.isphal-V1-ndk.so',
     'vendor/lib64/vendor.mediatek.hardware.pq_aidl-V2-ndk.so',
     'vendor/lib64/vendor.mediatek.hardware.pq_aidl-V3-ndk.so',
     'vendor/lib64/vendor.mediatek.hardware.pq_aidl-V4-ndk.so',
     'vendor/lib64/vendor.mediatek.hardware.pq_aidl-V7-ndk.so'): blob_fixup()
        .replace_needed('android.hardware.graphics.common-V4-ndk.so', 'android.hardware.graphics.common-V6-ndk.so')
        .replace_needed('android.hardware.graphics.allocator-V1-ndk.so', 'android.hardware.graphics.allocator-V2-ndk.so'),

    'vendor/lib64/libpqconfig.so': blob_fixup()
        .replace_needed('android.hardware.sensors-V2-ndk.so', 'android.hardware.sensors-V3-ndk.so'),
}  # fmt: skip

module = ExtractUtilsModule(
    'malachite',
    'xiaomi',
    blob_fixups=blob_fixups,
    namespace_imports=namespace_imports,
)

if __name__ == '__main__':
    utils = ExtractUtils.device(module)
    utils.run()
