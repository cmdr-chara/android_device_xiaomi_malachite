// SPDX-License-Identifier: Apache-2.0
package org.lineageos.malachite.esim;

import java.io.IOException;

/** Exercises response frames, including the stock comma separator and invalid frames. */
public final class EsimStatusTest {
    public static void main(String[] args) throws Exception {
        expect(0, "0");
        expect(1, "1");
        expect(0, "0,ignored");
        expect(1, " 1 ,ignored,tail");
        for (int value : new int[] {-3, -2, -1, 2, 3, 4, 5}) {
            expect(value, Integer.toString(value));
        }
        reject(null);
        reject(new String[0]);
        reject(new String[] {null});
        reject(new String[] {"0", "1"});
        for (String value : new String[] {"", " ", ",0", "1;ignored", "OK", "+1",
                "1x", "2147483648", "-", "0\n1"}) {
            reject(new String[] {value});
        }
        System.out.println("PASS: MIPC state/status response frames");
    }

    private static void expect(int expected, String frame) throws IOException {
        if (EsimStatus.parse(new String[] {frame}) != expected) {
            throw new AssertionError("Unexpected status");
        }
    }

    private static void reject(String[] frame) {
        try {
            EsimStatus.parse(frame);
            throw new AssertionError("Malformed frame accepted");
        } catch (IOException expected) {
            // A malformed response must not become a successful switch result.
        }
    }
}
