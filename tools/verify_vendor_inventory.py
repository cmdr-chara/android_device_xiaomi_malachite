#!/usr/bin/env python3
"""Check proprietary destination/fixup names against a collected vendor Git tree.

No extraction code is executed and no binary is modified or loaded. A PASS is
filename coverage only, not ELF dependency, provenance, or camera validation.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
from collect_source_evidence import safe_path


def destinations(text):
    result = []
    for number, line in enumerate(text.splitlines(), 1):
        line = line.partition('#')[0].strip()
        if not line:
            continue
        payload = line.removeprefix('-').split(';', 1)[0].split('|', 1)[0]
        paths = payload.split(':')
        if len(paths) not in (1, 2):
            raise ValueError(f'Invalid proprietary path pair on line {number}')
        for path in paths:
            safe_path(path)
        result.append(paths[-1])
    if not result:
        raise ValueError('Empty proprietary inventory')
    return result


def fixup_paths(source):
    result = set()
    found = False
    for node in ast.parse(source).body:
        if not isinstance(node, ast.AnnAssign) or not isinstance(node.target, ast.Name) or node.target.id != 'blob_fixups':
            continue
        found = True
        if not isinstance(node.value, ast.Dict):
            raise ValueError('Expected a literal blob_fixups dictionary')
        for key in node.value.keys:
            value = ast.literal_eval(key)
            paths = (value,) if isinstance(value, str) else value
            if not isinstance(paths, tuple) or not paths:
                raise ValueError('Expected literal string/tuple fixup keys')
            for path in paths:
                if not isinstance(path, str):
                    raise ValueError('Expected string fixup path')
                safe_path(path)
                result.add(path)
    if not found:
        raise ValueError('No supported blob_fixups declaration found')
    return result


def audit(proprietary, fixups, tree):
    available = set()
    for entry in tree:
        path = str(safe_path(entry['path']))
        if entry['type'] == 'blob':
            available.add(path)
    expected = destinations(proprietary)
    targets = fixup_paths(fixups)
    missing = sorted({p for p in expected if 'proprietary/' + p not in available})
    missing_fixups = sorted(p for p in targets if 'proprietary/' + p not in available)
    return {'schema_version': 1, 'status': 'FAIL' if missing or missing_fixups else 'PASS',
            'claim': 'Filename coverage only; extraction and ELF/runtime compatibility unverified',
            'proprietary_entries': len(expected), 'unique_destinations': len(set(expected)),
            'fixup_targets': len(targets), 'missing_destinations': missing,
            'missing_fixup_targets': missing_fixups, 'binary_compatibility': 'GAP'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device-root', type=Path, required=True)
    parser.add_argument('--vendor-tree', type=Path, required=True)
    args = parser.parse_args()
    files = [args.device_root / 'proprietary-files.txt', args.device_root / 'extract-files.py', args.vendor_tree]
    if any(p.is_symlink() or not p.is_file() for p in files):
        parser.error('Expected regular non-symlink input files')
    data = [p.read_bytes() for p in files]
    report = audit(data[0].decode(), data[1].decode(), json.loads(data[2]))
    report['input_sha256'] = {p.name: hashlib.sha256(content).hexdigest() for p, content in zip(files, data)}
    print(json.dumps(report, indent=2, sort_keys=True))
    return int(report['status'] != 'PASS')


if __name__ == '__main__':
    raise SystemExit(main())
