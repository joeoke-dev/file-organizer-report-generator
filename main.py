"""File organizer & data cleaner.

Commands
--------
organize   Sort the files in a messy folder into subfolders by type.
           Dry run by default; add --apply to actually move files.
clean      Clean a messy sales CSV and save the result.
report     Build charts and an HTML report from the cleaned data.
run        Clean a messy CSV and build the report in one go.

Examples
--------
python main.py organize --inbox inbox --dest sorted
python main.py organize --inbox inbox --dest sorted --apply
python main.py clean --input data/sample_messy_sales.csv
python main.py run --input data/sample_messy_sales.csv
"""

import argparse
import json
from collections import Counter
from pathlib import Path

import pandas as pd

from cleaner import clean_sales
from organizer import apply_moves, plan_moves
from report import build_report


def parse_args():
    parser = argparse.ArgumentParser(description="File organizer and data cleaner.")
    sub = parser.add_subparsers(dest="command", required=True)

    org = sub.add_parser("organize", help="Sort files into folders by type")
    org.add_argument("--inbox", default="inbox", help="Folder containing the messy files")
    org.add_argument("--dest", default="sorted", help="Folder to sort the files into")
    org.add_argument("--apply", action="store_true", help="Actually move files (default: dry run)")

    clean = sub.add_parser("clean", help="Clean a messy sales CSV")
    clean.add_argument("--input", required=True, help="Path to the messy CSV")
    clean.add_argument("--output", default="output", help="Folder for the cleaned data and summary")

    rep = sub.add_parser("report", help="Build charts and an HTML report from cleaned data")
    rep.add_argument("--output", default="output", help="Folder holding clean_sales.csv (and receiving the report)")

    run = sub.add_parser("run", help="Clean a messy CSV and build the report")
    run.add_argument("--input", required=True, help="Path to the messy CSV")
    run.add_argument("--output", default="output", help="Folder for all results")

    return parser.parse_args()


def run_organize(args):
    moves = plan_moves(args.inbox, args.dest)
    if not moves:
        print(f"No files to organize in {args.inbox}/")
        return

    print(f"Found {len(moves)} files in {args.inbox}/\n")
    for source, target in moves:
        print(f"  {source.name:<25} -> {target.parent.name}/{target.name}")

    counts = Counter(target.parent.name for _, target in moves)
    print("\nBy category:")
    for category, count in sorted(counts.items()):
        print(f"  {category}: {count}")

    if not args.apply:
        print("\nDry run only. Add --apply to move the files.")
        return

    log_file = Path(args.dest) / "moves_log.csv"
    Path(args.dest).mkdir(parents=True, exist_ok=True)
    results = apply_moves(moves, log_file)
    moved = sum(1 for _, _, status in results if status == "moved")
    print(f"\nMoved {moved} of {len(results)} files. Log saved to {log_file}")


def run_clean(args):
    raw = pd.read_csv(args.input, dtype=str, keep_default_na=False)
    clean, summary = clean_sales(raw)

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    clean.to_csv(output / "clean_sales.csv", index=False)
    (output / "cleaning_summary.json").write_text(json.dumps(summary, indent=2))

    print(f"Rows in:  {summary['rows_in']}")
    print(f"Rows out: {summary['rows_out']}\n")
    print("What was done:")
    for key, value in summary.items():
        if key not in ("rows_in", "rows_out"):
            print(f"  {key.replace('_', ' ')}: {value}")
    print(f"\nSaved {output / 'clean_sales.csv'} and {output / 'cleaning_summary.json'}")


def run_report(args):
    output = Path(args.output)
    clean_file = output / "clean_sales.csv"
    summary_file = output / "cleaning_summary.json"
    if not clean_file.exists() or not summary_file.exists():
        raise FileNotFoundError(f"Run the clean command first: {clean_file} not found")

    df = pd.read_csv(clean_file, parse_dates=["date"])
    summary = json.loads(summary_file.read_text())
    report_path = build_report(df, summary, output)
    print(f"\nSaved charts and report to {output}/")
    print(f"Open {report_path} in a browser to view it.")


def main():
    args = parse_args()
    if args.command == "organize":
        run_organize(args)
    elif args.command == "clean":
        run_clean(args)
    elif args.command == "report":
        run_report(args)
    elif args.command == "run":
        run_clean(args)
        run_report(args)


if __name__ == "__main__":
    main()
