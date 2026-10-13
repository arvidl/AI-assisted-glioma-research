"""Release bundle of the prepared LUMIERE Patient-048 inputs used by notebook 03.

The bundle holds only the files notebook 03 reads from a prepared root: per visit
the registered CT1, the MONAI BraTS label map with its record and the
registration QC record, plus the week-045 FreeSurfer parcellation. NIfTI files
are copied byte for byte. JSON records are rewritten only to replace absolute
local paths (relative to the prepared root where possible). The ZIP is
deterministic, so the same inputs give the same SHA-256. Use is subject to the
LUMIERE authors' non-commercial condition.
"""

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from glioma_ai.lumiere_slice import VISITS
from glioma_ai.provenance import sha256

REFERENCE = Path(__file__).parent / "references/lumiere_bundle_p048.json"
BUNDLE_NAME = "lumiere_p048_prepared"
VERSION = "v1"
REMOVED = "<local path removed>"
ZIP_TIME = (1980, 1, 1, 0, 0, 0)
ABSOLUTE = re.compile(r"(?:/Users|/home|/private|/var|/tmp|[A-Za-z]:\\)[^\s\"']*")

README = """# LUMIERE Patient-048, prepared inputs for notebook 03 ({version})

Registered contrast-enhanced T1 (CT1) images, automated tumour labels and a
week-045 tissue parcellation of one patient of the LUMIERE dataset, on one
1 mm RAS reference grid (the week-000-1 T1). They let notebook 03 of
AI-assisted-glioma-research run, including its 3D section, without repeating
registration, segmentation and FreeSurfer.

## Source and attribution

Suter Y, Knecht U, Valenzuela W, Notter M, Hewer E, Schucht P, Wiest R, Reyes M.
The LUMIERE dataset: Longitudinal Glioblastoma MRI with expert RANO evaluation.
Scientific Data 9, 768 (2022). https://doi.org/10.1038/s41597-022-01881-7
Data: https://doi.org/10.6084/m9.figshare.c.5904905.v1 (images: article 21249516).

**Use condition.** The Figshare files are labelled CC0, but the dataset
authors state that "this dataset may only be used for non-commercial purposes".
These derived files are shared for research, teaching and learning under the
same non-commercial condition. They are not covered by the MIT licence of the
code repository. Cite the article above when using them.

## How the files were made (upstream, not rerun by the notebook)

- Released skull-stripped LUMIERE images of Patient-048 (six visits).
- Rigid ANTsPyX registration of every visit to the week-000-1 T1, resampled to
  1 mm RAS (`registration_qc.json` per visit).
- Tumour labels from the MONAI `brats_mri_segmentation` bundle 0.4.8 (SegResNet),
  labels 1 necrosis/non-enhancing, 2 oedema, 4 enhancing (`*_seg_brats3_dl.json`).
  Automated labels, not expert masks.
- FreeSurfer 8.2.0 `wmparc` on the registered week-045 T1
  (`tp-week-045_wmparc.json`). FreeSurfer is not designed for brains with
  lesions; its classes near the tumour are unreliable.

Produced in the investigator's high-precision-glioma-segmentation project.
NIfTI files are unchanged; absolute local paths in the JSON records were
replaced (relative to this folder, or "{removed}"). `MANIFEST.json` lists every
file with its SHA-256 and, for rewritten records, the SHA-256 of the original.

## Use

Point notebook 03 at this folder, e.g. in `local/lumiere-case.json`:
`{{"prepared_root": "/absolute/path/to/{name}"}}`, or fetch and verify it with
`make lumiere-bundle-fetch`.

No patient identifiers beyond the released LUMIERE pseudonym are included.
"""


