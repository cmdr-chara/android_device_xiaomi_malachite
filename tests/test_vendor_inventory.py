from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from verify_vendor_inventory import audit, destinations, fixup_paths


class VendorInventoryTests(unittest.TestCase):
    def test_flags_renames_pins_and_comments(self):
        self.assertEqual(destinations('# comment\n-vendor/a.so:vendor/b.so;MODULE=x|abc\nodm/c|deadbeef\n'), ['vendor/b.so', 'odm/c'])

    def test_invalid_paths_and_empty_inventory(self):
        for data in ('', '../a', '/vendor/a', 'vendor/a:', 'a:b:c', 'a\\b'):
            with self.subTest(data=data), self.assertRaises(ValueError): destinations(data)

    def test_literal_groups_merge_without_executing_values(self):
        source = "blob_fixups: object = {'vendor/a': execute_nothing(), ('vendor/a', 'odm/b'): fail()}"
        self.assertEqual(fixup_paths(source), {'vendor/a', 'odm/b'})

    def test_nonliteral_or_unsafe_keys_are_rejected(self):
        for source in ("blob_fixups: object = {compute(): None}", "blob_fixups: object = {'../bad': None}", "blob_fixups: object = {42: None}", 'pass'):
            with self.subTest(source=source), self.assertRaises((ValueError, TypeError)): fixup_paths(source)

    def test_missing_destinations_and_fixups_fail(self):
        report = audit('vendor/a', "blob_fixups: object = {'odm/b': None}", [])
        self.assertEqual(report['status'], 'FAIL')
        self.assertEqual(report['missing_destinations'], ['vendor/a'])
        self.assertEqual(report['missing_fixup_targets'], ['odm/b'])

    def test_full_name_coverage_is_not_binary_validation(self):
        report = audit('vendor/a', "blob_fixups: object = {'vendor/a': None}", [{'path': 'proprietary/vendor/a', 'type': 'blob'}])
        self.assertEqual(report['status'], 'PASS')
        self.assertEqual(report['binary_compatibility'], 'GAP')


if __name__ == '__main__': unittest.main()
