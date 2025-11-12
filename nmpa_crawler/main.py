# -*- coding: utf-8 -*-
import argparse, json, os, sys, yaml, traceback
from typing import Any, Dict, List
from tqdm import tqdm
from rich import print as rprint

from browser_engine import NMPABrowserCrawler
from exporter import export_records

def run_jobs(cfg: Dict[str, Any]):
    mode = (cfg.get("mode") or "browser").lower()
    export_dir = cfg.get("output_dir", "outputs")
    jobs = cfg.get("jobs", [])
    results = []

    if mode == "browser":
        crawler = NMPABrowserCrawler(cfg)
        crawler.start()
        try:
            for job in jobs:
                dataset = job["dataset"]
                code_prefix = job["code_prefix"]
                rprint(f"[bold green]开始任务[/] dataset=[cyan]{dataset}[/] code_prefix=[magenta]{code_prefix}[/]")
                recs = crawler.crawl_job(dataset, code_prefix, export_dir)
                base = f"{dataset}_{code_prefix}"
                outs = export_records(recs, export_dir, base, cfg.get("export_format","excel"))
                rprint(f"  -> 导出完成: {outs}")
                results.append({"job": job, "export": outs, "count": len(recs)})
        finally:
            crawler.stop()
    else:
        # 可扩展: HTTP 引擎（需要 sign 算法）
        from http_engine import NMPAHttpEngine
        from utils import extract_required_fields, deep_find_item_id
        import httpx, time

        cli = NMPAHttpEngine(cfg)

        # 动态获取 itemId（尽量）
        item_ids = {}
        try:
            with httpx.Client() as hc:
                r = hc.get("https://www.nmpa.gov.cn/datasearch/config/NMPA_DATA.json", params={"date": int(time.time()*1000)})
                r.raise_for_status()
                data = r.json()
                item_ids["domestic"] = deep_find_item_id(data, "境内生产药品")
                item_ids["imported"] = deep_find_item_id(data, "境外生产药品")
        except Exception:
            # 回退静态
            try:
                with open("static_item_ids.json","r",encoding="utf-8") as f:
                    item_ids = json.load(f)
            except Exception:
                pass

        for job in jobs:
            dataset = job["dataset"]
            code_prefix = job["code_prefix"]
            item_id = item_ids.get(dataset,"")
            if not item_id:
                raise RuntimeError(f"未获取到 {dataset} itemId.")
            rprint(f"[bold yellow]HTTP引擎(实验)开始[/] dataset=[cyan]{dataset}[/] code_prefix=[magenta]{code_prefix}[/]")
            page = 1
            page_size = int(cfg.get("page_size", 30))
            all_recs = []
            while page <= int(cfg.get("max_pages", 50)):
                data = cli.search(item_id, code_prefix, page, page_size)
                node = data.get('data', data) if isinstance(data, dict) else {}
                lst = node.get('list') or node.get('resultList') or node.get('rows') or []
                if not lst:
                    break
                for row in lst:
                    doc_id = str(row.get('id') or row.get('ID') or row.get('docId') or row.get('dataId') or '')
                    if not doc_id:
                        continue
                    detail = cli.detail(item_id, doc_id)
                    fields = extract_required_fields(detail, dataset)
                    all_recs.append({"fields": fields, "raw": detail})
                pc = int(node.get('pageCount') or 0)
                if pc and page >= pc:
                    break
                page += 1

            base = f"{dataset}_{code_prefix}"
            outs = export_records(all_recs, export_dir, base, cfg.get("export_format","excel"))
            rprint(f"  -> 导出完成: {outs}")
            results.append({"job": job, "export": outs, "count": len(all_recs)})
    return results

def main():
    parser = argparse.ArgumentParser(description="NMPA 药品信息爬虫（默认 browser 引擎）")
    parser.add_argument("-c","--config", default="config.yaml", help="配置文件路径")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    try:
        results = run_jobs(cfg)
        rprint("[bold green]全部任务完成[/]")
        for r in results:
            rprint(f"  -> {r['job']}  数量: {r['count']}  导出: {r['export']}")
    except Exception as e:
        rprint(f"[bold red]运行失败[/]: {e}")
        traceback.print_exc()
        sys.exit(2)

if __name__ == "__main__":
    main()
