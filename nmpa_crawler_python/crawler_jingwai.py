import argparse
import json
import logging
import random
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import requests

from client import NMPAClient

IMPORTED_ITEM_ID = "ff80808183cad7500184088665711800"

OUTPUT_ROOT = Path("outputs_jingwai")
DATASET_DIR = OUTPUT_ROOT / "datasets"
DETAIL_DIR = OUTPUT_ROOT / "details"
STATE_PATH = OUTPUT_ROOT / "run_state.json"

PAGE_DELAY_RANGE = (1.8, 3.2)
CATEGORY_DELAY_RANGE = (30.0, 48.0)
DETAIL_BACKOFF_RANGE = (18.0, 30.0)
BLOCK_COOLDOWN_RANGE = (600.0, 800.0)
BLOCK_RETRY_LIMIT = 19
RECORD_DELAY_RANGE = (0.08, 0.18)

LOGGER = logging.getLogger("nmpa.jingwai")


def _sleep(range_pair: Optional[tuple[float, float]]) -> None:
    if not range_pair:
        return
    low, high = range_pair
    if high <= low:
        time.sleep(max(0.0, low))
    else:
        time.sleep(random.uniform(low, high))


def _handle_block(reason: str) -> None:
    wait_seconds = random.uniform(*BLOCK_COOLDOWN_RANGE)
    LOGGER.warning("%s，等待 %.1f 秒后继续", reason, wait_seconds)
    time.sleep(wait_seconds)


def _load_existing(category_prefix: str) -> Tuple[set[str], Dict[str, int]]:
    seen_codes: set[str] = set()
    segment_counts: Dict[str, int] = {}
    for segment_dir in DATASET_DIR.glob("国药准字*"):
        if not segment_dir.is_dir():
            continue
        if not segment_dir.name.startswith(category_prefix):
            continue
        files = sorted(segment_dir.glob("*.jsonl"))
        segment_counts[segment_dir.name] = len(files)
        for file_path in files:
            try:
                with file_path.open("r", encoding="utf-8") as handle:
                    for line in handle:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        code = (record.get("code") or "").strip()
                        if code:
                            seen_codes.add(code)
            except Exception as exc:  # noqa: BLE001
                LOGGER.warning("读取 %s 失败：%s", file_path, exc)
    return seen_codes, segment_counts


def _write_segment_page(segment_dir: Path, segment: str, index: int, entries: List[Dict[str, object]]) -> None:
    segment_dir.mkdir(parents=True, exist_ok=True)
    file_path = segment_dir / f"{segment}_{index:03d}.jsonl"
    with file_path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            serialized = json.dumps(entry, ensure_ascii=False)
            handle.write(serialized + "\n")


def _persist_detail(record_id: str, payload: Dict[str, object]) -> Path:
    DETAIL_DIR.mkdir(parents=True, exist_ok=True)
    path = DETAIL_DIR / f"{record_id}.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False)
    return path


def _load_detail(record_id: str) -> Optional[Dict[str, object]]:
    path = DETAIL_DIR / f"{record_id}.json"
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError:
        LOGGER.warning("详情缓存 %s 格式异常，重新请求。", path)
        return None


def _normalize_entry(detail: Dict[str, object], record: Dict[str, object]) -> Dict[str, object]:
    raw = (detail.get("f1") or detail.get("f0") or record.get("f0") or "").strip()
    if raw.startswith("国药准字"):
        raw = raw[len("国药准字") :]
    return {
        "code": raw,
        "product_zh": (detail.get("f14") or record.get("f1") or "").strip(),
        "product_en": (detail.get("f15") or "").strip(),
        "commodity_zh": (detail.get("f16") or "").strip(),
        "commodity_en": (detail.get("f17") or "").strip(),
    }


def _segment_name(raw_code: str, *, fallback_prefix: str) -> str:
    if not raw_code.startswith("国药准字"):
        raw_code = f"国药准字{raw_code}"
    stripped = raw_code[len("国药准字") :]
    letters = "".join(ch for ch in stripped if ch.isalpha())
    digits = "".join(ch for ch in stripped if ch.isdigit())
    segment_digits = digits[:3] if digits else ""
    fallback_letters = fallback_prefix[len("国药准字") :] if fallback_prefix.startswith("国药准字") else fallback_prefix
    prefix = letters or fallback_letters
    return f"国药准字{prefix}{segment_digits}" if (prefix or segment_digits) else raw_code


@dataclass
class CategoryConfig:
    name: str
    search_value: str
    output_filename: str


CATEGORIES: List[CategoryConfig] = [
    CategoryConfig(name="进口H", search_value="国药准字H", output_filename="进口H.jsonl"),
    CategoryConfig(name="进口S", search_value="国药准字S", output_filename="进口S.jsonl"),
]


