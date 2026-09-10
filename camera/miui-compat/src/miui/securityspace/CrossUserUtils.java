/*
 * SPDX-FileCopyrightText: 2026 The LineageOS Project
 * SPDX-License-Identifier: Apache-2.0
 */

package miui.securityspace;

import android.content.Context;

/** Compatibility surface for MIUI Second Space callers. */
public final class CrossUserUtils {
    private CrossUserUtils() {}

    public static boolean checkUidPermission(Context context, String callingPackage) {
        return false;
    }
}
