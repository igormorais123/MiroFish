"""CLI for generating the Helena HTML report validation lab."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.helena_report_lab import build_helena_report_lab


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Helena/Efesto/Oracle HTML report lab.")
    parser.add_argument(
        "--output-dir",
        default="docs/validation/helena_report_lab_2026-05-07",
        help="Directory where HTML reports and manifests will be written.",
    )
    args = parser.parse_args()

    manifest = build_helena_report_lab(Path(args.output_dir))
    print(json.dumps({
        "output_dir": args.output_dir,
        "reports_count": manifest["reports_count"],
        "passes": manifest["passes"],
        "oracle_verdict": manifest["oracle_verdict"],
    }, ensure_ascii=False, indent=2))
    return 0 if manifest.get("passes") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