class RunStateManager:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.data: Dict[str, Dict[str, Dict[str, object]]] = {"categories": {}}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                obj = json.load(handle)
            if isinstance(obj, dict):
                self.data = obj
                self.data.setdefault("categories", {})
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("状态文件 %s 加载失败：%s，使用空状态。", self.path, exc)
            self.data = {"categories": {}}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as handle:
            json.dump(self.data, handle, ensure_ascii=False, indent=2)
        tmp.replace(self.path)

    def start(self, name: str) -> Dict[str, object]:
        entry = self.data["categories"].get(name)
        now = time.time()
        if not entry:
            entry = {"status": "pending", "next_page": 1, "total_pages": None, "updated": now}
        else:
            entry["status"] = "in_progress"
            entry.setdefault("next_page", 1)
        entry["updated"] = now
        self.data["categories"][name] = entry
        self._save()
        return entry

    def update_page(self, name: str, next_page: int, *, total_pages: Optional[int] = None) -> None:
        entry = self.data["categories"].setdefault(name, {})
        entry["next_page"] = next_page
        if total_pages is not None:
            entry["total_pages"] = total_pages
        entry["status"] = "in_progress"
        entry["updated"] = time.time()
        self._save()

    def mark_completed(self, name: str) -> None:
        entry = self.data["categories"].setdefault(name, {})
        entry["status"] = "completed"
        entry["next_page"] = None
        entry["updated"] = time.time()
        self._save()

    def is_completed(self, name: str) -> bool:
        entry = self.data["categories"].get(name)
        return bool(entry and entry.get("status") == "completed")


def fetch_page(
    client: NMPAClient,
    *,
    search_value: str,
    page_num: int,
    page_size: int = 20,
) -> Dict[str, object]:
    for attempt in range(BLOCK_RETRY_LIMIT + 1):
        try:
            response = client.get(
                "/data/nmpadata/search",
                params={
                    "itemId": IMPORTED_ITEM_ID,
                    "searchValue": search_value,
                    "pageNum": page_num,
                    "pageSize": page_size,
                    "isSenior": "N",
                },
            )
            payload = response.json().get("data", {})
            if not payload:
                raise RuntimeError("列表响应缺失 data 字段")
            return payload
        except requests.HTTPError as exc:
            status = getattr(exc.response, "status_code", None)
            if status in (403, 412):
                _handle_block(f"{search_value} 第 {page_num} 页请求返回 {status}")
                continue
            LOGGER.warning("%s 第 %d 页请求异常 (%s)，第 %d 次重试", search_value, page_num, status, attempt + 1)
            _sleep(DETAIL_BACKOFF_RANGE)
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("%s 第 %d 页请求失败：%s", search_value, page_num, exc)
            _sleep(DETAIL_BACKOFF_RANGE)
    raise RuntimeError(f"{search_value} 第 {page_num} 页重试超限")


def fetch_detail(client: NMPAClient, record_id: str) -> Optional[Dict[str, object]]:
    cached = _load_detail(record_id)
    if cached is not None:
        return cached
    for attempt in range(BLOCK_RETRY_LIMIT + 1):
        try:
            response = client.get(
                "/data/nmpadata/queryDetail",
                params={
                    "id": record_id,
                    "itemId": IMPORTED_ITEM_ID,
                    "isSenior": "N",
                },
                timeout=15.0,
            )
            payload = response.json()
            if payload.get("code") != 200:
                raise RuntimeError(payload.get("message") or "detail code != 200")
            _persist_detail(record_id, payload)
            return payload
        except requests.HTTPError as exc:
            status = getattr(exc.response, "status_code", None)
            if status in (403, 412):
                _handle_block(f"详情 {record_id} 请求返回 {status}")
                continue
            LOGGER.warning("详情 %s 请求异常 (%s)，第 %d 次重试", record_id, status, attempt + 1)
            _sleep(DETAIL_BACKOFF_RANGE)
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("详情 %s 请求失败：%s", record_id, exc)
            _sleep(DETAIL_BACKOFF_RANGE)
    LOGGER.error("详情 %s 重试超限，跳过。", record_id)
    return None


