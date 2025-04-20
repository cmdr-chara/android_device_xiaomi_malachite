#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

DEVICE_PATH := device/xiaomi/malachite

# Architecture
TARGET_ARCH := arm64
TARGET_ARCH_VARIANT := armv8-2a-dotprod
TARGET_CPU_ABI := arm64-v8a
TARGET_CPU_VARIANT := cortex-a78

# Boot Image
AB_OTA_PARTITIONS += \
    boot

BOARD_BOOTIMAGE_PARTITION_SIZE := 67108864

# init_boot image
AB_OTA_PARTITIONS += \
    init_boot

BOARD_INIT_BOOT_HEADER_VERSION := 4
BOARD_INIT_BOOT_IMAGE_PARTITION_SIZE := 8388608

BOARD_MKBOOTIMG_INIT_ARGS += --header_version $(BOARD_INIT_BOOT_HEADER_VERSION)

# Kernel
BOARD_USES_GENERIC_KERNEL_IMAGE := true
BOARD_KERNEL_IMAGE_NAME := Image.gz

TARGET_KERNEL_SOURCE := kernel/xiaomi/mt6878
TARGET_KERNEL_CONFIG := \
    gki_defconfig \
    vendor/malachite.config

# Kernel Modules
TARGET_KERNEL_EXT_MODULE_ROOT := kernel/xiaomi/mt6878-modules

TARGET_KERNEL_EXT_MODULES := \
    connectivity/bt/mt66xx/btif \
    connectivity/common \
    connectivity/connfem \
    connectivity/conninfra \
    connectivity/gps/data_link/plat/v051 \
    connectivity/gps/gps_pwr \
    connectivity/gps/gps_scp \
    connectivity/wlan/adaptor \
    connectivity/wlan/core/gen4m \
    gpu \
    udc

# vendor_boot image
AB_OTA_PARTITIONS += \
    vendor_boot

BOARD_KERNEL_CMDLINE := bootopt=64S3,32N2,64N2

BOARD_BOOT_HEADER_VERSION := 4

BOARD_DTB_OFFSET := 0x07c88000
BOARD_KERNEL_BASE := 0x3fff8000
BOARD_KERNEL_OFFSET := 0x00008000
BOARD_KERNEL_PAGESIZE := 4096
BOARD_KERNEL_TAGS_OFFSET := 0x07c88000
BOARD_RAMDISK_OFFSET := 0x26f08000

BOARD_MKBOOTIMG_ARGS := --dtb_offset $(BOARD_DTB_OFFSET)
BOARD_MKBOOTIMG_ARGS += --base $(BOARD_KERNEL_BASE)
BOARD_MKBOOTIMG_ARGS += --kernel_offset $(BOARD_KERNEL_OFFSET)
BOARD_MKBOOTIMG_ARGS += --pagesize $(BOARD_KERNEL_PAGESIZE)
BOARD_MKBOOTIMG_ARGS += --tags_offset $(BOARD_KERNEL_TAGS_OFFSET)
BOARD_MKBOOTIMG_ARGS += --ramdisk_offset $(BOARD_RAMDISK_OFFSET)
BOARD_MKBOOTIMG_ARGS += --header_version $(BOARD_BOOT_HEADER_VERSION)

BOARD_INCLUDE_RECOVERY_RAMDISK_IN_VENDOR_BOOT := true
BOARD_MOVE_RECOVERY_RESOURCES_TO_VENDOR_BOOT := true
BOARD_VENDOR_BOOTIMAGE_PARTITION_SIZE := 67108864

# Inherit the proprietary files
include vendor/xiaomi/malachite/BoardConfigVendor.mk
