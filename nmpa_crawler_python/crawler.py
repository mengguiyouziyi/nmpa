import argparse
import json
import logging
import math
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Set, Tuple

from client import NMPAClient

DOMESTIC_ITEM_ID = "ff80808183cad75001840881f848179f"
PAGE_SIZE = 20
SEGMENT_THRESHOLD = PAGE_SIZE * 10
SEGMENT_MAX_PAGES = 10
SEGMENT_MAX_DEPTH = 8
SEGMENT_DIGITS = "0123456789"

OUTPUT_ROOT = Path("outputs")
DATASET_DIR = OUTPUT_ROOT / "datasets"
DETAIL_DIR = OUTPUT_ROOT / "details"

PAGE_DELAY_RANGE = (1.8, 3.2)
DETAIL_DELAY_RANGE = (2.6, 4.2)
SEGMENT_DELAY_RANGE = (30.0, 48.0)
DETAIL_BACKOFF_RANGE = (18.0, 30.0)

logger = logging.getLogger("nmpa.crawler")


@dataclass
class SegmentResult:
    value: str
    total: int
    page_size: int
    total_pages: int
    depth: int
    first_payload: Dict


def configure_logging(level_str: str) -> None:
    """初始化日志配置。"""
    level = getattr(logging, level_str.upper(), logging.INFO)
    root_logger = logging.getLogger()
    if root_logger.handlers:
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger.setLevel(level)
    logger.debug("日志级别已设置为 %s", logging.getLevelName(level))


def _sleep(range_pair: Tuple[float, float]) -> None:
    low, high = range_pair
    time.sleep(random.uniform(low, high))


def _ensure_directories() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    DETAIL_DIR.mkdir(parents=True, exist_ok=True)


def fetch_first_page(client: NMPAClient, search_value: str, depth: int) -> Optional[SegmentResult]:
    logger.info("【拆分】%s 深度=%d -> 请求第 1 页", search_value, depth)
    params = {
        "itemId": DOMESTIC_ITEM_ID,
        "searchValue": search_value,
        "pageNum": 1,
        "pageSize": PAGE_SIZE,
        "isSenior": "N",
    }
    response = client.get("/data/nmpadata/search", params=params)
    payload = response.json()
    data = payload.get("data") or {}
    total = int(data.get("total") or 0)
    if total <= 0:
        logger.info("【拆分】%s: 无数据，跳过", search_value)
        return None
    page_size = int(data.get("pageSize") or PAGE_SIZE) or PAGE_SIZE
    total_pages = math.ceil(total / max(1, page_size))
    logger.info(
        "【拆分】%s: 总记录=%d, 页数=%d, 实际页大小=%d, 深度=%d",
        search_value,
        total,
        total_pages,
        page_size,
        depth,
    )
    _sleep(PAGE_DELAY_RANGE)
    return SegmentResult(
        value=search_value,
        total=total,
        page_size=page_size,
        total_pages=total_pages,
        depth=depth,
        first_payload=payload,
    )


def segment_queries(
    client: NMPAClient,
    base_value: str,
    *,
    depth: int = 0,
    visited: Optional[Set[str]] = None,
) -> Iterator[SegmentResult]:
    if visited is None:
        visited = set()
    if base_value in visited:
        logger.debug("【拆分】%s: 已处理，跳过重复", base_value)
        return
    visited.add(base_value)
    result = fetch_first_page(client, base_value, depth)
    if result is None:
        return
    can_use_segment = (
        result.total <= SEGMENT_THRESHOLD
        and result.total_pages <= SEGMENT_MAX_PAGES
    )
    reached_depth = depth >= SEGMENT_MAX_DEPTH
    if can_use_segment or reached_depth:
        if reached_depth and not can_use_segment:
            logger.warning(
                "【拆分】%s: 达到最大拆分层级(%d)，仍有 %d 条/ %d 页，直接使用当前段",
                result.value,
                SEGMENT_MAX_DEPTH,
                result.total,
                result.total_pages,
            )
        else:
            logger.info(
                "【拆分】%s: 满足阈值，使用当前段 (记录=%d, 页数=%d, 深度=%d)",
                result.value,
                result.total,
                result.total_pages,
                depth,
            )
        yield result
        return
    if not SEGMENT_DIGITS:
        raise RuntimeError("SEGMENT_DIGITS 为空，无法继续拆分")
    logger.info(
        "【拆分】%s: 需要继续细分 -> 总记录=%d, 页数=%d, 深度=%d",
        result.value,
        result.total,
        result.total_pages,
        depth,
    )
    for digit in SEGMENT_DIGITS:
        next_value = f"{base_value}{digit}"
        yield from segment_queries(
            client,
            next_value,
            depth=depth + 1,
            visited=visited,
        )


