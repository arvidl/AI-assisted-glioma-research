"""Release bundle of the UCSF-PDGM cohort inputs used by Figure 3 of notebook 01.

The bundle holds, for the 50-subject evaluation cohort of the companion study,
the dataset reference segmentations, the companion's SegResNet label maps with
their records and its per-subject metrics records, plus the bias-corrected
post-contrast T1 of the one subject Figure 3 shows. It keeps the companion
checkout's layout, so the extracted folder can be named by ``HPGS_REPO``.
NIfTI files are copied byte for byte; JSON records only lose absolute local
paths. The ZIP is deterministic. UCSF-PDGM is licensed CC BY 4.0 by TCIA.
"""

import hashlib
import json
import zipfile
from pathlib import Path

from glioma_ai.hpgs_cohort import COHORT, IMAGES, _paths, cohort_subjects, cohort_table, median_case
from glioma_ai.lumiere_bundle import ABSOLUTE, _entry, clean_paths, fetch_archive
from glioma_ai.provenance import sha256

REFERENCE = Path(__file__).parent / "references/hpgs_bundle_cohort50.json"
BUNDLE_NAME = "ucsf_pdgm_cohort50"
VERSION = "v1"

README = """# UCSF-PDGM 50-subject cohort, inputs for Figure 3 of notebook 01 ({version})

Dataset reference tumour segmentations of the 50-subject evaluation cohort of
Lundervold et al. (2026), the SegResNet label maps that study produced for them,
its per-subject metrics records, and the bias-corrected post-contrast T1 (T1c)
of subject UCSF-PDGM-{case}, the subject Figure 3 shows. They let notebook 01 of
AI-assisted-glioma-research recompute Dice and volume error and draw Figure 3
without the 142 GB dataset and without rerunning the model.

## Source, licence and attribution

UCSF-PDGM v5, The Cancer Imaging Archive, licensed CC BY 4.0
(https://creativecommons.org/licenses/by/4.0/). Users must also follow the TCIA
Data Usage Policy and Restrictions
(https://www.cancerimagingarchive.net/data-usage-policies-and-restrictions/).
Cite:

- Calabrese E, Villanueva-Meyer J, Rudie J, Rauschecker A, Baid U, Bakas S,
  Cha S, Mongan J, Hess C (2022). The University of California San Francisco
  Preoperative Diffuse Glioma MRI (UCSF-PDGM) (Version 5) [dataset]. The Cancer
  Imaging Archive. https://doi.org/10.7937/tcia.bdgf-8v37
- Calabrese E, et al. (2022). The UCSF Preoperative Diffuse Glioma MRI
  (UCSF-PDGM) Dataset. Radiology: Artificial Intelligence.
  https://doi.org/10.1148/ryai.220058

The model label maps, their records and the metrics records are derivatives
produced by Lundervold et al. (2026), https://doi.org/10.1080/03091902.2026.2713703,
and are shared under CC BY 4.0; cite that article when using them.

## Contents and changes

- `{images}/sub-XXXX/sub-XXXX_tumor_segmentation.nii.gz`: the dataset's
  reference segmentation (labels 1 necrotic core, 2 oedema, 4 enhancing).
- `{images}/sub-{case}/sub-{case}_T1c_bias.nii.gz`: the dataset's bias-corrected
  post-contrast T1 of one subject.
- `{cohort}/sub-XXXX/seg_dl/`: MONAI `brats_mri_segmentation` (SegResNet) label
  map and its record. Automated labels; no inference is rerun by the notebook.
- `{cohort}/sub-XXXX/metrics/`: the companion's Dice and related metrics.

Dataset files were copied from the UCSF-PDGM v5 release and renamed from
`UCSF-PDGM-XXXX_*` to `sub-XXXX_*` by the companion's staging script; their
contents are unchanged. JSON records were re-serialized with sorted keys, and
any absolute local paths in them removed. `MANIFEST.json` lists every file with
its SHA-256 (and, for re-serialized records, the SHA-256 of the original).
Subjects are identified only by their public UCSF-PDGM numbers.

## Use

Fetch and verify with `make hpgs-bundle-fetch`, then set
`HPGS_REPO=/absolute/path/to/{name}` or `{{"checkout": "/absolute/path/to/{name}"}}`
in `local/hpgs.json`. Not for clinical use.
"""


