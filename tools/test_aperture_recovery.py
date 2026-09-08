#!/usr/bin/env python3
"""Execute the actual binding predicate and recovery policy with Kotlin/JVM, not a phone."""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def run(root: Path) -> None:
    package = root / 'app/src/main/java/org/lineageos/aperture'
    activity = (package / 'CameraActivity.kt').read_text()
    match = re.search(r'require\(\n(.*?)\n                \) \{\n'
                      r'                    "Video frame rate not supported with the requested video quality"',
                      activity, re.S)
    if not match:
        raise ValueError('Cannot locate the real frame-rate binding predicate')
    # Select the final require block, not an earlier multi-line require.
    condition = match.group(1).rsplit('require(\n', 1)[-1]
    policy = package / 'models/VideoRecoveryPolicy.kt'
    tests = '''
    for (requested in listOf<Int?>(null, 24, 30, 60)) {
        val cameraConfiguration = Configuration(requested)
        val videoQualityInfo = QualityInfo(setOf(24, 30, 60))
        check(CONDITION) { "Binding rejects supported rate/AUTO: $requested" }
    }
    val cameraConfiguration = Configuration(120)
    val videoQualityInfo = QualityInfo(setOf(24, 30, 60))
    check(!(CONDITION)) { "Binding accepts an unsupported fixed rate" }
'''.replace('CONDITION', condition)
    if policy.is_file():
        tests += '''
    check(VideoRecoveryPolicy.frameRate<Int>(null, setOf(24, 30, 60)) == null)
    check(VideoRecoveryPolicy.frameRate(60, setOf(24, 30, 60)) == 60)
    check(VideoRecoveryPolicy.frameRate(120, setOf(24, 30, 60)) == null)
    check(VideoRecoveryPolicy.frameRate(30, emptySet()) == null)
    check(VideoRecoveryPolicy.fallbackQuality("uhd", linkedSetOf("fhd", "uhd")) == "uhd")
    check(VideoRecoveryPolicy.fallbackQuality("uhd", linkedSetOf("fhd", "hd")) == "fhd")
    check(VideoRecoveryPolicy.fallbackQuality("uhd", emptySet()) == null)
    for (hdr in listOf(false, true)) for (idle in listOf(false, true)) {
        for (current in listOf(false, true)) {
            check(VideoRecoveryPolicy.canRecover(hdr, idle, current) == (hdr && idle && current))
        }
    }
'''
    kotlin = shutil.which('kotlinc')
    if not kotlin:
        raise RuntimeError('kotlinc is required; this check must not silently skip')
    with tempfile.TemporaryDirectory() as temp:
        tmp = Path(temp)
        source = tmp / 'Regression.kt'
        source.write_text('package org.lineageos.aperture.models\n'
                          'data class Configuration(val videoFrameRate: Int?)\n'
                          'data class QualityInfo(val supportedFrameRates: Set<Int>)\n'
                          'fun main() {\n' + tests + '\nprintln("PASS: binding and recovery policy")\n}\n')
        sources = [str(source)] + ([str(policy)] if policy.is_file() else [])
        subprocess.run([kotlin, *sources, '-include-runtime', '-d', str(tmp / 'test.jar')],
                       check=True, timeout=120)
        subprocess.run(['java', '-jar', str(tmp / 'test.jar')], check=True, timeout=30)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--aperture-root', required=True, type=Path)
    run(parser.parse_args().aperture_root)
