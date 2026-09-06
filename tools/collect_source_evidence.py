#!/usr/bin/env python3
"""Collect bounded, read-only evidence for the twelve pinned public forks.

Requires Python 3.10+, Git and network access. Does not build or execute repository
code, check out a phone, or write to GitHub. Exports selected text, not a buildable
source checkout. Binary payloads and unselected sources remain explicit exclusions.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
from urllib.request import Request, urlopen

OWNER = "cmdr-chara"
EXPECTED_NAMES = {
    "android_device_xiaomi_malachite", "proprietary_vendor_xiaomi_malachite",
    "android_hardware_mediatek", "android_hardware_xiaomi",
    "android_device_mediatek_sepolicy_vndr", "android_vendor_mediatek_ims",
    "android_kernel_xiaomi_mt6878", "android_kernel_device_modules",
    "android_vendor_mediatek_kernel_modules", "kernel-build-bazel_mgk_rules",
    "kernel_manifest-6.1", "android_device_xiaomi_malachite-kernel",
}
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_REPO_BYTES = 64 * 1024 * 1024
TEXT_SUFFIXES = {
    ".bp", ".mk", ".bzl", ".bazel", ".xml", ".rc", ".prop", ".txt",
    ".md", ".json", ".yaml", ".yml", ".sh", ".py", ".cfg", ".conf",
    ".te", ".cil", ".h", ".hpp", ".c", ".cpp", ".cc", ".java",
    ".aidl", ".map", ".config", ".dts", ".dtsi", ".dtso", ".rules",
}
BINARY_SUFFIXES = {
    ".so", ".ko", ".apk", ".jar", ".dex", ".bin", ".img", ".lz4",
    ".gz", ".zip", ".png", ".jpg", ".jpeg", ".webp", ".ttf", ".otf",
}


def safe_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if (not path.parts or path.is_absolute() or ".." in path.parts
            or ".git" in path.parts or "\\" in value or ":" in value
            or value != path.as_posix()):
        raise ValueError(f"Unsafe source path: {value!r}")
    return path


def load_lock(path: Path) -> dict:
    lock = json.loads(path.read_text(encoding="utf-8"))
    projects = lock.get("projects", [])
    expected = {f"{OWNER}/{name}" for name in EXPECTED_NAMES}
    if lock.get("schema_version") != 1 or len(projects) != 12:
        raise ValueError("Expected a version-1 twelve-project lock")
    if {p.get("repository") for p in projects} != expected:
        raise ValueError("Lock must contain exactly the twelve authorized forks")
    for project in projects:
        if not re.fullmatch(r"[0-9a-f]{40}", project.get("revision", "")):
            raise ValueError(f"Unpinned revision: {project['repository']}")
        if project.get("path") is not None:
            safe_path(project["path"])
    return lock


def selected(role: str, value: str) -> bool:
    path = safe_path(value)
    name = path.name
    if name in {"AGENTS.md", "CODEOWNERS"}:
        return True
    if role == "kleaf" and name in {"BUILD.ko", "BUILD.internal", "bazel.WORKSPACE"}:
        return True
    if name.startswith("fstab.") or path.suffix in {".hal", ".kt"}:
        return True
    if path.suffix.lower() in BINARY_SUFFIXES:
        return False
    if role == "prebuilt":
        return name.startswith("modules.load.") or name.startswith("README")
    build_metadata = (
        name in {"Makefile", "Kbuild", "Kconfig", "BUILD", "BUILD.bazel", "WORKSPACE"}
        or name.startswith("build.config") or path.suffix in {".bzl", ".bazel"}
    )
    if role in {"kernel", "device-modules", "vendor-modules"}:
        if len(path.parts) == 1 or name.startswith("build.config"):
            return True
        if value.startswith("arch/arm64/configs/"):
            return True
        if role != "kernel" and build_metadata:
            return True
        if role == "kernel" and path.suffix in {".bzl", ".bazel"}:
            return True
        if any(key in value.lower() for key in ("malachite", "mt6878")):
            return path.suffix in TEXT_SUFFIXES or build_metadata
        return False
    if role == "vendor":
        return len(path.parts) == 1 or path.suffix in {
            ".bp", ".mk", ".xml", ".rc", ".prop", ".txt", ".cfg",
            ".conf", ".json", ".md", ".py", ".sh",
        }
    return len(path.parts) == 1 or path.suffix in TEXT_SUFFIXES or not path.suffix


def command(args: list[str], cwd: Path | None = None, timeout: int = 300) -> bytes:
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_CONFIG_NOSYSTEM="1")
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, timeout=timeout)
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace")[-2000:]
        raise RuntimeError(f"Command {args[0]!r} failed ({result.returncode}): {detail}")
    return result.stdout


def api(path: str):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "malachite-source-audit"}
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request("https://api.github.com/" + path, headers=headers)
    with urlopen(request, timeout=90) as response:
        return json.load(response)


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def collect(project: dict, output: Path) -> dict:
    repository = project["repository"]
    revision = project["revision"]
    destination = output / repository.split("/", 1)[1]
    destination.mkdir()
    metadata = api(f"repos/{repository}")
    if metadata.get("private") is not False:
        raise ValueError("Refusing to export a private repository into CI artifacts")
    write_json(destination / "repository.json", {
        key: metadata.get(key) for key in
        ("full_name", "default_branch", "fork", "archived", "pushed_at", "parent", "source")
    })
    write_json(destination / "branches.json", api(f"repos/{repository}/branches?per_page=100"))
    history = []
    pages, per_page = (10, 100) if project["role"] == "device" else (1, 30)
    for page in range(1, pages + 1):
        commits = api(f"repos/{repository}/commits?sha={revision}&per_page={per_page}&page={page}")
        history.extend({
            "sha": c["sha"], "parents": [p["sha"] for p in c["parents"]],
            "date": c["commit"]["committer"]["date"], "message": c["commit"]["message"],
            "url": c["html_url"],
        } for c in commits)
        if len(commits) < per_page:
            break
    write_json(destination / "history.json", history)
    total_bytes = 0
    exports = []
    with tempfile.TemporaryDirectory(prefix="malachite-audit-") as temporary:
        repo = Path(temporary) / "source"
        command(["git", "clone", "--quiet", "--no-checkout", "--depth=1", "--single-branch",
                 "--filter=blob:limit=256k", "--branch", project["branch"],
                 f"https://github.com/{repository}.git", str(repo)], timeout=600)
        head = command(["git", "rev-parse", "HEAD"], repo).decode().strip()
        if head != revision:
            command(["git", "fetch", "--quiet", "--depth=1", "origin", revision], repo)
        # Resolving the exact recorded object, never silently following a moved branch.
        actual = command(["git", "rev-parse", revision + "^{commit}"], repo).decode().strip()
        if actual != revision:
            raise ValueError("Candidate identity mismatch")
        entries = []
        for record in command(["git", "ls-tree", "-r", "-z", revision], repo).split(b"\0"):
            if not record:
                continue
            meta, raw_path = record.split(b"\t", 1)
            mode, kind, oid = meta.decode().split()
            value = raw_path.decode("utf-8")
            safe_path(value)
            entries.append({"path": value, "mode": mode, "type": kind, "oid": oid})
        write_json(destination / "tree.json", entries)
        for entry in entries:
            value = entry["path"]
            if entry["mode"] not in {"100644", "100755"} or not selected(project["role"], value):
                continue
            data = command(["git", "show", f"{revision}:{value}"], repo)
            record = {"path": value, "git_blob": entry["oid"], "bytes": len(data)}
            if len(data) > MAX_FILE_BYTES or total_bytes + len(data) > MAX_REPO_BYTES:
                record["excluded"] = "size limit"
            else:
                try:
                    text = data.decode("utf-8")
                    if "\0" in text:
                        raise ValueError("NUL in text")
                except (UnicodeDecodeError, ValueError):
                    record["excluded"] = "non-text payload"
                else:
                    target = destination / "files" / value
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
                    total_bytes += len(data)
                    record["sha256"] = hashlib.sha256(data).hexdigest()
            exports.append(record)
    write_json(destination / "exports.json", exports)
    result = {"repository": repository, "revision": revision, "status": "PASS",
              "claim": "bounded source evidence collection only", "tree_entries": len(entries),
              "exported_files": sum("sha256" in r for r in exports), "exported_bytes": total_bytes,
              "history_commits": len(history), "history_limit": pages * per_page}
    write_json(destination / "result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path,
                        default=Path(__file__).resolve().parents[1] / "bringup/source-lock.json")
    parser.add_argument("--output", type=Path, required=True, help="New or empty evidence directory")
    parser.add_argument("--jobs", type=int, choices=range(1, 5), default=3)
    args = parser.parse_args()
    lock = load_lock(args.lock)
    if args.output.exists() and any(args.output.iterdir()):
        parser.error("Output must be empty; existing evidence is never overwritten")
    args.output.mkdir(parents=True, exist_ok=True)
    write_json(args.output / "source-lock.json", lock)
    results = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(collect, p, args.output): p for p in lock["projects"]}
        for future in as_completed(futures):
            project = futures[future]
            try:
                result = future.result()
            except Exception as error:
                result = {"repository": project["repository"], "revision": project["revision"],
                          "status": "FAIL", "error": str(error)}
            results.append(result)
            print(f"{result['status']} {result['repository']}", flush=True)
    report = {"completed_at": datetime.now(timezone.utc).isoformat(),
              "scope": "Selected text and tree/history metadata, NOT a complete source checkout",
              "build": "GAP", "device_testing": "GAP",
              "results": sorted(results, key=lambda r: r["repository"])}
    write_json(args.output / "collection-report.json", report)
    return int(any(r["status"] != "PASS" for r in results))


if __name__ == "__main__":
    raise SystemExit(main())
