import copy
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from collect_source_evidence import load_lock
from verify_candidate import validate
from workspace_manifest import render


class CandidateContracts(unittest.TestCase):
    def setUp(self):
        self.base = load_lock(ROOT / 'bringup/source-lock.json')
        self.candidate = load_lock(ROOT / 'bringup/candidates/2026-09-06.json')
        self.manifest = (ROOT / 'bringup/candidates/2026-09-06.xml').read_text()

    def test_candidate_matches_its_manifest(self):
        validate(self.base, self.candidate, self.manifest)

    def test_rejects_moving_revision(self):
        self.candidate['projects'][0]['revision'] = 'lineage-23.2'
        with self.assertRaises(ValueError): validate(self.base, self.candidate, render(self.candidate))

    def test_rejects_changed_boundary(self):
        self.candidate['projects'][0]['path'] = 'device/other'
        with self.assertRaises(ValueError): validate(self.base, self.candidate, render(self.candidate))

    def test_rejects_unreviewed_binary_or_policy_change(self):
        for role in ('vendor', 'prebuilt', 'sepolicy', 'vendor-modules'):
            candidate = copy.deepcopy(self.candidate)
            next(p for p in candidate['projects'] if p['role'] == role)['revision'] = 'a' * 40
            with self.subTest(role=role), self.assertRaises(ValueError):
                validate(self.base, candidate, render(candidate))

    def test_rejects_missing_repo_and_false_promotion(self):
        self.candidate['projects'].pop()
        with self.assertRaises(ValueError): validate(self.base, self.candidate, self.manifest)
        self.candidate = load_lock(ROOT / 'bringup/candidates/2026-09-06.json')
        self.candidate['purpose'] = 'flash-ready'
        with self.assertRaises(ValueError): validate(self.base, self.candidate, self.manifest)

    def test_rejects_stale_manifest(self):
        with self.assertRaises(ValueError): validate(self.base, self.candidate, render(self.base))


if __name__ == '__main__': unittest.main()
