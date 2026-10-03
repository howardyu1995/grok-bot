#!/usr/bin/env python3
"""在 Cursor／本機直接分析富途牛牛與 Firstrade 月結／成交匯出。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lib.analyzer import analyze
from lib.parsers import parse_files
from lib.report import render_markdown

ROOT = Path(__file__).resolve().parent
DEFAULT_INPUTS = [ROOT / "statements", ROOT / "samples"]
REPORTS_DIR = ROOT / "reports"


def _collect_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file():
            files.append(path)
            continue
        if path.is_dir():
            for pattern in ("*.csv", "*.CSV", "*.xlsx", "*.XLSX", "*.xlsm"):
                files.extend(sorted(path.glob(pattern)))
    # de-dupe, prefer statements over samples if same name? keep all unique paths
    uniq: list[Path] = []
    seen: set[Path] = set()
    for f in files:
        resolved = f.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        uniq.append(f)
    return uniq


def _prefer_statements(files: list[Path]) -> list[Path]:
    """若 statements/ 已有檔案，就不要混進 samples（避免示範資料污染月结）。"""
    statement_files = [f for f in files if "statements" in f.parts]
    if statement_files:
        return statement_files
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="分析富途牛牛／Firstrade 月結或成交匯出，輸出交易傾向與優化建議。",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="檔案或資料夾；預設讀 statements/，若無檔則用 samples/",
    )
    parser.add_argument(
        "--month",
        help="只分析指定月份，格式 YYYY-MM（預設自動取資料中最常見月份）",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="報告輸出路徑（預設 reports/YYYY-MM.md）",
    )
    parser.add_argument(
        "--stdout-only",
        action="store_true",
        help="只印到終端，不寫入 reports/",
    )
    args = parser.parse_args(argv)

    input_paths = args.paths or DEFAULT_INPUTS
    files = _prefer_statements(_collect_files(input_paths))
    if not files:
        print(
            "找不到可分析檔案。請把富途／Firstrade 的 CSV 或 XLSX 放到 "
            f"{ROOT / 'statements'}/ 後再執行。",
            file=sys.stderr,
        )
        return 1

    print("讀取檔案：")
    for f in files:
        print(f"  - {f}")

    parsed = parse_files(files)
    trades = []
    warnings: list[str] = []
    for result in parsed:
        trades.extend(result.trades)
        warnings.extend(result.warnings)
        if result.trades:
            print(
                f"  ✓ {result.file_name}: {result.broker}，"
                f"{len(result.trades)} 筆成交（略過 {result.skipped_rows} 列）"
            )
        else:
            print(f"  ✗ {result.file_name}: 沒有解析到成交")
            for w in result.warnings:
                print(f"      - {w}")

    if not trades:
        print("沒有可用成交資料，中止。", file=sys.stderr)
        return 2

    analysis = analyze(trades, month=args.month)
    report = render_markdown(analysis, warnings=warnings)

    if not args.stdout_only:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        out = args.output or REPORTS_DIR / f"{analysis.month or 'report'}.md"
        out.write_text(report, encoding="utf-8")
        print(f"\n報告已寫入：{out}\n")

    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
