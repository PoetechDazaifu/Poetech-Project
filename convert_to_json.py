"""Convert the supplied poem workbook into the application JSON format."""

import argparse
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = BASE_DIR / "data" / "AIタグ付け短歌・俳句.xlsx"
DEFAULT_OUTPUT = BASE_DIR / "poems.json"
REQUIRED_COLUMNS = ["句", "データ元", "年齢", "在住地", "AIタグ", "場所"]


def convert(input_file: Path, output_file: Path):
    dataframe = pd.read_excel(input_file)
    missing = set(REQUIRED_COLUMNS) - set(dataframe.columns)
    if missing:
        raise ValueError(f"必須列がありません: {', '.join(sorted(missing))}")
    dataframe[REQUIRED_COLUMNS].to_json(output_file, orient="records", force_ascii=False, indent=2)
    print(f"{len(dataframe)} 件を {output_file} に変換しました。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    convert(args.input, args.output)
