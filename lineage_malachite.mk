#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

# Inherit from those products. Most specific first.
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit_only.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)

# Inherit from device makefile.
$(call inherit-product, device/xiaomi/malachite/device.mk)

# Inherit some common LineageOS stuff.
$(call inherit-product, vendor/lineage/config/common_full_phone.mk)

PRODUCT_NAME := lineage_malachite
PRODUCT_DEVICE := malachite
PRODUCT_MANUFACTURER := Xiaomi
PRODUCT_BRAND := Redmi
PRODUCT_MODEL := 24090RA29G

PRODUCT_BUILD_PROP_OVERRIDES += \
    BuildDesc="malachite_global-user 15 UP1A.231005.007 OS2.0.3.0.VOOMIXM release-keys" \
    BuildFingerprint=Redmi/malachite_global/malachite:15/UP1A.231005.007/OS2.0.3.0.VOOMIXM:user/release-keys

PRODUCT_GMS_CLIENTID_BASE := android-xiaomi
