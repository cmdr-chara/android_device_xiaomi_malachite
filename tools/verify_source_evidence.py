#!/usr/bin/env python3
"""Verify a collected source snapshot without executing its code or touching devices.

Exit 1 means a failed integrity/structure check OR a detected inherited safety
blocker. PASS applies only to the named check; XML parsing is not checkvintf.
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from collect_source_evidence import load_lock, safe_path


def verify_payload(data: bytes, entry: dict) -> None:
    if len(data) != entry['bytes']:
        raise ValueError('Exported size differs')
    if hashlib.sha256(data).hexdigest() != entry['sha256']:
        raise ValueError('Exported SHA-256 differs')
    oid = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    if oid != entry['git_blob']:
        raise ValueError('Exported Git blob identity differs')


def module_membership(text: str, paths: set[str], directory: str) -> dict:
    names = [line.partition('#')[0].strip() for line in text.splitlines()]
    names = [name for name in names if name]
    for name in names:
        safe_path(name)
        if '/' in name or not name.endswith('.ko'):
            raise ValueError(f'Unexpected module load-list entry: {name}')
    return {'count': len(names), 'missing': [n for n in names if f'{directory}/{n}' not in paths],
            'duplicates': sorted(n for n, count in Counter(names).items() if count > 1)}


def audit(root: Path) -> dict:
    lock = load_lock(root / 'source-lock.json')
    checks = []
    def add(name, status, detail):
        checks.append({'check': name, 'status': status, 'detail': detail})
    verified, xmls, python_files = 0, 0, 0
    for project in lock['projects']:
        repo = root / project['repository'].split('/')[1]
        try:
            result = json.loads((repo / 'result.json').read_text())
            if result['revision'] != project['revision'] or result['repository'] != project['repository'] or result['status'] != 'PASS':
                raise ValueError('Collection identity/status mismatch')
            entries = json.loads((repo / 'exports.json').read_text())
            exported = 0
            for entry in entries:
                if 'sha256' not in entry:
                    continue
                safe_path(entry['path'])
                path = repo / 'files' / entry['path']
                if path.is_symlink() or not path.resolve().is_relative_to((repo / 'files').resolve()):
                    raise ValueError('Export escapes its repository')
                data = path.read_bytes()
                verify_payload(data, entry)
                if path.suffix == '.xml':
                    ET.fromstring(data)
                    xmls += 1
                if project['role'] == 'device' and path.suffix == '.py':
                    ast.parse(data, filename=entry['path'])
                    python_files += 1
                verified += 1
                exported += 1
            if exported != result['exported_files']:
                raise ValueError('Export inventory count differs')
            add(project['repository'], 'PASS', {'revision': project['revision'], 'exports': exported})
        except (OSError, ValueError, KeyError, ET.ParseError, SyntaxError) as error:
            add(project['repository'], 'FAIL', str(error))
    add('verified_export_totals', 'PASS' if all(c['status'] == 'PASS' for c in checks) else 'FAIL',
        {'files': verified, 'xml_well_formed': xmls, 'device_python_ast': python_files})
    try:
        repo = root / 'android_device_xiaomi_malachite-kernel'
        paths = {e['path'] for e in json.loads((repo / 'tree.json').read_text()) if e['type'] == 'blob'}
        for name, directory in {'system': 'system_dlkm', 'vendor': 'vendor_dlkm', 'vendor_ramdisk': 'vendor_ramdisk', 'recovery': 'vendor_ramdisk'}.items():
            result = module_membership((repo / 'files' / f'modules.load.{name}').read_text(), paths, directory)
            add(f'module_membership_{name}', 'FAIL' if result['missing'] else 'PASS', result)
    except (OSError, ValueError, KeyError) as error:
        add('module_membership', 'FAIL', str(error))
    try:
        device = root / 'android_device_xiaomi_malachite/files'
        board = (device / 'BoardConfig.mk').read_text().replace('\\\n', ' ')
        def value(name, default=None):
            found = re.findall(r'(?m)^' + re.escape(name) + r'\s*[:+?]?=\s*([^\n]+)', board)
            if not found:
                if default is not None:
                    return default
                raise ValueError(f'Missing board variable {name}')
            return ' '.join(s.partition('#')[0].strip() for s in found)
        fstab = {}
        for line in (device / 'init/fstab.mt6878').read_text().splitlines():
            fields = line.partition('#')[0].split()
            if fields:
                if len(fields) != 5:
                    raise ValueError('Malformed fstab row')
                if fields[0] in fstab:
                    raise ValueError('Duplicate fstab source')
                fstab[fields[0]] = fields
        partitions = value('BOARD_MEDIATEK_DYNAMIC_PARTITIONS_PARTITION_LIST').split()
        for partition in partitions:
            row = fstab[partition]
            if row[2] != value('BOARD_' + partition.upper() + 'IMAGE_FILE_SYSTEM_TYPE'):
                raise ValueError(f'Filesystem mismatch for {partition}')
            flags = set(row[4].split(','))
            if not {'logical', 'slotselect', 'first_stage_mount'} <= flags or not any(f == 'avb' or f.startswith('avb=') for f in flags):
                raise ValueError(f'Missing dynamic partition flags: {partition}')
        super_bytes = int(value('BOARD_SUPER_PARTITION_SIZE'))
        group_bytes = int(value('BOARD_MEDIATEK_DYNAMIC_PARTITIONS_SIZE'))
        if not 0 < group_bytes < super_bytes:
            raise ValueError('Dynamic group exceeds super capacity')
        add('partition_source_relationships', 'PASS', {'dynamic_partitions': partitions, 'super_bytes': super_bytes,
                                                      'group_bytes': group_bytes, 'unallocated_bytes': super_bytes - group_bytes})
        dangerous = []
        for partition in ('protect1', 'protect2', 'nvdata', 'nvcfg', 'persist'):
            if 'formattable' in fstab[f'/dev/block/by-name/{partition}'][4].split(','):
                dangerous.append(partition)
        add('persistent_autoformat_opt_in', 'FAIL' if dangerous else 'PASS',
            {'formattable_partitions': dangerous, 'scope': 'Not a guarantee against fsck or vendor-service writes'})
        args = value('BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS', '')
        flags = [int(f, 0) for f in re.findall(r'--flags\s+(0x[0-9a-fA-F]+|[0-9]+)', args)]
        add('avb_release_policy', 'FAIL' if any(f & 3 for f in flags) else 'GAP',
            {'make_vbmeta_args': args, 'scope': 'Signed image chain, rollback indices and keys still require validation'})
    except (OSError, ValueError, KeyError) as error:
        add('partition_configuration', 'FAIL', str(error))
    for name in ('android_build', 'merged_vintf_all_skus', 'compiled_selinux', 'blob_elf_and_fixups',
                 'generated_image_layout', 'kernel_prebuilt_artifact_equivalence', 'physical_device_tests'):
        add(name, 'GAP', 'Outside selected-text static evidence; use the build/device verification matrix')
    return {'scope': 'Pinned selected source text, not built images or hardware', 'checks': checks}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = audit(args.evidence)
    data = json.dumps(report, indent=2) + '\n'
    if args.output:
        if args.output.exists():
            parser.error('Output exists; evidence is never overwritten')
        args.output.write_text(data)
    print(data, end='')
    return int(any(c['status'] == 'FAIL' for c in report['checks']))


if __name__ == '__main__':
    raise SystemExit(main())
