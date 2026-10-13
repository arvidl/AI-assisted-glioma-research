"""Source-attributed published aggregates, kept apart from simulated results."""

import hashlib
import json
import subprocess
import urllib.error
import urllib.request
from importlib.resources import files
from pathlib import Path

from glioma_ai.provenance import sha256


def published_figure_reference() -> dict:
    """Manifest of unmodified public illustrations; image bytes stay local."""
    source = files("glioma_ai").joinpath("references/imaging_figures.json")
    return json.loads(source.read_text())


def verify_published_figure(payload: bytes, expected_sha256: str) -> None:
    """Reject source substitution or corruption before writing an illustration."""
    if hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise ValueError("Published figure differs from the pinned source hash")


def prepare_published_figures(output: Path, *, checkout: Path | None = None) -> dict:
    """Explicitly import pinned published PNGs from the author Git checkout.

    No source access occurs unless called. Local checkout reads the pinned
    Git blobs, not potentially changed working files. All bytes are verified
    before writing. Published illustrations are kept outside synthetic run
    records and remain ignored. This does not execute the imaging pipeline.
    """
    if checkout is None:
        raise ValueError("Choose an explicit source author checkout")
    reference = published_figure_reference()
    payloads = []
    for entry in reference["figures"]:
        payload = subprocess.check_output(
            ["git", "show", f"{reference['revision']}:{entry['source_path']}"],
            cwd=checkout,
        )
        verify_published_figure(payload, entry["sha256"])
        payloads.append((entry["name"], payload))
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for name, payload in payloads:
        (output / name).write_bytes(payload)
    (output / "published_figures.json").write_text(json.dumps(reference, indent=2) + "\n")
    return reference


def fetch_published_figures(output: Path, *, repo: str | None = None, use_gh: bool = False) -> dict:
    """Explicitly download the pinned published PNGs from their GitHub release.

    Each file is checked against the manifest hash before anything is written;
    files already present and verified are kept.
    """
    reference = published_figure_reference()
    release = reference["release"]
    repo = repo or release["repository"]
    output = Path(output)
    payloads, downloaded = [], 0
    for entry in reference["figures"]:
        target = output / entry["name"]
        if target.is_file():
            verify_published_figure(target.read_bytes(), entry["sha256"])
            continue
        if use_gh:
            payload = subprocess.check_output(
                [
                    "gh",
                    "release",
                    "download",
                    release["tag"],
                    "-R",
                    repo,
                    "-p",
                    entry["name"],
                    "-O",
                    "-",
                ]
            )
        else:
            url = f"https://github.com/{repo}/releases/download/{release['tag']}/{entry['name']}"
            try:
                with urllib.request.urlopen(url, timeout=120) as response:
                    payload = response.read()
            except urllib.error.HTTPError as error:
                if error.code != 404:
                    raise
                raise FileNotFoundError(
                    f"{url} is not available; if {repo} is not public, use --use-gh"
                ) from error
        verify_published_figure(payload, entry["sha256"])
        payloads.append((target, payload))
    output.mkdir(parents=True, exist_ok=True)
    for target, payload in payloads:
        target.write_bytes(payload)
        downloaded += 1
    (output / "published_figures.json").write_text(json.dumps(reference, indent=2) + "\n")
    return {
        "directory": str(output),
        "figures": len(reference["figures"]),
        "downloaded": downloaded,
        "license": reference["license"],
        "attribution": reference["attribution"],
    }


def prepared_published_figures(directory: Path) -> list[dict]:
    """Readiness and verified paths, with no acquisition as a side effect."""
    result = []
    for entry in published_figure_reference()["figures"]:
        path = Path(directory) / entry["name"]
        ready = path.is_file()
        if ready:
            verify_published_figure(path.read_bytes(), entry["sha256"])
        result.append({**entry, "path": str(path), "ready": ready})
    return result


def published_imaging_reference() -> dict:
    """Read the checked publication record, without executing its pipeline."""
    source = files("glioma_ai").joinpath("references/lundervold2026.json")
    return json.loads(source.read_text())


def write_published_imaging_reference(output: Path, paper_dir: Path | None) -> dict:
    """Export attributed numbers and TeX macros separately from synthetic evidence."""
    reference = published_imaging_reference()
    source = Path(__file__).parent / "references/lundervold2026.json"
    reference["reference_record_sha256"] = sha256(source)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "published_imaging_reference.json").write_text(json.dumps(reference, indent=2) + "\n")
    if paper_dir is not None:
        paper_dir = Path(paper_dir)
        paper_dir.mkdir(parents=True, exist_ok=True)
        evaluation = reference["evaluation"]
        macros = {"PublishedImagingN": str(evaluation["n_subjects"])}
        for compartment, label in (
            ("whole_tumor", "WT"),
            ("tumor_core", "TC"),
            ("enhancing_tumor", "ET"),
        ):
            macros[f"PublishedDice{label}"] = f"{evaluation['median_dice'][compartment]:.2f}"
            macros[f"PublishedHD{label}"] = f"{evaluation['median_hd95_mm'][compartment]:.1f}"
        (paper_dir / "published_numbers.tex").write_text(
            "% Reported published aggregates; inference NOT rerun in this repository.\n"
            "% Source: "
            + reference["doi"]
            + ", abstract.\n"
            + "".join(
                "\\newcommand{\\" + key + "}{" + value + "}\n" for key, value in macros.items()
            )
        )
    return reference
