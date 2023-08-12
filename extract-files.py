#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: 2024 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

from extract_utils.fixups_blob import (
    BlobFixupCtx,
    File,
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

from extract_utils.tools import (
    llvm_objdump_path,
)

from extract_utils.utils import (
    run_cmd,
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

def blob_fixup_graphic_buffer_size(
    ctx: BlobFixupCtx,
    file: File,
    file_path: str,
    *args,
    **kwargs,
):
    for line in run_cmd(
        [
            llvm_objdump_path,
            '--disassemble-all',
            file_path,
        ]
    ).splitlines():
        line = line.split(maxsplit=5)
        if len(line) != 6:
            continue

        # The size of GraphicBuffer changed from 0x100 to 0xd30
        offset, _, instruction, register, value, _ = line
        if instruction == 'mov' and register[:-1] == 'w0' and value == '#0x100':
            with open(file_path, 'rb+') as f:
                f.seek(int(offset[:-1], 16))
                f.write(b'\x00\xa6\x81\x52')  # AArch64 mov w0, #0xd30

blob_fixups: blob_fixups_user_type = {
     'vendor/lib64/hw/audio.primary.mt6878.so': blob_fixup()
        .replace_needed('libtinyxml2.so', 'libtinyxml2-v34.so')
        .replace_needed('libalsautils.so', 'libalsautils-stock.so')
        .binary_regex_replace(b'A2dpsuspendonly', b'A2dpSuspended\x00\x00')
        .binary_regex_replace(b'BTAudiosuspend', b'A2dpSuspended\x00'),

     'vendor/lib64/libsi_sixth.so': blob_fixup()
        .replace_needed('audio.primary.mediatek.so', 'audio.primary.mt6878.so'),

     'vendor/etc/init/android.hardware.graphics.composer@3.2-service.rc': blob_fixup()
        .regex_replace('ServiceCapacityLow', 'ProcessCapacityHigh HighPerformance'),

     'vendor/etc/vintf/manifest/manifest_media_c2_V1_2_default.xml': blob_fixup()
        .regex_replace(r'\s*<fqname>@1\.0::IComponentStore/dolby</fqname>\s*\n', '')
        .regex_replace(r'(</interface>)\s*(</hal>)', r'\1\n    \2'),

     'vendor/etc/init/vendor.xiaomi.sensor.citsensorservice.aidl.rc': blob_fixup()
        .add_line_if_missing('    task_profiles ServiceCapacityLow'),

    ('vendor/lib64/hw/vendor.mediatek.hardware.pq_aidl-impl.so', 'odm/bin/hw/vendor.xiaomi.sensor.citsensorservice.aidl'): blob_fixup()
        .replace_needed('libtinyxml2.so', 'libtinyxml2-v34.so')
        .add_needed('libui_shim.so'),

    ('odm/lib64/nfc_nci.thn31nfc.tms.so', 'odm/lib64/tms-utils.so'): blob_fixup()
        .add_needed('libbase_shim.so'),

    'vendor/lib64/libmicamera_hal_core.so': blob_fixup()
        .add_needed('libui_shim.so')
        .add_needed('libprocessgroup_shim.so')
        .replace_needed('libtinyxml2.so', 'libtinyxml2-v34.so')
        .call(blob_fixup_graphic_buffer_size),

    ('vendor/lib64/lib3a.ae.stat.so', 'vendor/lib64/libarmnn_ndk.mtk.vndk.so'): blob_fixup()
        .add_needed('liblog.so'),

    'vendor/lib64/libultrahdr_malachite.so': blob_fixup()
        .replace_needed('libjpegencoder.so', 'libjpegencoder_malachite.so')
        .replace_needed('libjpegdecoder.so', 'libjpegdecoder_malachite.so'),

    ('odm/lib64/camera/plugins/com.xiaomi.plugin.gainmap.so',
     'odm/lib64/camera/plugins/com.xiaomi.plugin.jpegrAggr.so',
     'vendor/lib64/libmtkcam_hwnode.jpegnode.so'): blob_fixup()
        .replace_needed('libultrahdr.so', 'libultrahdr_malachite.so'),


    ('vendor/lib64/hw/vendor.mediatek.hardware.pq_aidl-impl.so',
     'vendor/lib64/libpqxmlflagparser.so',
     'vendor/lib64/libpqxmlparser.so',
     'vendor/lib64/librt_extamp_intf.so',
     'vendor/lib64/libsilkybrightnesscore.so',
     'vendor/lib64/libmicamera_aidl_provider.so',
     'vendor/lib64/libmmlpqImpl.so'): blob_fixup()
        .replace_needed('libtinyxml2.so', 'libtinyxml2-v34.so'),

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
     'vendor/lib64/libcodec2_vpp_AIMEMC_plugin.so',
     'vendor/lib64/libcodec2_vpp_AISR_plugin.so',
     'vendor/lib64/libmtkcam_grallocutils.so',
     'vendor/lib64/libmtkcam_grallocutils_aidlv1helper.so',
     'vendor/lib64/vendor.mediatek.hardware.camera.isphal-V1-ndk.so',
     'vendor/lib64/vendor.mediatek.hardware.pq_aidl-V2-ndk.so',
     'vendor/lib64/vendor.mediatek.hardware.pq_aidl-V4-ndk.so',
     'vendor/lib64/vendor.mediatek.hardware.pq_aidl-V7-ndk.so'): blob_fixup()
        .replace_needed('android.hardware.graphics.common-V4-ndk.so', 'android.hardware.graphics.common-V7-ndk.so')
        .replace_needed('android.hardware.graphics.allocator-V1-ndk.so', 'android.hardware.graphics.allocator-V2-ndk.so'),

    'vendor/lib64/libcodec2_fsr.so': blob_fixup()
        .call(blob_fixup_graphic_buffer_size)
        .replace_needed('android.hardware.graphics.common-V4-ndk.so', 'android.hardware.graphics.common-V7-ndk.so')
        .replace_needed('android.hardware.graphics.allocator-V1-ndk.so', 'android.hardware.graphics.allocator-V2-ndk.so'),

    'vendor/lib64/libmialgoengine.so': blob_fixup()
        .add_needed('libprocessgroup_shim.so')
        .call(blob_fixup_graphic_buffer_size),

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
