"""Validate and convert the supplied poem workbook into application JSON."""

import argparse
import json
import re
from pathlib import Path
from typing import Optional

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = BASE_DIR / "data" / "AIタグ付け短歌・俳句.xlsx"
DEFAULT_OUTPUT = BASE_DIR / "poems.json"
REQUIRED_COLUMNS = ["句", "データ元", "年齢", "在住地", "AIタグ", "場所"]
NON_EMPTY_COLUMNS = ["句", "データ元", "AIタグ", "場所"]
KNOWN_TAGS = {"まちづくり", "観光", "危機管理", "福祉", "こども", "該当なし"}


def split_tags(value):
    if not isinstance(value, str):
        return []
    return [tag.strip() for tag in re.split(r"[,、]", value) if tag.strip()]


def validate_dataframe(dataframe):
    missing_columns = sorted(set(REQUIRED_COLUMNS) - set(dataframe.columns))
    report = {
        "row_count": len(dataframe),
        "missing_columns": missing_columns,
        "empty_values": {},
        "duplicate_poem_count": 0,
        "unknown_tags": [],
    }
    if missing_columns:
        return report

    for column in NON_EMPTY_COLUMNS:
        empty = dataframe[column].isna() | dataframe[column].astype(str).str.strip().eq("")
        report["empty_values"][column] = int(empty.sum())
    report["duplicate_poem_count"] = int(dataframe.duplicated(subset=["句"], keep=False).sum())
    tags = {tag for value in dataframe["AIタグ"] for tag in split_tags(value)}
    report["unknown_tags"] = sorted(tags - KNOWN_TAGS)
    return report


def has_blocking_errors(report):
    return bool(report["missing_columns"] or any(report["empty_values"].values()))


def convert(input_file: Path, output_file: Path, report_file: Optional[Path] = None):
    dataframe = pd.read_excel(input_file)
    report = validate_dataframe(dataframe)
    if report_file:
        report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if has_blocking_errors(report):
        raise ValueError(f"データ検証に失敗しました: {json.dumps(report, ensure_ascii=False)}")
    dataframe[REQUIRED_COLUMNS].to_json(output_file, orient="records", force_ascii=False, indent=2)
    print(f"{len(dataframe)} 件を {output_file} に変換しました。")
    if report["duplicate_poem_count"] or report["unknown_tags"]:
        print(f"警告: 重複句 {report['duplicate_poem_count']} 件、未定義タグ {report['unknown_tags']}")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=BASE_DIR / "data-validation-report.json")
    args = parser.parse_args()
    convert(args.input, args.output, args.report)
