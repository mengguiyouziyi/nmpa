# -*- coding: utf-8 -*-
import os, json
from typing import List, Dict, Any
import pandas as pd

def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)

def export_records(records: List[Dict[str, Any]], out_dir: str, basename: str, export_format: str = "excel"):
    ensure_dir(out_dir)

    # 导出结构化必需字段
    df = pd.DataFrame([r["fields"] for r in records])
    # 原始JSON留档
    raw_path = os.path.join(out_dir, f"{basename}.raw.jsonl")
    with open(raw_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r["raw"], ensure_ascii=False) + "\n")

    out = {}
    if export_format in ("excel", "both"):
        xlsx = os.path.join(out_dir, f"{basename}.xlsx")
        df.to_excel(xlsx, index=False)
        out["excel"] = xlsx

    if export_format in ("csv", "both"):
        csv = os.path.join(out_dir, f"{basename}.csv")
        df.to_csv(csv, index=False, encoding="utf-8-sig")
        out["csv"] = csv

    out["raw"] = raw_path
    return out
