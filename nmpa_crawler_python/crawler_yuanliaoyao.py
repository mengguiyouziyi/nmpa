import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List

import requests

API_URL = "https://www.cde.org.cn/main/xxgk/getYfbListHc"
LIST_PAGE_URL = "https://www.cde.org.cn/main/xxgk/listpage/9f9c74c73e0f8f56a8bfbc646055026d"
PAGE_SIZE = 50
YFB_TYPE = "原料药"

OUTPUT_ROOT = Path("outputs_yuanliaoyao")
OUTPUT_FILE = OUTPUT_ROOT / "原料药.jsonl"
STATE_PATH = OUTPUT_ROOT / "run_state.json"

LOGGER = logging.getLogger("nmpa.yuanliao")


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://www.cde.org.cn",
            "Referer": "https://www.cde.org.cn/main/xxgk/listpage/9f9c74c73e0f8f56a8bfbc646055026d",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/118.0.0.0 Safari/537.36"
            ),
            "X-Requested-With": "XMLHttpRequest",
        }
    )
    session.get(LIST_PAGE_URL, timeout=30)
    return session


def fetch_page(session: requests.Session, page_num: int) -> Dict:
    payload = {
        "pageSize": PAGE_SIZE,
        "pageNum": page_num,
        "yfbType": YFB_TYPE,
        "noticeTag": "0",
        "condition": "",
    }
    resp = session.post(API_URL, data=payload, timeout=30)
    resp.raise_for_status()
    try:
        data = resp.json()
    except ValueError as exc:  # noqa: B904
        LOGGER.error("解析第 %d 页响应失败：%s", page_num, resp.text[:200])
        raise exc
    if data.get("code") != 200:
        raise RuntimeError(data.get("msg") or "unknown error")
    return data.get("data") or {}


def flatten_record(record: Dict) -> Dict[str, str]:
    return {
        "登记号": record.get("djh", ""),
        "品种名称": record.get("drgnamecn", ""),
        "企业名称": record.get("company", ""),
        "企业地址": record.get("regaddress", ""),
        "产品来源": record.get("source", ""),
        "包装规格": record.get("packageform", ""),
        "规格": record.get("specification", record.get("memo", "")),
        "更新日期": record.get("updatedate", ""),
        "与制剂共同审评审批结果": record.get("glypzjspqk", ""),
        "省份": record.get("province", ""),
        "备注": record.get("memo", ""),
    }


def write_jsonl(records: List[Dict]) -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as handle:
        for entry in records:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def save_state(page_num: int, total_pages: int) -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    with STATE_PATH.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "page_num": page_num,
                "total_pages": total_pages,
            },
            handle,
            ensure_ascii=False,
            indent=2,
        )


def crawl_all(session: requests.Session) -> None:
    LOGGER.info("开始抓取原料药信息…")
    all_entries: List[Dict[str, str]] = []
    page_num = 1
    total_pages = None
    while True:
        LOGGER.info("请求第 %d 页", page_num)
        payload = fetch_page(session, page_num)
        records = payload.get("records") or []
        if total_pages is None:
            total = payload.get("total") or len(records)
            total_pages = payload.get("pages") or (
                (total + PAGE_SIZE - 1) // PAGE_SIZE if total else 0
            )
            LOGGER.info("预计总 %d 页，总记录数 %d", total_pages, total)
        if not records:
            break
        for record in records:
            all_entries.append(flatten_record(record))
        save_state(page_num, total_pages)
        if total_pages and page_num >= total_pages:
            break
        page_num += 1
    write_jsonl(all_entries)
    LOGGER.info("抓取完成，共 %d 条记录，输出：%s", len(all_entries), OUTPUT_FILE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="原料药列表抓取脚本")
    parser.add_argument("--log-level", default="INFO", help="日志级别，默认 INFO")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    configure_logging(args.log_level)
    session = create_session()
    try:
        crawl_all(session)
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("抓取失败：%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