def bundle_files(checkout: Path) -> tuple[list[str], str]:
    """Relative paths of every file Figure 3 reads, and the subject it shows."""
    checkout = Path(checkout)
    subjects = cohort_subjects(checkout)
    if not subjects:
        raise FileNotFoundError(f"No cohort subjects under {checkout}.")
    case = median_case(cohort_table(checkout))
    names = []
    for subject in subjects:
        paths = _paths(checkout, subject)
        record = paths["prediction"].with_suffix("").with_suffix(".json")
        names += [str(paths[key].relative_to(checkout)) for key in ("reference", "prediction")]
        names += [str(record.relative_to(checkout)), str(paths["metrics"].relative_to(checkout))]
    names.append(str(_paths(checkout, case)["t1c"].relative_to(checkout)))
    missing = [name for name in names if not (checkout / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Checkout lacks {len(missing)} file(s), e.g. {missing[0]}")
    return sorted(names), case


def build_bundle(checkout: Path, output: Path) -> dict:
    """Write ``<output>/ucsf_pdgm_cohort50_v1.zip``; return its size, hash and counts."""
    root = Path(checkout).resolve()
    names, case = bundle_files(root)
    contents, files = {}, []
    home = str(Path.home())
    for name in names:
        original = (root / name).read_bytes()
        change = "JSON formatting normalized"
        if name.endswith(".json"):
            parsed = json.loads(original.decode("utf-8"))
            cleaned = clean_paths(parsed, root)
            if cleaned != parsed:
                change += "; absolute local paths removed"
            data = (json.dumps(cleaned, indent=2, sort_keys=True) + "\n").encode()
        else:
            data = original
        if home.encode() in data or (name.endswith(".json") and ABSOLUTE.search(data.decode())):
            raise ValueError(f"A local path survived cleaning in {name}.")
        contents[name] = data
        record = {"path": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        if data != original:
            record["original_sha256"] = hashlib.sha256(original).hexdigest()
            record["rewritten"] = change
        files.append(record)
    manifest = {
        "schema": "hpgs-cohort-bundle-v1",
        "bundle": BUNDLE_NAME,
        "version": VERSION,
        "dataset": "UCSF-PDGM v5, https://doi.org/10.7937/tcia.bdgf-8v37",
        "licence": "CC BY 4.0 (dataset files, TCIA); CC BY 4.0 (companion derivatives)",
        "use_condition": (
            "CC BY 4.0 with attribution to UCSF-PDGM (Calabrese et al. 2022) and "
            "Lundervold et al. 2026; TCIA Data Usage Policy applies"
        ),
        "companion_study": "https://doi.org/10.1080/03091902.2026.2713703",
        "figure_case": case,
        "subjects": len({Path(name).parts[2] for name in names}),
        "files": files,
    }
    readme = README.format(
        version=VERSION, case=case, images=IMAGES, cohort=COHORT, name=BUNDLE_NAME
    ).encode()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"{BUNDLE_NAME}_{VERSION}.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(_entry("README.md", True, BUNDLE_NAME), readme, compresslevel=9)
        zf.writestr(
            _entry("MANIFEST.json", True, BUNDLE_NAME),
            json.dumps(manifest, indent=2) + "\n",
            compresslevel=9,
        )
        for name in sorted(contents):
            zf.writestr(
                _entry(name, name.endswith(".json"), BUNDLE_NAME), contents[name], compresslevel=9
            )
    return {
        "archive": str(archive),
        "size": archive.stat().st_size,
        "sha256": sha256(archive),
        "files": len(files),
        "subjects": manifest["subjects"],
        "figure_case": case,
    }


def bundle_reference() -> dict:
    return json.loads(REFERENCE.read_text())


def fetch_bundle(
    output: Path,
    *,
    repo: str | None = None,
    zip_path: Path | None = None,
    use_gh: bool = False,
    reference: dict | None = None,
) -> dict:
    """Download (or take ``zip_path``), check the pinned SHA-256, extract and verify."""
    reference = reference or bundle_reference()
    folder, manifest, downloaded = fetch_archive(
        output,
        BUNDLE_NAME,
        reference,
        repo=repo or reference["repository"],
        zip_path=zip_path,
        use_gh=use_gh,
    )
    return {
        "checkout": str(folder),
        "files": len(manifest["files"]),
        "subjects": manifest["subjects"],
        "downloaded": downloaded,
        "use_condition": manifest["use_condition"],
        "next_step": f'set HPGS_REPO={folder.resolve()} or {{"checkout": "{folder.resolve()}"}} '
        "in local/hpgs.json",
    }
