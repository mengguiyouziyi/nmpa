import json
from pathlib import Path
from typing import Iterable, List, Tuple

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
DOMESTIC_DATASETS = PROJECT_ROOT / "outputs" / "datasets"
FOREIGN_DATASETS = PROJECT_ROOT / "outputs_jingwai" / "datasets"
EXPORT_DIR = PROJECT_ROOT / "exports"


def _load_jsonl_files(base_dir: Path, prefixes: Iterable[str]) -> List[dict]:
    records: List[dict] = []
    if not base_dir.exists():
        return records
    prefix_tuple: Tuple[str, ...] = tuple(prefixes)
    for segment_dir in sorted(base_dir.iterdir()):
        if not segment_dir.is_dir():
            continue
        name = segment_dir.name
        if not name.startswith(prefix_tuple):
            continue
        for file_path in sorted(segment_dir.glob("*.jsonl")):
            with file_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    return records


def export_domestic(prefix_char: str, output_name: str) -> None:
    prefixes = [f"国药准字{prefix_char}"]
    records = _load_jsonl_files(DOMESTIC_DATASETS, prefixes)
    rows = [
        {
            "code": rec.get("code", ""),
            "name_zh": rec.get("zh", ""),
            "name_en": rec.get("en", ""),
        }
        for rec in records
    ]
    df = pd.DataFrame(rows)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_excel(EXPORT_DIR / output_name, index=False)


def export_foreign(prefix_char: str, output_name: str) -> None:
    prefixes = [f"国药准字{prefix_char}"]
    records = _load_jsonl_files(FOREIGN_DATASETS, prefixes)
    rows = [
        {
            "code": rec.get("code", ""),
            "product_zh": rec.get("product_zh", ""),
            "product_en": rec.get("product_en", ""),
            "commodity_zh": rec.get("commodity_zh", ""),
            "commodity_en": rec.get("commodity_en", ""),
        }
        for rec in records
    ]
    df = pd.DataFrame(rows)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_excel(EXPORT_DIR / output_name, index=False)


def main() -> None:
    export_domestic("H", "境内-国药准字H.xlsx")
    export_domestic("S", "境内-国药准字S.xlsx")
    export_foreign("H", "境外-国药准字H.xlsx")
    export_foreign("S", "境外-国药准字S.xlsx")


if __name__ == "__main__":
    main()
