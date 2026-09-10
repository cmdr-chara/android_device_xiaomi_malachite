/*
 * SPDX-FileCopyrightText: 2026 The LineageOS Project
 * SPDX-License-Identifier: Apache-2.0
 */

package miui.security;

/** Compatibility surface for MIUI App Lock checks. */
public class SecurityManager {
    public boolean checkAccessControlPass(String packageName) {
        return false;
    }

    public boolean getApplicationAccessControlEnabled(String packageName) {
        return false;
    }
}
