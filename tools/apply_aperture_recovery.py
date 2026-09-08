#!/usr/bin/env python3
"""Check/apply the pinned Aperture patch to a clean host source checkout; no device I/O."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / 'bringup/runtime-regressions'


def digest(path):
    if path.is_symlink():
        raise ValueError(f'Refusing symlink: {path}')
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def apply(root: Path, write: bool = False) -> str:
    root = root.resolve(strict=True)
    manifest = json.loads((BUNDLE / 'aperture-patch.json').read_text())
    patch = BUNDLE / 'aperture-hdr-recovery.patch'
    if digest(patch) != manifest['patch_sha256']:
        raise ValueError('Patch digest mismatch')
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.STDOUT,
                                       timeout=30).decode().strip()
    if Path(git('rev-parse', '--show-toplevel')).resolve() != root:
        raise ValueError('Specify the Aperture repository root, not a subdirectory')
    if git('rev-parse', 'HEAD') != manifest['revision']:
        raise ValueError('Aperture HEAD does not match the reviewed revision')
    for f in manifest['files']:
        p = Path(f['path'])
        if p.is_absolute() or '..' in p.parts or not (root / p).resolve().is_relative_to(root):
            raise ValueError('Unsafe patch input path')
    actual = [digest(root / f['path']) for f in manifest['files']]
    if actual == [f['after_sha256'] for f in manifest['files']]:
        return 'Already applied; all patched file digests match'
    if git('status', '--porcelain', '--untracked-files=all'):
        raise ValueError('Refusing to modify a dirty checkout')
    if actual != [f['before_sha256'] for f in manifest['files']]:
        raise ValueError('Source file digest mismatch')
    git('apply', '--check', '--whitespace=error', str(patch))
    if not write:
        return 'PASS: patch applies to the exact clean source; no files changed'
    git('apply', '--whitespace=error', str(patch))
    if [digest(root / f['path']) for f in manifest['files']] != [
            f['after_sha256'] for f in manifest['files']]:
        raise ValueError('Post-apply digest mismatch; inspect the checkout without resetting it')
    return 'PASS: patch applied and all output digests verified'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--aperture-root', required=True, type=Path)
    parser.add_argument('--apply', action='store_true', help='Write after all preflight checks pass')
    args = parser.parse_args()
    try:
        print(apply(args.aperture_root, args.apply))
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        parser.exit(1, f'FAIL: {error}\n')