def _prepare_segment_output(segment_value: str) -> None:
    segment_dir = DATASET_DIR / segment_value
    if segment_dir.exists():
        for file_path in segment_dir.glob("*.jsonl"):
            file_path.unlink()
    else:
        segment_dir.mkdir(parents=True, exist_ok=True)


def _dataset_page_path(segment_value: str, page_number: int) -> Path:
    filename = f"{segment_value}_{page_number:03d}.jsonl"
    return DATASET_DIR / segment_value / filename


def _write_dataset_records(segment_value: str, page_number: int, records: Sequence[Dict[str, str]]) -> None:
    path = _dataset_page_path(segment_value, page_number)
    if not records:
        logger.warning("【写入】%s 第 %03d 页无有效详情，产生空文件", segment_value, page_number)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    logger.info("【写入】%s 第 %03d 页 -> %d 条记录", segment_value, page_number, len(records))


def _detail_path(record_id: str) -> Path:
    return DETAIL_DIR / f"{record_id}.json"


def _fetch_detail(client: NMPAClient, record_id: str) -> Optional[Dict]:
    params = {"id": record_id, "itemId": DOMESTIC_ITEM_ID, "isSenior": "N"}
    response = client.get("/data/nmpadata/queryDetail", params=params, timeout=15.0, retries=3)
    return response.json()


def _persist_detail(record_id: str, payload: Dict) -> None:
    path = _detail_path(record_id)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False)


def _extract_detail(payload: Dict) -> Optional[Dict]:
    if not isinstance(payload, dict):
        return None
    detail = payload.get("detail")
    if isinstance(detail, dict):
        return detail
    data = payload.get("data")
    if isinstance(data, dict):
        nested = data.get("detail")
        if isinstance(nested, dict):
            return nested
    return None


def _detail_to_entry(detail: Dict) -> Optional[Dict[str, str]]:
    code = (detail.get("f0") or "").strip()
    if not code:
        return None
    return {
        "code": code,
        "zh": (detail.get("f1") or "").strip(),
        "en": (detail.get("f2") or "").strip(),
    }


def fetch_details(client: NMPAClient, records: Sequence[Dict], seen_codes: Set[str]) -> List[Dict[str, str]]:
    dataset_entries: List[Dict[str, str]] = []
    for record in records:
        record_id = record.get("f4") or record.get("id")
        if not record_id:
            continue
        record_id = str(record_id)
        detail_payload: Optional[Dict] = None
        detail_file = _detail_path(record_id)
        if detail_file.exists():
            try:
                with detail_file.open("r", encoding="utf-8") as handle:
                    detail_payload = json.load(handle)
                logger.debug("【详情】%s: 使用本地缓存", record_id)
            except Exception as exc:  # noqa: BLE001
                logger.warning("【详情】%s: 读取缓存失败(%s)，重新请求", record_id, exc)
        if detail_payload is None:
            try:
                detail_payload = _fetch_detail(client, record_id)
                if detail_payload is not None:
                    _persist_detail(record_id, detail_payload)
                _sleep(DETAIL_DELAY_RANGE)
            except Exception as exc:  # noqa: BLE001
                logger.warning("【详情】%s: 请求失败(%s)，执行退避", record_id, exc)
                _sleep(DETAIL_BACKOFF_RANGE)
                continue
        detail = _extract_detail(detail_payload or {})
        if not detail:
            logger.debug("【详情】%s: 无 detail 字段，跳过", record_id)
            continue
        entry = _detail_to_entry(detail)
        if not entry:
            continue
        code = entry["code"]
        if code in seen_codes:
            logger.debug("【详情】%s: 代码 %s 已存在，跳过", record_id, code)
            continue
        seen_codes.add(code)
        dataset_entries.append(entry)
    if dataset_entries:
        logger.info("【详情】本批新增 %d 条有效记录", len(dataset_entries))
    return dataset_entries


