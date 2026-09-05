"""Offline documentation contracts; external links are not network-validated."""
import json
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class BringupDocsTests(unittest.TestCase):
    def test_required_operating_documents_exist(self):
        for name in ('README.md', 'ARCHITECTURE.md', 'HISTORY.md', 'SAFETY.md', 'VERIFICATION.md'):
            with self.subTest(name=name):
                self.assertTrue((ROOT / 'bringup' / name).is_file())

    def test_architecture_covers_all_owned_repositories(self):
        lock = json.loads((ROOT / 'bringup/source-lock.json').read_text())
        architecture = (ROOT / 'bringup/ARCHITECTURE.md').read_text()
        for project in lock['projects']:
            with self.subTest(repository=project['repository']):
                self.assertIn(project['repository'].split('/', 1)[1], architecture)

    def test_relative_markdown_targets_exist_inside_repository(self):
        for document in (ROOT / 'bringup').glob('*.md'):
            for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)', document.read_text()):
                target = urlsplit(link)
                if target.scheme or target.netloc or not target.path:
                    continue
                path = (document.parent / unquote(target.path)).resolve()
                with self.subTest(document=document.name, link=link):
                    self.assertTrue(path.is_relative_to(ROOT.resolve()))
                    self.assertTrue(path.exists())


if __name__ == '__main__':
    unittest.main()
