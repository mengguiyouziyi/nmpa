# -*- coding: utf-8 -*-
import json, os, time, random, urllib.parse
from typing import Any, Dict, List
from seleniumwire import webdriver  # 用于拦截网络请求(可调试)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

from utils import sleep_jitter, deep_find_item_id, extract_required_fields

NMPA_BASE = "https://www.nmpa.gov.cn"

class NMPABrowserCrawler:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.driver = None

    def _build_driver(self):
        opts = uc.ChromeOptions()
        if self.cfg.get("headless", True):
            opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        # 代理
        proxy_cfg = self.cfg.get("proxy") or {}
        http_proxy = proxy_cfg.get("http")
        https_proxy = proxy_cfg.get("https")
        seleniumwire_options = {}
        if http_proxy or https_proxy:
            seleniumwire_options["proxy"] = {"http": http_proxy, "https": https_proxy}

        self.driver = uc.Chrome(options=opts, seleniumwire_options=seleniumwire_options)

    def _exec_async(self, script: str, timeout: int = 30):
        """
        执行带回调的异步 JS（使用 axios/fetch 由站点本身进行加密签名），返回其结果。
        """
        cb_script = f"""
            const done = arguments[arguments.length - 1];
            (async () => {{
                try {{
                    {script}
                }} catch(err) {{
                    done({{error: String(err)}});
                }}
            }})();
        """
        return self.driver.execute_async_script(cb_script)

    def _wait_axios(self, timeout: int = 20):
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script("return !!window.axios;")
        )

    def start(self):
        self._build_driver()
        self.driver.get(f"{NMPA_BASE}/datasearch/home-index.html")
        self._wait_axios()

    def stop(self):
        try:
            if self.driver:
                self.driver.quit()
        except Exception:
            pass

    def get_item_ids(self) -> Dict[str, str]:
        """
        优先从 NMPA_DATA.json 动态获取 “境内生产药品 / 境外生产药品” itemId
        """
        data = self._exec_async("""
            const url = '/datasearch/config/NMPA_DATA.json?date=' + Date.now();
            const resp = await axios.get(url);
            done(resp.data);
        """, timeout=40)
        if isinstance(data, dict) and data.get("error"):
            raise RuntimeError("读取 NMPA_DATA.json 失败: " + data["error"])

        domestic_id = deep_find_item_id(data, "境内生产药品") or ""
        imported_id = deep_find_item_id(data, "境外生产药品") or ""

        # 回退静态映射
        if not domestic_id or not imported_id:
            try:
                with open("static_item_ids.json", "r", encoding="utf-8") as f:
                    static_map = json.load(f)
                domestic_id = domestic_id or static_map.get("domestic", "")
                imported_id = imported_id or static_map.get("imported", "")
            except Exception:
                pass

        return {"domestic": domestic_id, "imported": imported_id}

    def search_once(self, item_id: str, search_value: str, page_num: int, page_size: int) -> Dict[str, Any]:
        """
        使用站点自身 axios 请求 /datasearch/data/nmpadata/search
        让前端自动处理 sign/token/参数加密等。
        """
        js = f"""
            const url = '/datasearch/data/nmpadata/search';
            const params = {{
                itemId: {json.dumps(item_id)},
                isSenior: 'N',
                searchValue: {json.dumps(search_value)},
                pageNum: {page_num},
                pageSize: {page_size},
                timestamp: Date.now()
            }};
            const resp = await axios.get(url, {{ params }});
            done(resp.data);
        """
        data = self._exec_async(js, timeout=60)
        return data

    def fetch_detail(self, item_id: str, doc_id: str) -> Dict[str, Any]:
        js = f"""
            const url = '/datasearch/data/nmpadata/queryDetail';
            const params = {{
                itemId: {json.dumps(item_id)},
                id: {json.dumps(doc_id)},
                timestamp: Date.now()
            }};
            const resp = await axios.get(url, {{ params }});
            done(resp.data);
        """
        data = self._exec_async(js, timeout=60)
        return data

    def crawl_job(self, dataset: str, code_prefix: str, out_dir: str) -> List[Dict[str, Any]]:
        item_ids = self.get_item_ids()
        item_id = item_ids.get(dataset, "")
        if not item_id:
            raise RuntimeError(f"未能找到 {dataset} 的 itemId，请检查站点或更新 static_item_ids.json")

        max_pages = int(self.cfg.get("max_pages", 50))
        page_size = int(self.cfg.get("page_size", 30))

        all_records: List[Dict[str, Any]] = []
        for page in range(1, max_pages + 1):
            data = self.search_once(item_id, code_prefix, page, page_size)
            # 常见结构：{'code':200, 'data': {'list': [...], 'pageCount': N, 'totalCount': M}} 或者顶层直接包含 list
            if not data:
                break
            node = data.get('data', data) if isinstance(data, dict) else {}
            lst = node.get('list') or node.get('resultList') or []
            if not lst:
                # 有些返回把数据放在 rows
                lst = node.get('rows') or []
            if not lst:
                break

            for row in lst:
                doc_id = str(row.get('id') or row.get('ID') or row.get('docId') or row.get('dataId') or '')
                if not doc_id:
                    continue
                detail = self.fetch_detail(item_id, doc_id)
                fields = extract_required_fields(detail, dataset)
                all_records.append({"fields": fields, "raw": detail})

            # 简单的翻页终止判断
            page_count = int(node.get('pageCount') or 0)
            if page_count and page >= page_count:
                break

            sleep_jitter(self.cfg.get("delay_min_ms", 600), self.cfg.get("delay_max_ms", 1500))

        return all_records
