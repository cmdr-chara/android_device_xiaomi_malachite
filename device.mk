#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

# Shipping API level
PRODUCT_SHIPPING_API_LEVEL := 34

# Soong namespaces
PRODUCT_SOONG_NAMESPACES += \
    $(LOCAL_PATH)

# Dynamic Partitions
PRODUCT_USE_DYNAMIC_PARTITIONS := true

# Inherit the proprietary files
$(call inherit-product, vendor/xiaomi/malachite/malachite-vendor.mk)
