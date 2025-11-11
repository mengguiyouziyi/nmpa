import json
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent / "outputs_yuanliaoyao"
INPUT_FILE = BASE_DIR / "原料药.jsonl"
OUTPUT_FILE = BASE_DIR / "原料药.xlsx"


def main() -> None:
    rows = []
    with INPUT_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    df = pd.DataFrame(rows)
    df.to_excel(OUTPUT_FILE, index=False)


if __name__ == "__main__":
    main()
