"""Small explicit CLI for the reproducible teaching workflows."""

import argparse
import json
import platform
from pathlib import Path

from glioma_ai.assistance import validate_record
from glioma_ai.btc_cantab import fetch_btc
from glioma_ai.cantab import fetch_release
from glioma_ai.cantab_examples import write_cantab_example
from glioma_ai.cgga_clinical import summarize_cgga_clinical
from glioma_ai.demo import run_demo, write_json
from glioma_ai.hpgs_bundle import fetch_bundle as fetch_cohort_bundle
from glioma_ai.imaging import summarize_labels
from glioma_ai.lumiere_bundle import fetch_bundle
from glioma_ai.lumiere_fetch import fetch_patient
from glioma_ai.lumiere_slice import write_lumiere_slice_illustration
from glioma_ai.paper_assets import write_paper_assets
from glioma_ai.published import fetch_published_figures, prepare_published_figures
from glioma_ai.runtime import device_report
from glioma_ai.tcga_reports import summarize_tcga_reports


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspectable glioma research examples")
    commands = parser.add_subparsers(dest="command", required=True)
    doctor = commands.add_parser("doctor", help="Environment and optional device smoke check")
    doctor.add_argument("--device", choices=["auto", "cpu", "mps", "cuda"], default="auto")
    demo = commands.add_parser("demo", help="Generate all synthetic CPU examples")
    demo.add_argument("--output", type=Path, default=Path("outputs/demo"))
    demo.add_argument("--paper-dir", type=Path)
    nifti = commands.add_parser("nifti", help="Measure explicitly selected NIfTI labels")
    nifti.add_argument("path", type=Path)
    nifti.add_argument("--labels", type=int, nargs="+", required=True)
    nifti.add_argument("--reference", type=Path)
    nifti.add_argument("--output", type=Path)
    cgga = commands.add_parser("cgga", help="Count a locally supplied clinical table")
    cgga.add_argument("--input", required=True, type=Path)
    cgga.add_argument("--output", required=True, type=Path)
    reports = commands.add_parser("reports", help="Count stated terms in locally supplied reports")
    reports.add_argument("--archive", required=True, type=Path)
    reports.add_argument("--case-list", required=True, type=Path)
    reports.add_argument("--output", required=True, type=Path)
    lumiere = commands.add_parser("lumiere", help="Run explicitly configured prepared MRI recipe")
    lumiere.add_argument("--output", type=Path, default=Path("outputs/lumiere"))
    lumiere_fetch = commands.add_parser(
        "lumiere-fetch", help="Explicitly fetch pinned LUMIERE Patient-048 files"
    )
    lumiere_fetch.add_argument("--output", type=Path, default=Path("data/lumiere"))
    bundle = commands.add_parser(
        "lumiere-bundle-fetch", help="Explicitly fetch the pinned prepared Patient-048 bundle"
    )
    bundle.add_argument("--output", type=Path, default=Path("data"))
    bundle.add_argument("--repo", help="GitHub repository holding the release (default: pinned)")
    bundle.add_argument("--zip", type=Path, help="Verify and extract a local copy instead")
    bundle.add_argument("--use-gh", action="store_true", help="Download with the gh CLI")
    cohort = commands.add_parser(
        "hpgs-bundle-fetch", help="Explicitly fetch the pinned UCSF-PDGM cohort bundle"
    )
    cohort.add_argument("--output", type=Path, default=Path("data"))
    cohort.add_argument("--repo", help="GitHub repository holding the release (default: pinned)")
    cohort.add_argument("--zip", type=Path, help="Verify and extract a local copy instead")
    cohort.add_argument("--use-gh", action="store_true", help="Download with the gh CLI")
    released = commands.add_parser(
        "published-figures-fetch",
        help="Explicitly fetch the pinned published figures from their GitHub release",
    )
    released.add_argument("--output", type=Path, default=Path("paper/generated"))
    released.add_argument("--repo", help="GitHub repository holding the release (default: pinned)")
    released.add_argument("--use-gh", action="store_true", help="Download with the gh CLI")
    figures = commands.add_parser(
        "published-figures", help="Prepare pinned published public figures"
    )
    figures.add_argument("--output", type=Path, default=Path("paper/generated"))
    figures.add_argument("--checkout", type=Path, required=True)
    acquisition = commands.add_parser("cantab-fetch", help="Explicitly fetch pinned public tables")
    acquisition.add_argument("--output", type=Path, default=Path("data/cantab/osf"))
    btc = commands.add_parser(
        "btc-fetch", help="Explicitly fetch the pinned OpenNeuro BTC participant tables"
    )
    btc.add_argument("--output", type=Path, default=Path("data/btc"))
    cognition = commands.add_parser(
        "cantab", help="Verify prepared behavioral data and make evidence"
    )
    cognition.add_argument("--release-dir", type=Path, default=Path("data/cantab/osf"))
    cognition.add_argument("--case-config", type=Path)
    cognition.add_argument("--output", type=Path, default=Path("outputs/cantab"))
    cognition.add_argument("--paper-dir", type=Path)
    paper = commands.add_parser(
        "paper-assets", help="Write the paper's figures and number macros, notebook by notebook"
    )
    paper.add_argument("--output", type=Path, default=Path("outputs/paper"))
    paper.add_argument("--paper-dir", type=Path, default=Path("paper/generated"))
    paper.add_argument("--btc-dir", type=Path, default=Path("data/btc"))
    record = commands.add_parser("validate-record", help="Check assistance record completeness")
    record.add_argument("path", type=Path)
    args = parser.parse_args()
    if args.command == "doctor":
        result = {
            "python": platform.python_version(),
            "platform": platform.system(),
            "architecture": platform.machine(),
            **device_report(args.device),
        }
    elif args.command == "demo":
        result = run_demo(args.output, args.paper_dir)
    elif args.command == "nifti":
        result = summarize_labels(args.path, args.labels, args.reference)
    elif args.command == "cgga":
        result = summarize_cgga_clinical(args.input)
    elif args.command == "reports":
        result = summarize_tcga_reports(args.archive, args.case_list)
    elif args.command == "lumiere":
        result = write_lumiere_slice_illustration(args.output)
        if result is None:
            parser.error("Set LUMIERE_P048_ROOT to the documented prepared extract.")
    elif args.command == "lumiere-fetch":
        result = fetch_patient(args.output)
    elif args.command == "lumiere-bundle-fetch":
        result = fetch_bundle(args.output, repo=args.repo, zip_path=args.zip, use_gh=args.use_gh)
    elif args.command == "hpgs-bundle-fetch":
        result = fetch_cohort_bundle(
            args.output, repo=args.repo, zip_path=args.zip, use_gh=args.use_gh
        )
    elif args.command == "published-figures-fetch":
        result = fetch_published_figures(args.output, repo=args.repo, use_gh=args.use_gh)
    elif args.command == "published-figures":
        result = prepare_published_figures(args.output, checkout=args.checkout)
    elif args.command == "cantab-fetch":
        result = fetch_release(args.output)
    elif args.command == "btc-fetch":
        result = fetch_btc(args.output)
    elif args.command == "cantab":
        result = write_cantab_example(
            args.release_dir, args.output, args.case_config, args.paper_dir
        )
    elif args.command == "paper-assets":
        result = write_paper_assets(Path.cwd(), args.output, args.paper_dir, args.btc_dir)
    else:
        validate_record(json.loads(args.path.read_text()))
        result = {"record_complete": True, "scientific_quality_evaluated": False}
    if getattr(args, "output", None) is not None and args.command in {"nifti", "cgga", "reports"}:
        write_json(args.output, result)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
