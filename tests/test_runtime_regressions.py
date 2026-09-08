"""Offline integrity tests for the source-only camera recovery bundle."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / 'bringup/runtime-regressions'
SPEC = importlib.util.spec_from_file_location('apply_recovery', ROOT / 'tools/apply_aperture_recovery.py')
apply_recovery = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(apply_recovery)


class RecoveryBundle(unittest.TestCase):
    def test_patch_digest_and_scope(self):
        manifest = json.loads((BUNDLE / 'aperture-patch.json').read_text())
        data = (BUNDLE / 'aperture-hdr-recovery.patch').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), manifest['patch_sha256'])
        changed = {line.split(' b/', 1)[1] for line in data.decode().splitlines()
                   if line.startswith('diff --git ')}
        self.assertEqual(changed, {f['path'] for f in manifest['files']})
        self.assertEqual(len(changed), 5)
        self.assertNotIn('clearApplicationUserData', data.decode())
        self.assertNotIn('editor.clear()', data.decode())
        self.assertNotIn('config_enableHdrVideo', data.decode())

    def test_refuses_wrong_revision_without_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(['git', 'init', '-q', td], check=True)
            (root / 'sentinel').write_text('keep me')
            subprocess.run(['git', '-C', td, 'add', '.'], check=True)
            subprocess.run(['git', '-C', td, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                            'commit', '-qm', 'fixture'], check=True)
            with self.assertRaisesRegex(ValueError, 'reviewed revision'):
                apply_recovery.apply(root, True)
            self.assertEqual((root / 'sentinel').read_text(), 'keep me')
            self.assertEqual(subprocess.check_output(['git', '-C', td, 'status', '--porcelain']), b'')

    def test_refuses_patch_tampering(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'aperture-patch.json').write_text((BUNDLE / 'aperture-patch.json').read_text())
            (root / 'aperture-hdr-recovery.patch').write_text('tampered')
            with patch.object(apply_recovery, 'BUNDLE', root):
                with self.assertRaisesRegex(ValueError, 'Patch digest mismatch'):
                    apply_recovery.apply(root, True)

    def test_refuses_symlink_input(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'original').write_text('original')
            (root / 'link').symlink_to(root / 'original')
            with self.assertRaisesRegex(ValueError, 'symlink'):
                apply_recovery.digest(root / 'link')

    def test_baseline_runtime_configuration_unchanged(self):
        expected = {
            'device.mk': '74a2e421f63fb4ee3720e59e2a749844f31e96f7',
            'manifest.xml': 'c676723715ca6993637592a93e35f90aba353b69',
            'BoardConfig.mk': '004c1e917762e9fad2e76e1c05b528bda1311654',
        }
        for name, oid in expected.items():
            data = (ROOT / name).read_bytes()
            self.assertEqual(hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest(), oid)


if __name__ == '__main__':
    unittest.main()