def fetch_remaining_pages(client: NMPAClient, segment: SegmentResult, seen_codes: Set[str]) -> int:
    total_written = 0
    for page in range(2, segment.total_pages + 1):
        logger.info(
            "【分页】%s: 请求第 %d/%d 页",
            segment.value,
            page,
            segment.total_pages,
        )
        params = {
            "itemId": DOMESTIC_ITEM_ID,
            "searchValue": segment.value,
            "pageNum": page,
            "pageSize": PAGE_SIZE,
            "isSenior": "N",
        }
        response = client.get("/data/nmpadata/search", params=params)
        payload = response.json()
        records = payload.get("data", {}).get("list", []) or []
        entries = fetch_details(client, records, seen_codes)
        _write_dataset_records(segment.value, page, entries)
        total_written += len(entries)
        _sleep(PAGE_DELAY_RANGE)
    return total_written


def process_segment(client: NMPAClient, segment: SegmentResult) -> int:
    logger.info(
        "【段开始】%s: 总记录=%d, 页数=%d, 深度=%d",
        segment.value,
        segment.total,
        segment.total_pages,
        segment.depth,
    )
    _prepare_segment_output(segment.value)
    seen_codes: Set[str] = set()
    first_records = segment.first_payload.get("data", {}).get("list", []) or []
    entries = fetch_details(client, first_records, seen_codes)
    _write_dataset_records(segment.value, 1, entries)
    total_written = len(entries)
    if segment.total_pages > 1:
        total_written += fetch_remaining_pages(client, segment, seen_codes)
    logger.info("【段完成】%s: 本段共写入 %d 条", segment.value, total_written)
    _sleep(SEGMENT_DELAY_RANGE)
    return total_written


def crawl(
    client: NMPAClient,
    base_queries: Iterable[str],
    *,
    max_segments: Optional[int] = None,
) -> None:
    _ensure_directories()
    processed = 0
    total_records = 0
    for base in base_queries:
        logger.info("【入口】开始处理基础关键词：%s", base)
        for segment in segment_queries(client, base):
            logger.info("【队列】处理分段：%s (总记录=%d)", segment.value, segment.total)
            written = process_segment(client, segment)
            processed += 1
            total_records += written
            if max_segments is not None and processed >= max_segments:
                logger.info(
                    "【终止】达到 max_segments=%d，提前结束。累计段=%d，记录=%d",
                    max_segments,
                    processed,
                    total_records,
                )
                return
    logger.info("【完成】基础关键词全部处理完毕。累计段=%d，记录=%d", processed, total_records)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NMPA 数据抓取脚本（纯 Python 版）")
    parser.add_argument(
        "-q",
        "--query",
        action="append",
        dest="queries",
        help="基础搜索词，可多次指定；默认处理国药准字H",
    )
    parser.add_argument(
        "--max-segments",
        type=int,
        default=None,
        help="最多处理的分段数量，用于测试或限速",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="日志级别，默认 INFO，可选 DEBUG/INFO/WARNING/ERROR/CRITICAL",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    configure_logging(args.log_level)
    base_queries = args.queries or ["国药准字H", "国药准字S"]
    logger.info("【启动】NMPA 爬虫启动，基础关键词=%s", base_queries)
    client = NMPAClient(warmup_on_init=True, warmup_delay=1.5, timestamp_ttl=60.0)
    crawl(client, base_queries, max_segments=args.max_segments)


if __name__ == "__main__":
    main()
