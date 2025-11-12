import hashlib
import logging
import random
import time
import urllib.parse
from dataclasses import dataclass
from datetime import timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, Mapping, MutableMapping, Optional

import requests
from requests import Response, Session

APP_SECRET = "nmpasecret2020"
BASE_URL = "https://www.nmpa.gov.cn/datasearch"
REFERER = "https://www.nmpa.gov.cn/datasearch/search-result.html"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
    "Referer": REFERER,
    "Origin": "https://www.nmpa.gov.cn",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "sec-ch-ua": '\"Google Chrome\";v=\"123\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"123\"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '\"Windows\"',
}
CONFIG_HEADERS = {
    "User-Agent": DEFAULT_HEADERS["User-Agent"],
    "Accept": "*/*",
    "Accept-Language": DEFAULT_HEADERS["Accept-Language"],
    "Connection": "keep-alive",
    "Referer": REFERER,
}
WARMUP_URLS = [
    "https://www.nmpa.gov.cn/",
    "https://www.nmpa.gov.cn/yaopin/",
    REFERER,
]
BLOCK_COOLDOWN_RANGE = (600.0, 800.0)
BLOCK_RETRY_LIMIT = 19
logger = logging.getLogger("nmpa.client")


def _sorted_query_string(pairs: Mapping[str, Any]) -> str:
    items: list[str] = []
    for key, value in pairs.items():
        if value is None or value == "":
            continue
        items.append(f"{key}={value}")
    return "&".join(sorted(items))


def _json_md5_to_str(sorted_query: str) -> str:
    payload = f"{sorted_query}&{APP_SECRET}" if sorted_query else APP_SECRET
    encoded = urllib.parse.quote(payload, safe="-_.!~*'()")
    encoded = (
        encoded.replace("!", "%21")
        .replace("(", "%28")
        .replace(")", "%29")
        .replace("~", "%7E")
    )
    return hashlib.md5(encoded.encode("utf-8")).hexdigest()


@dataclass
class SignedRequest:
    sign: str
    timestamp: int
    raw: str


