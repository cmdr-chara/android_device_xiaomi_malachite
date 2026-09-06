"""Offline regressions for source integrity and module-list verification."""
import hashlib
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from verify_source_evidence import module_membership, verify_payload


class EvidenceVerificationTests(unittest.TestCase):
    def setUp(self):
        self.data = b'verified source\n'
        self.entry = {'bytes': len(self.data), 'sha256': hashlib.sha256(self.data).hexdigest(),
                      'git_blob': hashlib.sha1(b'blob ' + str(len(self.data)).encode() + b'\0' + self.data).hexdigest()}

    def test_exact_payload(self):
        verify_payload(self.data, self.entry)

    def test_tampered_content_rejected(self):
        with self.assertRaises(ValueError):
            verify_payload(b'Verified source\n', self.entry)

    def test_wrong_size_rejected(self):
        with self.assertRaises(ValueError):
            verify_payload(self.data + b'x', self.entry)

    def test_wrong_git_identity_rejected(self):
        self.entry['git_blob'] = '0' * 40
        with self.assertRaises(ValueError):
            verify_payload(self.data, self.entry)

    def test_missing_and_duplicate_modules_remain_visible(self):
        result = module_membership('a.ko\na.ko\nb.ko\n# comment\n', {'vendor_dlkm/a.ko'}, 'vendor_dlkm')
        self.assertEqual(result, {'count': 3, 'missing': ['b.ko'], 'duplicates': ['a.ko']})

    def test_unsafe_or_non_module_entries_rejected(self):
        for name in ('../x.ko', '/x.ko', 'a/x.ko', 'x.txt'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                module_membership(name, set(), 'vendor_dlkm')


if __name__ == '__main__':
    unittest.main()
