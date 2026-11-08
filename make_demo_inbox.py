"""Create a small messy folder of placeholder files to try the organizer on."""

import sys
from pathlib import Path

NAMES = [
    "sales_jan.csv", "sales_feb.csv", "notes.txt", "photo1.jpg", "photo2.PNG",
    "report_draft.pdf", "budget.xlsx", "script.py", "backup.zip", "random_file",
    ".hidden_config",
]


def main(folder="inbox"):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for name in NAMES:
        (folder / name).write_text("placeholder")
    print(f"Created {len(NAMES)} files in {folder}/")


if __name__ == "__main__":
    main(*sys.argv[1:2])
