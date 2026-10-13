"""Record source and environment hashes without collecting credentials."""

import hashlib
import json
import platform
import subprocess
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def environment_record() -> dict:
    root = Path(__file__).resolve().parents[2]
    packages = {}
    for name in ("ai-assisted-glioma-research", "numpy", "matplotlib", "nibabel", "torch"):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
        dirty = bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=root, text=True, stderr=subprocess.DEVNULL
            ).strip()
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        commit, dirty = None, None
    bundle_revision = root / ".source-revision.json"
    exported_commit = (
        json.loads(bundle_revision.read_text()).get("commit") if bundle_revision.is_file() else None
    )
    files = list(Path(__file__).parent.glob("*.py"))
    files.extend((Path(__file__).parent / "references").glob("*.json"))
    files.extend(root / name for name in ("pyproject.toml", "uv.lock"))
    return {
        "created_utc": datetime.now(UTC).isoformat(),
        "python": platform.python_version(),
        "platform": platform.system(),
        "machine": platform.machine(),
        "packages": packages,
        "git": {"commit": commit, "dirty": dirty},
        "source_revision_from_bundle": exported_commit,
        "source_sha256": {
            str(path.relative_to(root)): sha256(path) for path in files if path.is_file()
        },
    }
