"""Explicit, pinned partial download of LUMIERE Patient-048 from the Figshare archive.

The LUMIERE imaging release is one 32.6 GB ZIP. Its server accepts HTTP range
requests, so the central directory and the selected members can be read without
downloading the rest. Only the 36 files that the companion segmentation
repository stages for Patient-048 (four MRI sequences and two released tumour
segmentations at six visits) are pinned here by size, CRC-32 and SHA-256.
Nothing is registered, segmented or converted; files are written unchanged into
an ignored local directory. Use is subject to the dataset authors'
non-commercial condition.
"""

import hashlib
import io
import json
import time
import urllib.error
import urllib.request
import zipfile
from collections.abc import Callable
from pathlib import Path

from glioma_ai.provenance import sha256

REFERENCE = Path(__file__).parent / "references/lumiere_imaging_p048.json"
STAGED_SUFFIXES = (
    "T1.nii.gz",
    "CT1.nii.gz",
    "T2.nii.gz",
    "FLAIR.nii.gz",
    "HD-GLIO-AUTO-segmentation/registered/segmentation.nii.gz",
    "DeepBraTumIA-segmentation/native/segmentation/ct1_seg_mask.nii.gz",
)
RangeReader = Callable[[int, int], bytes]


def imaging_reference() -> dict:
    return json.loads(REFERENCE.read_text())


def http_range_reader(url: str, *, attempts: int = 3, timeout: float = 60) -> RangeReader:
    """Return ``read(start, stop)`` for bytes [start, stop) of ``url``.

    Each request follows the download redirect again, because Figshare's signed
    storage URL expires after seconds.
    """

    def read(start: int, stop: int) -> bytes:
        request = urllib.request.Request(url, headers={"Range": f"bytes={start}-{stop - 1}"})
        for attempt in range(attempts):
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    if response.status != 206:
                        raise ValueError("The server ignored the byte range; nothing written.")
                    data = response.read()
                if len(data) != stop - start:
                    raise ValueError("Short range response.")
                return data
            except (urllib.error.URLError, TimeoutError):
                if attempt == attempts - 1:
                    raise
                time.sleep(2**attempt)
        raise AssertionError("unreachable")

    return read


class RangeFile(io.RawIOBase):
    """Seekable read-only view of a remote file through a range reader."""

    def __init__(self, read: RangeReader, size: int):
        self._read, self.size, self.position, self.requests = read, int(size), 0, 0

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.position

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        base = {io.SEEK_SET: 0, io.SEEK_CUR: self.position, io.SEEK_END: self.size}[whence]
        self.position = base + offset
        return self.position

    def readinto(self, buffer) -> int:
        if self.position >= self.size:
            return 0
        stop = min(self.position + len(buffer), self.size)
        data = self._read(self.position, stop)
        self.requests += 1
        buffer[: len(data)] = data
        self.position += len(data)
        return len(data)


def open_archive(read: RangeReader, size: int) -> zipfile.ZipFile:
    return zipfile.ZipFile(io.BufferedReader(RangeFile(read, size), buffer_size=4 << 20))


def staged_member_names(archive: zipfile.ZipFile, patient: str = "Patient-048") -> list[str]:
    """The archive members that the companion staging script copies for ``patient``."""
    prefix = f"Imaging/{patient}/"
    names = []
    for info in archive.infolist():
        if info.is_dir() or not info.filename.startswith(prefix):
            continue
        week, _, rest = info.filename[len(prefix) :].partition("/")
        if week.startswith("week-") and rest in STAGED_SUFFIXES:
            names.append(info.filename)
    return sorted(names)


def pin_members(archive: zipfile.ZipFile, names: list[str]) -> dict:
    """Size, CRC-32 and SHA-256 of each member, read through the archive."""
    pins = {}
    for name in names:
        info = archive.getinfo(name)
        digest = hashlib.sha256(archive.read(name)).hexdigest()
        pins[name] = {"size": info.file_size, "crc32": f"{info.CRC:08x}", "sha256": digest}
    return pins


def _target(directory: Path, name: str) -> Path:
    relative = Path(name).relative_to("Imaging")
    if ".." in relative.parts:
        raise ValueError(f"Unsafe archive member name: {name}")
    return Path(directory) / relative


def verify_patient(directory: Path, reference: dict | None = None) -> dict:
    """Check every pinned member under ``directory``; return their SHA-256."""
    reference = reference or imaging_reference()
    hashes = {}
    for name, pin in reference["members"].items():
        path = _target(directory, name)
        intact = path.is_file() and path.stat().st_size == pin["size"]
        if not intact or sha256(path) != pin["sha256"]:
            raise ValueError(f"Missing or changed pinned LUMIERE file: {name}.")
        hashes[str(Path(name).relative_to("Imaging"))] = pin["sha256"]
    return hashes


def fetch_patient(
    directory: Path,
    *,
    reference: dict | None = None,
    read: RangeReader | None = None,
) -> dict:
    """Download the pinned members into ``directory`` (archive layout, without ``Imaging/``).

    Existing files are kept only if they match their pin. Every member is
    checked by size, by the ZIP's CRC-32 and by SHA-256 before it is written.
    """
    reference = reference or imaging_reference()
    archive_spec = reference["archive"]
    read = read or http_range_reader(archive_spec["download_url"])
    directory = Path(directory)
    pending = {}
    for name, pin in reference["members"].items():
        path = _target(directory, name)
        if path.is_file():
            if sha256(path) != pin["sha256"]:
                raise ValueError(f"Existing {path} differs from the pinned release; preserve it.")
            continue
        pending[name] = pin
    requests = 0
    if pending:
        raw = RangeFile(read, archive_spec["size"])
        with zipfile.ZipFile(io.BufferedReader(raw, buffer_size=4 << 20)) as archive:
            for name, pin in pending.items():
                info = archive.getinfo(name)
                if info.file_size != pin["size"] or f"{info.CRC:08x}" != pin["crc32"]:
                    raise ValueError(f"{name} in the remote archive differs from its pin.")
                content = archive.read(name)
                if hashlib.sha256(content).hexdigest() != pin["sha256"]:
                    raise ValueError(f"Downloaded {name} differs from the pinned release.")
                path = _target(directory, name)
                path.parent.mkdir(parents=True, exist_ok=True)
                partial = path.with_name(path.name + ".part")
                partial.write_bytes(content)
                partial.replace(path)
        requests = raw.requests
    return {
        "source": archive_spec["doi"],
        "archive": archive_spec["name"],
        "use_condition": reference["use_condition"],
        "downloaded": len(pending),
        "already_present": len(reference["members"]) - len(pending),
        "range_requests": requests,
        "files": verify_patient(directory, reference),
    }
