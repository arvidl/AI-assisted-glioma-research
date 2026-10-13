import hashlib
import io
import zipfile

import pytest

from glioma_ai import lumiere_fetch as lf


def _archive() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("Imaging/", b"")
        archive.writestr("Imaging/Patient-048/week-045/CT1.nii.gz", b"ct1" * 1000)
        archive.writestr("Imaging/Patient-048/week-045/T1.nii.gz", b"t1" * 500)
        archive.writestr("Imaging/Patient-048/week-045/DeepBraTumIA-segmentation/x.json", b"{}")
        archive.writestr("Imaging/Patient-049/week-001/CT1.nii.gz", b"other")
    return buffer.getvalue()


def _reader(data: bytes, calls: list):
    def read(start: int, stop: int) -> bytes:
        calls.append((start, stop))
        return data[start:stop]

    return read


def _reference(data: bytes) -> dict:
    archive = lf.open_archive(_reader(data, []), len(data))
    names = lf.staged_member_names(archive)
    return {
        "archive": {"name": "test.zip", "size": len(data), "doi": "test", "download_url": ""},
        "use_condition": "test",
        "members": lf.pin_members(archive, names),
    }


def test_selection_keeps_only_the_staged_files_of_one_patient():
    data = _archive()
    archive = lf.open_archive(_reader(data, []), len(data))
    assert lf.staged_member_names(archive) == [
        "Imaging/Patient-048/week-045/CT1.nii.gz",
        "Imaging/Patient-048/week-045/T1.nii.gz",
    ]


def test_fetch_writes_verified_members_and_is_idempotent(tmp_path):
    data = _archive()
    reference = _reference(data)
    calls = []
    result = lf.fetch_patient(tmp_path, reference=reference, read=_reader(data, calls))
    assert result["downloaded"] == 2 and result["range_requests"] == len(calls) > 0
    content = (tmp_path / "Patient-048/week-045/CT1.nii.gz").read_bytes()
    assert (
        hashlib.sha256(content).hexdigest()
        == reference["members"]["Imaging/Patient-048/week-045/CT1.nii.gz"]["sha256"]
    )
    again = lf.fetch_patient(tmp_path, reference=reference, read=_reader(data, []))
    assert again["downloaded"] == 0 and again["already_present"] == 2


def test_fetch_refuses_changed_local_or_remote_files(tmp_path):
    data = _archive()
    reference = _reference(data)
    target = tmp_path / "Patient-048/week-045/T1.nii.gz"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"edited")
    with pytest.raises(ValueError, match="preserve it"):
        lf.fetch_patient(tmp_path, reference=reference, read=_reader(data, []))
    target.unlink()
    reference["members"]["Imaging/Patient-048/week-045/T1.nii.gz"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="differs from the pinned release"):
        lf.fetch_patient(tmp_path, reference=reference, read=_reader(data, []))
    assert not target.exists()


def test_pinned_reference_is_the_documented_selection():
    reference = lf.imaging_reference()
    assert reference["archive"]["size"] == 32565467707
    assert len(reference["members"]) == 36
    weeks = {name.split("/")[2] for name in reference["members"]}
    assert weeks == {"week-000-1", "week-000-2", "week-013", "week-023", "week-045", "week-049"}
    assert "non-commercial" in reference["use_condition"]
