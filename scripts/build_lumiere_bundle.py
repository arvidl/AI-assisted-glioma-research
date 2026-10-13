"""Build the deterministic release ZIP of the prepared LUMIERE Patient-048 inputs."""

import argparse
import json
from pathlib import Path

from glioma_ai.lumiere_bundle import build_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("outputs/lumiere_bundle"))
    args = parser.parse_args()
    result = build_bundle(args.prepared_root, args.output)
    result["archive"] = str(Path(result["archive"]).resolve().relative_to(Path.cwd().resolve()))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
