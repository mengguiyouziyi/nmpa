# -*- coding: utf-8 -*-
"""
实验性 HTTP 引擎：仅在您具备 sign/params 加密算法时使用。
默认请使用 browser 引擎，无需逆向。
"""
import os, json, subprocess, tempfile
from typing import Any, Dict, List
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

class NMPAHttpEngine:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.client = httpx.Client(http2=False, timeout=30.0)

    def _node(self) -> str:
        return self.cfg.get("http_engine", {}).get("node_path", "node")

    def _sign_js(self) -> str:
        return self.cfg.get("http_engine", {}).get("sign_js", "http_engine/nmpa_js/main.js")

    def gen_sign(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用外部 NodeJS 实现（请参考 http_engine/nmpa_js/README.md）
        返回: {'sign': 'xxx', 'timestamp': 1710000000000}
        """
        js_path = self._sign_js()
        if not os.path.exists(js_path):
            raise RuntimeError(f"缺少 sign JS 文件: {js_path}")
        data = json.dumps({"url": url, "params": params}, ensure_ascii=False)
        out = subprocess.check_output([self._node(), js_path, data], text=True)
        return json.loads(out.strip())

    @retry(wait=wait_exponential_jitter(initial=1, max=5), stop=stop_after_attempt(3))
    def search(self, item_id: str, search_value: str, page_num: int, page_size: int) -> Dict[str, Any]:
        url = "https://www.nmpa.gov.cn/datasearch/data/nmpadata/search"
        params = {
            "itemId": item_id,
            "isSenior": "N",
            "searchValue": search_value,
            "pageNum": page_num,
            "pageSize": page_size,
            "timestamp": int(__import__("time").time() * 1000)
        }
        sign = self.gen_sign(url, params)
        headers = {
            "Referer": "https://www.nmpa.gov.cn/datasearch/search-result.html",
            "User-Agent": "Mozilla/5.0",
            "timestamp": str(sign.get("timestamp")),
            "sign": sign.get("sign", ""),
            "token": "false",
            "Accept": "application/json, text/plain, */*"
        }
        r = self.client.get(url, params=params, headers=headers)
        r.raise_for_status()
        return r.json()

    @retry(wait=wait_exponential_jitter(initial=1, max=5), stop=stop_after_attempt(3))
    def detail(self, item_id: str, doc_id: str) -> Dict[str, Any]:
        url = "https://www.nmpa.gov.cn/datasearch/data/nmpadata/queryDetail"
        params = {
            "itemId": item_id,
            "id": doc_id,
            "timestamp": int(__import__("time").time() * 1000)
        }
        sign = self.gen_sign(url, params)
        headers = {
            "Referer": "https://www.nmpa.gov.cn/datasearch/search-result.html",
            "User-Agent": "Mozilla/5.0",
            "timestamp": str(sign.get("timestamp")),
            "sign": sign.get("sign", ""),
            "token": "false",
            "Accept": "application/json, text/plain, */*"
        }
        r = self.client.get(url, params=params, headers=headers)
        r.raise_for_status()
        return r.json()
