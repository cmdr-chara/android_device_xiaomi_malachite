#!/usr/bin/env python3
"""Validate the build-review lock; optionally inspect public GitHub refs (GET only)."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
from urllib.parse import quote
from collect_source_evidence import api, load_lock
from workspace_manifest import render

ROOT = Path(__file__).resolve().parents[1]


def validate(baseline, candidate, manifest):
    if candidate.get('purpose') != 'build-review-only':
        raise ValueError('Candidate must not claim deployment readiness')
    old = {p['repository']: p for p in baseline['projects']}
    new = {p['repository']: p for p in candidate['projects']}
    if len(candidate['projects']) != 12 or new.keys() != old.keys():
        raise ValueError('Expected exactly the baseline twelve repositories')
    for name, project in new.items():
        original = old[name]
        if any(project.get(k) != original.get(k) for k in ('path', 'workspace', 'role')):
            raise ValueError('Candidate changes a repository identity or checkout boundary')
        if not re.fullmatch(r'[0-9a-f]{40}', project.get('revision', '')):
            raise ValueError('Candidate revision is not immutable')
        if not isinstance(project.get('branch'), str) or not project['branch']:
            raise ValueError('Missing branch provenance')
        if project['role'] in {'vendor', 'prebuilt', 'sepolicy', 'vendor-modules'} and project['revision'] != original['revision']:
            raise ValueError('Unreviewed binary/policy/vendor-module baseline change')
    if manifest != render(candidate):
        raise ValueError('Android candidate manifest differs from its source lock')


def inspect_project(project):
    repository = project['repository']
    result = {'repository': repository, 'revision': project['revision'], 'status': 'GAP'}
    try:
        commit = api(f"repos/{repository}/git/commits/{project['revision']}")
        if commit.get('sha') != project['revision']:
            raise ValueError('GitHub returned a different commit identity')
        result['tree'] = commit['tree']['sha']
        branch = quote(project['branch'], safe='')
        result['branch_head'] = api(f'repos/{repository}/git/ref/heads/{branch}')['object']['sha']
        result['baseline_head'] = api(f'repos/{repository}/git/ref/heads/lineage-23.2')['object']['sha']
        pulls = api(f'repos/{repository}/pulls?state=open&per_page=100')
        if len(pulls) == 100:
            raise ValueError('PR inventory requires pagination; refusing an incomplete count')
        result['open_pull_requests'] = [
            {'number': p['number'], 'title': p['title'], 'draft': p['draft'],
             'head': p['head']['ref'], 'head_sha': p['head']['sha'], 'url': p['html_url']}
            for p in pulls]
        result['status'] = 'PASS'
    except Exception as error:
        result['error'] = f'{type(error).__name__}: {error}'
        result['status'] = 'FAIL'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--online', action='store_true')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    baseline = load_lock(ROOT / 'bringup/source-lock.json')
    candidate = load_lock(ROOT / 'bringup/candidates/2026-09-06.json')
    validate(baseline, candidate, (ROOT / 'bringup/candidates/2026-09-06.xml').read_text())
    report = {'schema_version': 1, 'offline_contracts': 'PASS', 'release_status': 'BLOCKED',
              'claim': 'Source identity checks, not build or hardware certification'}
    if args.online:
        with ThreadPoolExecutor(max_workers=4) as pool:
            report['projects'] = list(pool.map(inspect_project, candidate['projects']))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return int(any(p['status'] != 'PASS' for p in report.get('projects', [])))


if __name__ == '__main__':
    raise SystemExit(main())