class NMPAClient:
    """NMPA 网站请求客户端。"""

    def __init__(
        self,
        *,
        base_url: str = BASE_URL,
        session: Optional[Session] = None,
        token: Optional[str] = None,
        timestamp_ttl: float = 1.5,
        visual_device: str = "pc",
        warmup_on_init: bool = False,
        warmup_delay: float = 0.6,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.session: Session = session or requests.Session()
        self.session.cookies.set(
            "visualdevice", visual_device, domain="www.nmpa.gov.cn", path="/"
        )
        self.token = token
        self._timestamp_ttl = max(timestamp_ttl, 0.0)
        self._cached_timestamp: Optional[int] = None
        self._timestamp_fetched_at: Optional[float] = None
        self._warmup_delay = max(warmup_delay, 0.0)
        self._warmed = False
        if warmup_on_init:
            self.warmup()

    def set_token(self, token: Optional[str]) -> None:
        self.token = token

    def warmup(self, delay: Optional[float] = None, retries: int = 6) -> None:
        if self._warmed:
            return
        wait = self._warmup_delay if delay is None else max(delay, 0.0)
        for url in WARMUP_URLS:
            attempt = 0
            while attempt < retries:
                attempt += 1
                try:
                    resp = self.session.get(
                        url,
                        headers=DEFAULT_HEADERS,
                        timeout=10,
                        allow_redirects=True,
                    )
                    if resp.status_code in {403, 412}:
                        cookies = self.session.cookies.get_dict()
                        if "acw_tc" in cookies:
                            break
                        cooldown = wait or 0.8
                        logging.getLogger("nmpa.client").warning(
                            "warmup %s 返回 %d，%.1f 秒后重试", url, resp.status_code, cooldown
                        )
                        time.sleep(cooldown)
                        continue
                    resp.raise_for_status()
                    break
                except requests.HTTPError as exc:
                    if (
                        getattr(exc.response, "status_code", None) in {403, 412}
                        and attempt < retries
                    ):
                        cooldown = wait or 0.8
                        logging.getLogger("nmpa.client").warning(
                            "warmup %s 捕获 %d，%.1f 秒后重试", url, exc.response.status_code, cooldown
                        )
                        time.sleep(cooldown)
                        continue
                    raise
            if wait:
                time.sleep(wait)
        self._warmed = True

    def get(
        self,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: float = 10.0,
        retries: int = 2,
    ) -> Response:
        return self._request(
            "GET",
            path,
            params=params,
            headers=headers,
            timeout=timeout,
            retries=retries,
        )

    def post_json(
        self,
        path: str,
        *,
        json: Optional[MutableMapping[str, Any]] = None,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: float = 10.0,
        retries: int = 2,
    ) -> Response:
        request_headers = {"Content-Type": "application/json;charset=UTF-8"}
        if headers:
            request_headers.update(headers)
        return self._request(
            "POST",
            path,
            params=params,
            json=json or {},
            headers=request_headers,
            timeout=timeout,
            retries=retries,
        )

    def _ensure_session_ready(self) -> None:
        if not self._warmed:
            self.warmup()

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Optional[MutableMapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: float,
        retries: int,
    ) -> Response:
        self._ensure_session_ready()
        params = dict(params or {})
        attempt = 0
        last_exc: Optional[Exception] = None
        while attempt <= retries:
            attempt += 1
            signed = self._prepare_signature(params)
            req_headers = self._build_headers(signed, headers)
            url = self._resolve(path)
            try:
                request_kwargs: Dict[str, Any] = {
                    "params": params,
                    "headers": req_headers,
                    "timeout": timeout,
                }
                if json is not None:
                    request_kwargs["json"] = json
                response = self.session.request(method, url, **request_kwargs)
                if response.status_code == 412 and attempt <= retries:
                    self._invalidate_timestamp()
                    time.sleep(0.8)
                    continue
                if response.status_code == 403:
                    self._invalidate_timestamp()
                    if attempt <= retries:
                        wait_seconds = random.uniform(*BLOCK_COOLDOWN_RANGE)
                        logger.warning(
                            "【客户端】%s %s 返回 403，第 %d/%d 次冷却 %.1f 秒",
                            method,
                            path,
                            attempt,
                            retries + 1,
                            wait_seconds,
                        )
                        time.sleep(wait_seconds)
                        continue
                response.raise_for_status()
                return response
            except requests.HTTPError as exc:
                status = getattr(exc.response, "status_code", None)
                if status == 412 and attempt <= retries:
                    self._invalidate_timestamp()
                    last_exc = exc
                    time.sleep(0.8)
                    continue
                if status == 403 and attempt <= retries:
                    self._invalidate_timestamp()
                    wait_seconds = random.uniform(*BLOCK_COOLDOWN_RANGE)
                    logger.warning(
                        "【客户端】请求 %s %s 捕获 403，第 %d/%d 次冷却 %.1f 秒",
                        method,
                        path,
                        attempt,
                        retries + 1,
                        wait_seconds,
                    )
                    last_exc = exc
                    time.sleep(wait_seconds)
                    continue
                raise
            except Exception as exc:
                last_exc = exc
                if attempt <= retries:
                    time.sleep(0.8)
                    continue
                raise
        assert last_exc is not None
        raise last_exc

    def _prepare_signature(self, params: Mapping[str, Any]) -> SignedRequest:
        timestamp = self.fetch_server_timestamp()
        sign_payload: Dict[str, Any] = {
            key: value for key, value in params.items() if value not in ("", None)
        }
        sign_payload["timestamp"] = timestamp
        sorted_query = _sorted_query_string(sign_payload)
        sign = _json_md5_to_str(sorted_query)
        return SignedRequest(sign=sign, timestamp=timestamp, raw=sorted_query)

    def _build_headers(
        self,
        signed: SignedRequest,
        extra: Optional[Mapping[str, str]],
    ) -> Dict[str, str]:
        headers = dict(DEFAULT_HEADERS)
        headers.update(
            {
                "timestamp": str(signed.timestamp),
                "sign": signed.sign,
            }
        )
        if self.token:
            headers.setdefault("token", self.token)
        if extra:
            headers.update(extra)
        return headers

    def _resolve(self, path: str) -> str:
        path = path.strip()
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"

    def fetch_server_timestamp(self, *, force: bool = False) -> int:
        self._ensure_session_ready()
        now = time.time()
        if (
            not force
            and self._cached_timestamp is not None
            and self._timestamp_fetched_at is not None
            and now - self._timestamp_fetched_at <= self._timestamp_ttl
        ):
            return self._cached_timestamp

        url = self._resolve("/config/DATE.json")
        params = {"date": int(now * 1000)}
        attempts = 0
        while True:
            try:
                resp = self.session.get(url, params=params, headers=CONFIG_HEADERS, timeout=10)
                if resp.status_code == 403:
                    if attempts >= BLOCK_RETRY_LIMIT:
                        resp.raise_for_status()
                    wait_seconds = random.uniform(*BLOCK_COOLDOWN_RANGE)
                    logger.warning(
                        "【客户端】DATE.json 返回 403，第 %d/%d 次冷却 %.1f 秒",
                        attempts + 1,
                        BLOCK_RETRY_LIMIT + 1,
                        wait_seconds,
                    )
                    time.sleep(wait_seconds)
                    attempts += 1
                    continue
                resp.raise_for_status()
                break
            except requests.HTTPError as exc:
                status = getattr(exc.response, "status_code", None)
                if status in (403, 412) and attempts < BLOCK_RETRY_LIMIT:
                    wait_seconds = random.uniform(*BLOCK_COOLDOWN_RANGE)
                    logger.warning(
                        "【客户端】DATE.json 捕获 %s，第 %d/%d 次冷却 %.1f 秒",
                        status,
                        attempts + 1,
                        BLOCK_RETRY_LIMIT + 1,
                        wait_seconds,
                    )
                    time.sleep(wait_seconds)
                    attempts += 1
                    continue
                raise
        date_header = resp.headers.get("Date")
        if not date_header:
            raise RuntimeError("NMPA response missing Date header")
        dt = parsedate_to_datetime(date_header)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        timestamp = int(dt.timestamp() * 1000)
        self._cached_timestamp = timestamp
        self._timestamp_fetched_at = now
        return timestamp

    def _invalidate_timestamp(self) -> None:
        self._cached_timestamp = None
        self._timestamp_fetched_at = None


__all__ = ["NMPAClient", "SignedRequest"]
