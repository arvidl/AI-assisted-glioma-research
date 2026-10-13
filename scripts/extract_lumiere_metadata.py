"""Extract one patient's released LUMIERE metadata into a tracked reference file.

Reads the dataset's CSV tables from an explicit local directory (nothing is
downloaded) and writes src/glioma_ai/references/<name>.json with the SHA-256 of
each table. The investigator authorized tracking Patient-048's released
metadata, including demographics and pathology (see AGENTS.md).
"""

import argparse
import json
from pathlib import Path

from glioma_ai.lumiere_metadata import read_case_metadata


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lumiere-dir", type=Path, required=True)
    parser.add_argument("--patient", default="Patient-048")
    parser.add_argument("--name", default="lumiere_p048")
    arguments = parser.parse_args()
    metadata = read_case_metadata(arguments.lumiere_dir, arguments.patient)
    target = root / "src/glioma_ai/references" / f"{arguments.name}.json"
    target.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {target.relative_to(root)} ({len(metadata['visits'])} visits)")


if __name__ == "__main__":
    main()