def bundle_files(prepared_root: Path) -> list[str]:
    """Relative paths, under ``prepared_root``, of every file notebook 03 reads."""
    root = Path(prepared_root)
    names = []
    for visit in VISITS:
        tp = f"derivatives/tp-{visit['name']}"
        names += [
            f"{tp}/tp-{visit['name']}_CT1_to_ref.nii.gz",
            f"{tp}/seg_dl/tp-{visit['name']}_seg_brats3_dl.nii.gz",
            f"{tp}/seg_dl/tp-{visit['name']}_seg_brats3_dl.json",
            f"{tp}/registration_qc.json",
        ]
    parcellation = "derivatives/tp-week-045/parcellation"
    names += [
        f"{parcellation}/tp-week-045_wmparc_native.nii.gz",
        f"{parcellation}/tp-week-045_wmparc_lut.json",
        f"{parcellation}/tp-week-045_wmparc.json",
    ]
    missing = [name for name in names if not (root / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Prepared root lacks {len(missing)} file(s), e.g. {missing[0]}")
    return names


def clean_paths(value, root: Path):
    """Replace absolute paths in a JSON value; paths inside ``root`` become relative."""
    if isinstance(value, dict):
        return {key: clean_paths(item, root) for key, item in value.items()}
    if isinstance(value, list):
        return [clean_paths(item, root) for item in value]
    if isinstance(value, str):
        prefix = str(Path(root).resolve()) + "/"
        text = value.replace(prefix, "").replace(str(Path(root).resolve()), ".")
        return ABSOLUTE.sub(REMOVED, text)
    return value


def _entry(name: str, compress: bool, bundle: str = BUNDLE_NAME) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(f"{bundle}/{name}", date_time=ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED
    info.external_attr = 0o644 << 16
    info.create_system = 3
    return info


def build_bundle(prepared_root: Path, output: Path) -> dict:
    """Write ``<output>/lumiere_p048_prepared_v1.zip``; return its manifest and hash."""
    root = Path(prepared_root).resolve()
    contents, files = {}, []
    home = str(Path.home())
    for name in bundle_files(root):
        path = root / name
        original = path.read_bytes()
        if name.endswith(".json"):
            cleaned = json.loads(original.decode("utf-8"))
            data = (
                json.dumps(clean_paths(cleaned, root), indent=2, sort_keys=True) + "\n"
            ).encode()
        else:
            data = original
        if home.encode() in data or (name.endswith(".json") and ABSOLUTE.search(data.decode())):
            raise ValueError(f"A local path survived cleaning in {name}.")
        contents[name] = data
        record = {"path": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        if data != original:
            record["original_sha256"] = hashlib.sha256(original).hexdigest()
            record["rewritten"] = "absolute local paths replaced"
        files.append(record)
    manifest = {
        "schema": "lumiere-prepared-bundle-v1",
        "bundle": BUNDLE_NAME,
        "version": VERSION,
        "patient": "LUMIERE Patient-048",
        "source": "https://doi.org/10.1038/s41597-022-01881-7",
        "source_data": "https://doi.org/10.6084/m9.figshare.c.5904905.v1",
        "use_condition": (
            "non-commercial research, teaching and learning, as stated by the LUMIERE "
            "authors; not covered by the code repository's MIT licence"
        ),
        "grid": "1 mm RAS, week-000-1 T1 reference; registration supplied upstream",
        "files": files,
    }
    readme = README.format(version=VERSION, removed=REMOVED, name=BUNDLE_NAME).encode()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"{BUNDLE_NAME}_{VERSION}.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(_entry("README.md", True), readme, compresslevel=9)
        zf.writestr(
            _entry("MANIFEST.json", True),
            json.dumps(manifest, indent=2) + "\n",
            compresslevel=9,
        )
        for name in sorted(contents):
            zf.writestr(_entry(name, name.endswith(".json")), contents[name], compresslevel=9)
    return {
        "archive": str(archive),
        "size": archive.stat().st_size,
        "sha256": sha256(archive),
        "files": len(files),
    }


def bundle_reference() -> dict:
    return json.loads(REFERENCE.read_text())


def _download(reference: dict, repo: str, use_gh: bool, folder: Path) -> Path:
    asset, tag = reference["asset"], reference["tag"]
    target = folder / asset
    if use_gh:
        subprocess.run(
            ["gh", "release", "download", tag, "-R", repo, "-p", asset, "-D", str(folder)],
            check=True,
        )
    else:
        url = f"https://github.com/{repo}/releases/download/{tag}/{asset}"
        try:
            with urllib.request.urlopen(url, timeout=120) as response, target.open("wb") as out:
                shutil.copyfileobj(response, out)
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
            raise FileNotFoundError(
                f"{url} is not available; if {repo} is not public, use --use-gh with an "
                "authorized GitHub CLI, or pass a downloaded archive with --zip"
            ) from error
    return target


def verify_bundle(folder: Path) -> dict:
    """Check every file of an extracted bundle against its MANIFEST.json."""
    folder = Path(folder)
    manifest = json.loads((folder / "MANIFEST.json").read_text())
    for record in manifest["files"]:
        path = folder / record["path"]
        if not path.is_file() or sha256(path) != record["sha256"]:
            raise ValueError(f"Missing or changed bundle file: {record['path']}.")
    return manifest


def fetch_bundle(
    output: Path,
    *,
    repo: str | None = None,
    zip_path: Path | None = None,
    use_gh: bool = False,
    reference: dict | None = None,
) -> dict:
    """Download (or take ``zip_path``), check the pinned SHA-256, extract and verify.

    The prepared root is ``<output>/lumiere_p048_prepared``. An existing folder
    is kept only if it verifies against its manifest.
    """
    reference = reference or bundle_reference()
    folder, manifest, downloaded = fetch_archive(
        output, BUNDLE_NAME, reference, repo=repo, zip_path=zip_path, use_gh=use_gh
    )
    return _fetched(folder, manifest, downloaded=downloaded)


def fetch_archive(
    output: Path,
    bundle: str,
    reference: dict,
    *,
    repo: str | None = None,
    zip_path: Path | None = None,
    use_gh: bool = False,
) -> tuple[Path, dict, bool]:
    """Fetch a pinned release archive whose members all lie under ``bundle/``.

    Returns the extracted folder, its verified manifest and whether it was downloaded.
    """
    output = Path(output)
    folder = output / bundle
    if folder.exists():
        return folder, verify_bundle(folder), False
    with tempfile.TemporaryDirectory() as temporary:
        archive = (
            Path(zip_path)
            if zip_path
            else _download(reference, repo or reference["repository"], use_gh, Path(temporary))
        )
        if sha256(archive) != reference["sha256"]:
            raise ValueError("The bundle differs from the pinned SHA-256; nothing extracted.")
        with zipfile.ZipFile(archive) as zf:
            for name in zf.namelist():
                parts = Path(name).parts
                if Path(name).is_absolute() or ".." in parts or parts[0] != bundle:
                    raise ValueError(f"Unsafe member in bundle: {name}")
            staging = output / f".{bundle}.part"
            if staging.exists():
                shutil.rmtree(staging)
            zf.extractall(staging)
        manifest = verify_bundle(staging / bundle)
        (staging / bundle).replace(folder)
        staging.rmdir()
    return folder, manifest, zip_path is None


def _fetched(folder: Path, manifest: dict, *, downloaded: bool) -> dict:
    return {
        "prepared_root": str(folder),
        "files": len(manifest["files"]),
        "downloaded": downloaded,
        "use_condition": manifest["use_condition"],
        "next_step": f'set {{"prepared_root": "{folder.resolve()}"}} in local/lumiere-case.json',
    }
