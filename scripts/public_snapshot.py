"""Write a reviewed snapshot of committed HEAD into a clone of the public repository.

Only committed content is copied, never working copies. Files under public/
replace their counterparts (README, notebook map, CI workflow, notebook 00).
Held-back material (notebooks not yet reviewed, paper, talk, sub-PAT16
matrices, Cursor rules, the manuscript plan and the internal release checklist)
is left out, and Makefile targets that need it are dropped. Before anything is
written, the snapshot is checked for local paths, data files and oversized
files; relative links that point outside the snapshot are reported.
Nothing is committed or pushed in the destination.
"""

import argparse
import fnmatch
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED_NOTEBOOKS = ("00", "01", "02", "03", "04", "05", "06", "07", "08", "09")
HELD_BACK = (
    "public/*",
    "paper/*",
    "talk/*",
    "data/derived/*",
    ".cursor/*",
    "AGENTS.md",
    "docs/perspective-plan.md",
    "docs/public-release.md",
    "docs/notebook-review-checklist.md",
    "scripts/colab_bundle.py",
    "scripts/derive_pat16_connectome.py",
    "scripts/export_talk_pptx.mjs",
    "scripts/import_talk_artwork.py",
    "scripts/prepare_talk_export.py",
)
DROPPED_TARGETS = ("paper", "talk", "talk-pptx", "talk-artwork", "colab-bundle", "pat16-connectome")
LOCAL_PATH = re.compile(r"/Users/[A-Za-z]|/home/[a-z]|/var/folders/|[A-Za-z]:\\\\Users")
# Detector patterns and fabricated test paths, not local paths.
ALLOWED_MATCHES = {
    ("scripts/export_executed_notebooks.py", "/var/folders/"),
    ("scripts/public_snapshot.py", "/var/folders/"),
    ("scripts/public_snapshot.py", "/Users/s"),
    ("scripts/public_snapshot.py", "/Users/x"),
    ("tests/test_export_notebooks.py", "/Users/s"),
    ("tests/test_lumiere_bundle.py", "/Users/x"),
    ("tests/test_hpgs_bundle.py", "/Users/x"),
}
DATA_SUFFIXES = (".nii", ".nii.gz", ".npz", ".npy", ".mat", ".dcm", ".zip", ".tck", ".h5")
MAX_BYTES = 6 * 1024 * 1024
LINK = re.compile(r"\]\(([^)\s#]+)(?:#[^)]*)?\)")


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout


def blob(revision: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{revision}:{path}"], cwd=ROOT, capture_output=True, check=True
    ).stdout


def selected(path: str) -> bool:
    if any(fnmatch.fnmatch(path, pattern) for pattern in HELD_BACK):
        return False
    name = Path(path).name
    if path.startswith("notebooks/") and name.endswith(".ipynb"):
        return name[:2] in PUBLISHED_NOTEBOOKS
    return True


def public_makefile(text: str) -> str:
    """Drop held-back targets with their comments, and the authoring-runtime variables."""
    blocks, kept = re.split(r"\n\n+", text.strip("\n")), []
    for block in blocks:
        target = re.search(r"^([A-Za-z][\w-]*):", block, re.M)
        if target and target.group(1) in DROPPED_TARGETS:
            continue
        if block.startswith("UV ?="):
            block = "\n".join(
                line
                for line in block.splitlines()
                if not re.match(r"(CODEX|PPTX|LATEXMK|ifneq|endif|export PATH)", line.strip())
            )
        if block.startswith(".PHONY:"):
            names = [n for n in block.split()[1:] if n not in DROPPED_TARGETS]
            block = ".PHONY: " + " ".join(names)
        kept.append(block.replace(" --paper-dir paper/generated", ""))
    return "\n\n".join(kept) + "\n"


def build(revision: str) -> dict[str, bytes]:
    files = {
        path: blob(revision, path)
        for path in git("ls-tree", "-r", "--name-only", revision).splitlines()
        if selected(path)
    }
    for path in git("ls-tree", "-r", "--name-only", revision, "public").splitlines():
        files[path.removeprefix("public/")] = blob(revision, path)
    files["Makefile"] = public_makefile(files["Makefile"].decode()).encode()
    return files


def problems(files: dict[str, bytes]) -> list[str]:
    found = []
    for path, content in files.items():
        if path.endswith(DATA_SUFFIXES):
            found.append(f"data file: {path}")
        if len(content) > MAX_BYTES:
            found.append(f"larger than {MAX_BYTES} bytes: {path}")
        text = content.decode("utf-8", errors="ignore")
        for match in sorted(set(LOCAL_PATH.findall(text))):
            if (path, match) not in ALLOWED_MATCHES:
                found.append(f"local path {match!r}: {path}")
    return found


def broken_links(files: dict[str, bytes]) -> list[str]:
    paths = set(files) | {os.path.dirname(p) for p in files}
    broken = []
    for path, content in files.items():
        if not path.endswith((".md", ".ipynb")):
            continue
        for target in LINK.findall(content.decode("utf-8", errors="ignore")):
            if "://" in target or target.startswith("mailto:"):
                continue
            resolved = os.path.normpath(os.path.join(os.path.dirname(path), target))
            if resolved not in paths:
                broken.append(f"{path} -> {target}")
    return sorted(set(broken))


def write(files: dict[str, bytes], destination: Path) -> None:
    if not (destination / ".git").is_dir():
        sys.exit(f"{destination} is not a Git clone.")
    for item in destination.iterdir():
        if item.name == ".git":
            continue
        shutil.rmtree(item) if item.is_dir() and not item.is_symlink() else item.unlink()
    for path, content in files.items():
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="clone of the public repository")
    parser.add_argument("--revision", default="HEAD")
    arguments = parser.parse_args()
    revision = git("rev-parse", arguments.revision).strip()
    files = build(revision)
    found = problems(files)
    if found:
        sys.exit("Snapshot refused:\n  " + "\n  ".join(found))
    write(files, arguments.destination.resolve())
    links = broken_links(files)
    print(f"Wrote {len(files)} files from {revision[:12]} to {arguments.destination}")
    print(f"Relative links outside the snapshot: {len(links)}")
    for link in links:
        print("  " + link)


if __name__ == "__main__":
    main()