def process_category(
    client: NMPAClient,
    category: CategoryConfig,
    *,
    state_manager: RunStateManager,
) -> None:
    LOGGER.info("【入口】开始处理 %s", category.name)
    state = state_manager.start(category.name)
    next_page = int(state.get("next_page") or 1)
    total_pages = state.get("total_pages")

    prefix = category.search_value.replace("国药准字", "国药准字")
    DATASET_DIR.mkdir(parents=True, exist_ok=True)

    if next_page <= 1:
        for segment_dir in DATASET_DIR.glob(f"{category.search_value}*"):
            if segment_dir.is_dir():
                shutil.rmtree(segment_dir, ignore_errors=True)
        seen_codes: set[str] = set()
        segment_counts: Dict[str, int] = {}
        LOGGER.info("【写入】%s 输出至 %s（覆盖模式）", category.name, DATASET_DIR)
    else:
        seen_codes, segment_counts = _load_existing(category.search_value)
        LOGGER.info(
            "【写入】%s 续跑模式，已存在 %d 条记录，涉及 %d 个分段。",
            category.name,
            len(seen_codes),
            len(segment_counts),
        )
        if not segment_counts and not seen_codes:
            LOGGER.warning("【续跑】%s 未发现已有数据，重置从第 1 页重新抓取。", category.name)
            next_page = 1
            state_manager.update_page(category.name, 1, total_pages=None)

    total_written = len(seen_codes)
    page_num = next_page

    while True:
        payload = fetch_page(client, search_value=category.search_value, page_num=page_num)
        records = payload.get("list") or []
        if not records:
            LOGGER.info("【列表】%s 第 %d 页无数据，提前结束。", category.name, page_num)
            break

        if total_pages is None:
            effective_page_size = payload.get("pageSize") or 20
            total = payload.get("total") or len(records)
            total_pages = int((total + effective_page_size - 1) // effective_page_size)
            LOGGER.info("【计划】%s 共 %d 条数据，预计 %d 页。", category.name, total, total_pages)
            state_manager.update_page(category.name, page_num, total_pages=total_pages)

        segment_batches: Dict[str, List[Dict[str, object]]] = {}

        for record in records:
            record_id = record.get("f3")
            if not record_id:
                continue
            detail_payload = fetch_detail(client, record_id)
            if not detail_payload:
                continue
            detail = detail_payload.get("data", {}).get("detail", {})
            entry = _normalize_entry(detail, record)
            code = entry["code"]
            if not code or code in seen_codes:
                continue
            raw_code = detail.get("f0") or record.get("f0") or code
            segment = _segment_name(raw_code, fallback_prefix=category.search_value)
            segment_batches.setdefault(segment, []).append(entry)
            seen_codes.add(code)
            _sleep(RECORD_DELAY_RANGE)

        for segment, entries in segment_batches.items():
            segment_dir = DATASET_DIR / segment
            next_index = segment_counts.get(segment, 0) + 1
            _write_segment_page(segment_dir, segment, next_index, entries)
            segment_counts[segment] = next_index
            total_written += len(entries)

        LOGGER.info("【进度】%s 完成第 %d 页，累计写入 %d 条记录。", category.name, page_num, total_written)

        if total_pages is not None and page_num >= total_pages:
            break

        page_num += 1
        state_manager.update_page(category.name, page_num, total_pages=total_pages)
        _sleep(PAGE_DELAY_RANGE)

    state_manager.mark_completed(category.name)
    LOGGER.info("【完成】%s 共写入 %d 条记录。", category.name, total_written)
    _sleep(CATEGORY_DELAY_RANGE)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NMPA 境外药品数据爬虫")
    parser.add_argument(
        "--category",
        action="append",
        dest="categories",
        choices=["H", "S"],
        help="指定抓取品种：H（化药）或 S（生物制品），可多次使用；默认全部。",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="日志级别，默认 INFO（可选 DEBUG/INFO/WARNING/ERROR/CRITICAL）。",
    )
    parser.add_argument(
        "--log-file",
        default=None,
        help="可选，日志输出文件。",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="继续上次的 run_state.json 进度（默认即为续跑）。",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="兼容参数（保留，与自动化脚本一致），对本爬虫无影响。",
    )
    return parser.parse_args(argv)


def configure_logging(level: str, log_file: Optional[str]) -> None:
    handlers: List[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    configure_logging(args.log_level, args.log_file)

    if args.categories:
        targets = []
        for letter in args.categories:
            if letter.upper() == "H":
                targets.append(CATEGORIES[0])
            elif letter.upper() == "S":
                targets.append(CATEGORIES[1])
        categories = targets
    else:
        categories = CATEGORIES

    LOGGER.info(
        "启动境外爬虫，目标分类：%s",
        ", ".join(cat.name for cat in categories) if categories else "无",
    )

    client = NMPAClient(warmup_on_init=True, warmup_delay=1.5, timestamp_ttl=60.0)
    state_manager = RunStateManager(STATE_PATH)

    for category in categories:
        if state_manager.is_completed(category.name):
            LOGGER.info("【跳过】%s 已完成，跳过。", category.name)
            continue
        try:
            process_category(client, category, state_manager=state_manager)
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("处理 %s 发生异常，终止。", category.name)
            return 1

    LOGGER.info("全部分类处理完成。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
