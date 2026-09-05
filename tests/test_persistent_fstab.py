"""Guard fs_mgr automatic-format policy, not all possible partition writes."""
import os
from pathlib import Path
import unittest
ROOT = Path(os.environ.get('MALACHITE_DEVICE_ROOT', Path(__file__).resolve().parents[1]))


def entries():
    rows = {}
    for line in (ROOT / 'init/fstab.mt6878').read_text().splitlines():
        line = line.partition('#')[0].strip()
        if not line:
            continue
        fields = line.split()
        if len(fields) != 5:
            raise ValueError(f'Malformed fstab entry: {line}')
        if fields[0] in rows:
            raise ValueError(f'Duplicate fstab source: {fields[0]}')
        rows[fields[0]] = fields
    return rows


class PersistentFstabTests(unittest.TestCase):
    def test_persistent_partitions_never_opt_into_autoformat(self):
        rows = entries()
        for partition in ('protect1', 'protect2', 'nvdata', 'nvcfg', 'persist'):
            with self.subTest(partition=partition):
                row = rows[f'/dev/block/by-name/{partition}']
                self.assertEqual(row[2], 'ext4')
                self.assertEqual(set(row[4].split(',')), {'wait', 'check'})

    def test_data_and_metadata_format_policy_unchanged(self):
        rows = entries()
        for partition in ('userdata', 'metadata'):
            with self.subTest(partition=partition):
                self.assertIn('formattable', rows[f'/dev/block/by-name/{partition}'][4].split(','))

    def test_dynamic_partitions_keep_slot_avb_and_first_stage(self):
        rows = entries()
        for partition in ('system', 'system_ext', 'product', 'vendor', 'odm', 'vendor_dlkm', 'odm_dlkm', 'system_dlkm'):
            with self.subTest(partition=partition):
                flags = set(rows[partition][4].split(','))
                self.assertTrue({'logical', 'slotselect', 'first_stage_mount'} <= flags)
                self.assertTrue(any(f == 'avb' or f.startswith('avb=') for f in flags))


if __name__ == '__main__':
    unittest.main()
