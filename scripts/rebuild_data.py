#!/usr/bin/env python3
"""Run workbook validation, JSON conversion, and atomic database rebuilding."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from convert_to_json import DEFAULT_INPUT, DEFAULT_OUTPUT, convert
from init_db import DB_FILE, build_database


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--json", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--database", type=Path, default=DB_FILE)
    parser.add_argument("--report", type=Path, default=ROOT / "data-validation-report.json")
    args = parser.parse_args()
    convert(args.input, args.json, args.report)
    build_database(args.json, args.database)


if __name__ == "__main__":
    main()
