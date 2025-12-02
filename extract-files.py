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

from extract_utils.fixups_lib import (
    lib_fixup_remove_arch_suffix,
    lib_fixups_user_type,
    libs_clang_rt_ubsan,
)

namespace_imports = [
    'device/xiaomi/malachite',
    'hardware/mediatek',
    'hardware/mediatek/libaedv',
    'hardware/xiaomi',
]

lib_fixups: lib_fixups_user_type = {
    libs_clang_rt_ubsan: lib_fixup_remove_arch_suffix,
}

blob_fixups: blob_fixups_user_type = {
     'vendor/lib64/libmt_mitee.so': blob_fixup()
        .replace_needed('android.hardware.security.keymint-V3-ndk.so', 'android.hardware.security.keymint-V4-ndk.so'),

     'vendor/lib64/hw/audio.primary.mt6878.so': blob_fixup()
        .add_needed('libstagefright_foundation-v33.so')
        .replace_needed('libalsautils.so', 'libalsautils-stock.so')
        .binary_regex_replace(b'A2dpsuspendonly', b'A2dpSuspended\x00\x00')
        .binary_regex_replace(b'BTAudiosuspend', b'A2dpSuspended\x00'),

     'vendor/lib64/libsi_sixth.so': blob_fixup()
        .replace_needed('audio.primary.mediatek.so', 'audio.primary.mt6878.so'),

     'vendor/etc/init/android.hardware.graphics.composer@3.2-service.rc': blob_fixup()
        .regex_replace('ServiceCapacityLow', 'ProcessCapacityHigh HighPerformance'),

    ('vendor/lib64/hw/vendor.mediatek.hardware.pq_aidl-impl.so', 'odm/bin/hw/vendor.xiaomi.sensor.citsensorservice.aidl'): blob_fixup()
        .add_needed('libui_shim.so'),

    ('odm/lib64/nfc_nci.thn31nfc.tms.so', 'odm/lib64/tms-utils.so'): blob_fixup()
        .add_needed('libbase_shim.so'),

    'vendor/lib64/c2.dolby.client.so': blob_fixup()
        .add_needed('dolbycodec_shim.so'),

    'vendor/lib64/libmicamera_hal_core.so': blob_fixup()
        .add_needed('libui_shim.so')
        .add_needed('libprocessgroup_shim.so')
        .replace_needed('libui.so', 'libui-v34.so'),

    ('vendor/lib64/lib3a.ae.stat.so', 'vendor/lib64/libarmnn_ndk.mtk.vndk.so'): blob_fixup()
        .add_needed('liblog.so'),

    ('vendor/lib64/c2.dolby.hevc.dec.so', 'vendor/lib64/c2.dolby.hevc.sec.dec.so'): blob_fixup()
        .add_needed('libcodec2_shim.so'),

    'vendor/lib64/libultrahdr_malachite.so': blob_fixup()
        .replace_needed('libjpegencoder.so', 'libjpegencoder_malachite.so')
        .replace_needed('libjpegdecoder.so', 'libjpegdecoder_malachite.so'),

    ('odm/lib64/camera/plugins/com.xiaomi.plugin.gainmap.so',
     'odm/lib64/camera/plugins/com.xiaomi.plugin.jpegrAggr.so',
     'vendor/lib64/libmtkcam_hwnode.jpegnode.so'): blob_fixup()
        .replace_needed('libultrahdr.so', 'libultrahdr_malachite.so'),


    ('vendor/lib64/libneuralnetworks_sl_driver_mtk_prebuilt.so',
     'vendor/lib64/libTrueSight.so',
     'vendor/lib64/libwa_widelens_undistort.so',
     'vendor/lib64/libMiPhotoFilter.so',
     'vendor/lib64/libMiVideoFilter.so'): blob_fixup()
        .clear_symbol_version('AHardwareBuffer_allocate')
        .clear_symbol_version('AHardwareBuffer_createFromHandle')
        .clear_symbol_version('AHardwareBuffer_describe')
        .clear_symbol_version('AHardwareBuffer_getNativeHandle')
        .clear_symbol_version('AHardwareBuffer_isSupported')
        .clear_symbol_version('AHardwareBuffer_lock')
        .clear_symbol_version('AHardwareBuffer_lockPlanes')
        .clear_symbol_version('AHardwareBuffer_release')
        .clear_symbol_version('AHardwareBuffer_unlock'),

    ('vendor/lib64/libcameraopt.so',
     'vendor/lib64/libcam.hal3a.so',
     'vendor/lib64/libcam.hal3a.ctrl.so',
     'vendor/lib64/libmtkcam_taskmgr.so',
     'vendor/lib64/hw/hwcomposer.mtk_common.so'): blob_fixup()
        .add_needed('libprocessgroup_shim.so'),

    ('odm/lib64/camera/plugins/com.xiaomi.plugin.capdepth.so', 'vendor/lib64/libalNN.so', 'vendor/lib64/libmiphone_preview_bokeh.so', 'vendor/lib64/libmiphone_preview_mdbokeh.so'): blob_fixup()
        .replace_needed('libomp.so', 'libomp_vendor.so'),

    'odm/lib64/libHISCppAlgos_odm.so': blob_fixup()
        .replace_needed('libhis_motion_tracker.so', 'libhis_motion_tracker_odm.so'),

    ('odm/lib64/camera/plugins/com.xiaomi.plugin.mihisv1.so',
     'odm/lib64/camera/plugins/com.xiaomi.plugin.mihisv2.so',
     'odm/lib64/camera/plugins/com.xiaomi.plugin.mihisv3.so'): blob_fixup()
        .replace_needed('libHISCppAlgos.so','libHISCppAlgos_odm.so'),

    'vendor/lib64/vendor.mediatek.hardware.bluetooth.audio-V1-ndk.so': blob_fixup()
        .replace_needed('android.hardware.audio.common-V1-ndk.so', 'android.hardware.audio.common-V2-ndk.so'),

    ('vendor/bin/hw/android.hardware.graphics.allocator-V2-service-mediatek',
     'vendor/lib64/egl/libGLES_mali.so',
     'vendor/lib64/hw/android.hardware.graphics.allocator-V2-mediatek.so',
     'vendor/lib64/hw/android.hardware.graphics.mapper@4.0-impl-mediatek.so',
     'vendor/lib64/hw/mapper.mediatek.so',
     'vendor/lib64/libcodec2_fsr.so',
     'vendor/lib64/libcodec2_vpp_AIMEMC_plugin.so',
     'vendor/lib64/libcodec2_vpp_AISR_plugin.so',
     'vendor/lib64/libmtkcam_grallocutils_aidlv1helper.so',
     'vendor/lib64/vendor.mediatek.hardware.camera.isphal-V1-ndk.so',
     'vendor/lib64/vendor.mediatek.hardware.pq_aidl-V2-ndk.so',
     'vendor/lib64/vendor.mediatek.hardware.pq_aidl-V3-ndk.so',
     'vendor/lib64/vendor.mediatek.hardware.pq_aidl-V4-ndk.so',
     'vendor/lib64/vendor.mediatek.hardware.pq_aidl-V7-ndk.so'): blob_fixup()
        .replace_needed('android.hardware.graphics.common-V4-ndk.so', 'android.hardware.graphics.common-V6-ndk.so')
        .replace_needed('android.hardware.graphics.allocator-V1-ndk.so', 'android.hardware.graphics.allocator-V2-ndk.so'),

    'vendor/lib64/libmtkcam_grallocutils.so': blob_fixup()
        .replace_needed('libui.so', 'libui-v34.so')
        .replace_needed('android.hardware.graphics.common-V4-ndk.so', 'android.hardware.graphics.common-V6-ndk.so')
        .replace_needed('android.hardware.graphics.allocator-V1-ndk.so', 'android.hardware.graphics.allocator-V2-ndk.so'),

    'vendor/lib64/libmialgoengine.so': blob_fixup()
        .add_needed('libprocessgroup_shim.so')
        .replace_needed('libui.so', 'libui-v34.so'),

    'vendor/lib64/libpqconfig.so': blob_fixup()
        .replace_needed('android.hardware.sensors-V2-ndk.so', 'android.hardware.sensors-V3-ndk.so'),
}  # fmt: skip

module = ExtractUtilsModule(
    'malachite',
    'xiaomi',
    blob_fixups=blob_fixups,
    lib_fixups=lib_fixups,
    namespace_imports=namespace_imports,
)

if __name__ == '__main__':
    utils = ExtractUtils.device(module)
    utils.run()
