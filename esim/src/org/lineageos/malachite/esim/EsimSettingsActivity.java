// SPDX-License-Identifier: Apache-2.0
package org.lineageos.malachite.esim;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.telecom.TelecomManager;
import android.util.Log;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import java.io.IOException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class EsimSettingsActivity extends Activity {
    private static final String TAG = "MalachiteEsim";
    private static final ExecutorService WORKER = Executors.newSingleThreadExecutor();
    private static final String LPA_PACKAGE = "im.angry.openeuicc";
    private TextView status;
    private Button toggle;
    private Button refresh;
    private Button manage;
    private int currentState = -1;
    private boolean busy;

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        if (getActionBar() != null) getActionBar().setDisplayHomeAsUpEnabled(true);
        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        int padding = Math.round(24 * getResources().getDisplayMetrics().density);
        content.setPadding(padding, padding, padding, padding);
        content.setGravity(Gravity.TOP);
        status = new TextView(this);
        status.setTextSize(22);
        status.setText(R.string.checking);
        content.addView(status, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        TextView explanation = new TextView(this);
        explanation.setText(R.string.explanation);
        explanation.setTextSize(16);
        explanation.setPadding(0, padding, 0, padding);
        content.addView(explanation);
        toggle = button(content, R.string.enable_esim);
        toggle.setOnClickListener(view -> confirmSwitch());
        manage = button(content, R.string.manage_profiles);
        manage.setOnClickListener(view -> openManager());
        refresh = button(content, R.string.retry);
        refresh.setOnClickListener(view -> readState());
        setContentView(content);
        if (!getPackageManager().hasSystemFeature(PackageManager.FEATURE_TELEPHONY_EUICC)) {
            status.setText(R.string.unavailable);
            setBusy(true);
            return;
        }
        readState();
    }

    @Override public boolean onNavigateUp() { finish(); return true; }

    private Button button(LinearLayout parent, int text) {
        Button button = new Button(this);
        button.setText(text);
        button.setFilterTouchesWhenObscured(true);
        parent.addView(button, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        return button;
    }

    private void setBusy(boolean value) {
        busy = value;
        toggle.setEnabled(!value && (currentState == 0 || currentState == 1));
        manage.setEnabled(!value && currentState == 1);
        refresh.setEnabled(!value);
    }

    private void readState() {
        if (busy) return;
        setBusy(true);
        status.setText(R.string.checking);
        WORKER.execute(() -> {
            int state = -1;
            try {
                state = MtkEsimTransport.getInstance().readState();
                Log.i(TAG, "read_state=" + state);
            } catch (IOException failure) {
                // All top-level transport messages are fixed diagnostics, never modem payloads.
                Log.w(TAG, "read_failed=" + failure.getMessage());
            }
            final int result = state;
            runOnUiThread(() -> {
                if (isDestroyed()) return;
                showState(result);
            });
        });
    }

    private void showState(int state) {
        currentState = state;
        status.setText(state == 1 ? R.string.esim_selected
                : state == 0 ? R.string.physical_selected : R.string.read_error);
        toggle.setText(state == 1 ? R.string.disable_esim : R.string.enable_esim);
        setBusy(false);
    }

    private boolean callIsActive() {
        TelecomManager telecom = getSystemService(TelecomManager.class);
        return telecom == null || telecom.isInCall();
    }

    private void confirmSwitch() {
        if (busy || (currentState != 0 && currentState != 1)) return;
        if (callIsActive()) {
            Toast.makeText(this, R.string.call_active, Toast.LENGTH_LONG).show();
            return;
        }
        boolean enable = currentState == 0;
        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle(enable ? R.string.enable_esim : R.string.disable_esim)
                .setMessage(enable ? R.string.confirm_enable : R.string.confirm_disable)
                .setNegativeButton(android.R.string.cancel, null)
                .setPositiveButton(R.string.confirm_switch, (confirmation, which) -> switchState(enable))
                .create();
        dialog.setOnShowListener(shown -> dialog.getButton(AlertDialog.BUTTON_POSITIVE)
                .setFilterTouchesWhenObscured(true));
        dialog.show();
    }

    private void switchState(boolean enable) {
        if (busy) return;
        if (callIsActive()) {
            Toast.makeText(this, R.string.call_active, Toast.LENGTH_LONG).show();
            return;
        }
        setBusy(true);
        status.setText(R.string.busy);
        WORKER.execute(() -> {
            boolean success = false;
            int actualState = -1;
            try {
                MtkEsimTransport transport = MtkEsimTransport.getInstance();
                transport.select(enable);
                success = true;
                actualState = enable ? 1 : 0;
                Log.i(TAG, "switch_confirmed=" + actualState);
            } catch (IOException failure) {
                Log.w(TAG, "switch_failed=" + failure.getMessage());
                try {
                    actualState = MtkEsimTransport.getInstance().readState();
                } catch (IOException ignored) {
                    // Unknown state stays unknown; do not silently reverse a timed-out command.
                }
            }
            final boolean confirmed = success;
            final int state = actualState;
            runOnUiThread(() -> {
                if (isDestroyed()) return;
                showState(state);
                if (!confirmed) {
                    Toast.makeText(this, R.string.switch_error, Toast.LENGTH_LONG).show();
                }
            });
        });
    }

    private void openManager() {
        if (busy || currentState != 1) return;
        Intent intent = getPackageManager().getLaunchIntentForPackage(LPA_PACKAGE);
        try {
            if (intent == null) throw new ActivityNotFoundException();
            startActivity(intent);
        } catch (ActivityNotFoundException failure) {
            Toast.makeText(this, R.string.manager_missing, Toast.LENGTH_LONG).show();
        }
    }
}
