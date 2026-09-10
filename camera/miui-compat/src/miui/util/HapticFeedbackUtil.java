/*
 * SPDX-FileCopyrightText: 2026 The LineageOS Project
 * SPDX-License-Identifier: Apache-2.0
 */

package miui.util;

import android.content.Context;
import android.os.VibrationAttributes;

/** Compatibility surface that lets MIUIX fall back to Android haptics. */
public class HapticFeedbackUtil {
    public HapticFeedbackUtil(Context context, boolean always) {}

    public static boolean isSupportLinearMotorVibrate() {
        return false;
    }

    public static boolean isSupportLinearMotorVibrate(int effectId) {
        return false;
    }

    public boolean performExtHapticFeedback(int effectId) {
        return false;
    }

    public boolean performHapticFeedback(int effectId, double strength, String reason) {
        return false;
    }

    public boolean performHapticFeedback(int effectId, boolean always) {
        return false;
    }

    public boolean performHapticFeedback(int effectId, boolean always, int fallbackEffect) {
        return false;
    }

    public boolean performHapticFeedback(
            VibrationAttributes attributes, int effectId, double strength, String reason) {
        return false;
    }

    public boolean performHapticFeedback(
            VibrationAttributes attributes, int effectId, boolean always) {
        return false;
    }

    public boolean performHapticFeedback(
            VibrationAttributes attributes, int effectId, boolean always, int fallbackEffect) {
        return false;
    }
}
