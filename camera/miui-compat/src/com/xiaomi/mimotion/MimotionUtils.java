/*
 * SPDX-FileCopyrightText: 2026 The LineageOS Project
 * SPDX-License-Identifier: Apache-2.0
 */

package com.xiaomi.mimotion;

/** Compatibility surface for MIUI's optional display refresh-rate controller. */
public final class MimotionUtils {
    private MimotionUtils() {}

    public static boolean isEnabled() {
        return false;
    }

    public static boolean setPreferredRefreshRate(Object token, int refreshRate) {
        return false;
    }
}
