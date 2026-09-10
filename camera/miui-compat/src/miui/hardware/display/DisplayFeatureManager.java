/*
 * SPDX-FileCopyrightText: 2026 The LineageOS Project
 * SPDX-License-Identifier: Apache-2.0
 */

package miui.hardware.display;

/** No-op compatibility surface for MIUI display effects used by MiuiCamera. */
public final class DisplayFeatureManager {
    private static final DisplayFeatureManager INSTANCE = new DisplayFeatureManager();

    private DisplayFeatureManager() {}

    public static DisplayFeatureManager getInstance() {
        return INSTANCE;
    }

    public void setScreenEffect(int effect, int value) {}
}
