# -*- coding: utf-8 -*-
"""
代理管理模块 - 支持多种代理轮换策略
包括代理池、健康检查、故障转移等功能
"""
import random
import time
import threading
import requests
import json
import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

class ProxyType(Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"

class ProxyStatus(Enum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    BANNED = "banned"
    RATE_LIMITED = "rate_limited"

@dataclass
class ProxyInfo:
    """代理信息数据结构"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    proxy_type: ProxyType = ProxyType.HTTP
    status: ProxyStatus = ProxyStatus.UNKNOWN
    success_count: int = 0
    failure_count: int = 0
    last_used: float = 0.0
    last_check: float = 0.0
    response_time: float = 0.0
    country: Optional[str] = None
    provider: Optional[str] = None

    def get_proxy_url(self) -> str:
        """获取代理URL"""
        if self.username and self.password:
            auth = f"{self.username}:{self.password}@"
        else:
            auth = ""

        return f"{self.proxy_type.value}://{auth}{self.host}:{self.port}"

    def get_dict(self) -> Dict[str, str]:
        """获取requests使用的代理字典"""
        proxy_url = self.get_proxy_url()
        if self.proxy_type == ProxyType.HTTP:
            return {
                "http": proxy_url,
                "https": proxy_url
            }
        else:
            return {
                "http": proxy_url,
                "https": proxy_url
            }

class ProxyPool:
    """代理池管理器"""

    def __init__(self, cfg: Dict[str, Any] = None):
        self.cfg = cfg or {}
        self.proxies: List[ProxyInfo] = []
        self.lock = threading.Lock()
        self.check_interval = self.cfg.get("proxy", {}).get("check_interval", 300)  # 5分钟
        self.max_failure_rate = self.cfg.get("proxy", {}).get("max_failure_rate", 0.3)
        self.timeout = self.cfg.get("proxy", {}).get("timeout", 10)
        self.test_urls = self.cfg.get("proxy", {}).get("test_urls", [
            "http://httpbin.org/ip",
            "https://api.ipify.org?format=json",
            "https://httpbin.org/headers"
        ])

        # 加载初始代理
        self._load_proxies()

        # 启动健康检查线程
        self._start_health_check()

    def _load_proxies(self):
        """加载代理配置"""
        proxy_cfg = self.cfg.get("proxy", {})

        # 从配置文件加载
        if "proxies" in proxy_cfg:
            for proxy_data in proxy_cfg["proxies"]:
                proxy = ProxyInfo(
                    host=proxy_data["host"],
                    port=proxy_data["port"],
                    username=proxy_data.get("username"),
                    password=proxy_data.get("password"),
                    proxy_type=ProxyType(proxy_data.get("type", "http")),
                    country=proxy_data.get("country"),
                    provider=proxy_data.get("provider")
                )
                self.proxies.append(proxy)

        # 从API加载
        if "api_url" in proxy_cfg:
            self._load_from_api(proxy_cfg["api_url"])

        # 从文件加载
        if "file_path" in proxy_cfg:
            self._load_from_file(proxy_cfg["file_path"])

        logger.info(f"加载了 {len(self.proxies)} 个代理")

    def _load_from_api(self, api_url: str):
        """从API加载代理"""
        try:
            headers = self.cfg.get("proxy", {}).get("api_headers", {})
            response = requests.get(api_url, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            if isinstance(data, list):
                for proxy_data in data:
                    proxy = ProxyInfo(
                        host=proxy_data["host"],
                        port=proxy_data["port"],
                        username=proxy_data.get("username"),
                        password=proxy_data.get("password"),
                        proxy_type=ProxyType(proxy_data.get("type", "http")),
                        country=proxy_data.get("country"),
                        provider=proxy_data.get("provider")
                    )
                    self.proxies.append(proxy)

        except Exception as e:
            logger.error(f"从API加载代理失败: {e}")

    def _load_from_file(self, file_path: str):
        """从文件加载代理"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.json'):
                    data = json.load(f)
                    for proxy_data in data:
                        proxy = ProxyInfo(
                            host=proxy_data["host"],
                            port=proxy_data["port"],
                            username=proxy_data.get("username"),
                            password=proxy_data.get("password"),
                            proxy_type=ProxyType(proxy_data.get("type", "http")),
                            country=proxy_data.get("country"),
                            provider=proxy_data.get("provider")
                        )
                        self.proxies.append(proxy)
                else:
                    # 纯文本格式 host:port:username:password
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = line.split(':')
                            if len(parts) >= 2:
                                proxy = ProxyInfo(
                                    host=parts[0],
                                    port=int(parts[1]),
                                    username=parts[2] if len(parts) > 2 else None,
                                    password=parts[3] if len(parts) > 3 else None
                                )
                                self.proxies.append(proxy)

        except Exception as e:
            logger.error(f"从文件加载代理失败: {e}")

    def _start_health_check(self):
        """启动健康检查线程"""
        def health_check_worker():
            while True:
                try:
                    self._check_all_proxies()
                    time.sleep(self.check_interval)
                except Exception as e:
                    logger.error(f"健康检查失败: {e}")
                    time.sleep(60)  # 出错后等待1分钟再重试

        thread = threading.Thread(target=health_check_worker, daemon=True)
        thread.start()

    def _check_all_proxies(self):
        """检查所有代理的健康状态"""
        logger.info("开始代理健康检查")

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for proxy in self.proxies:
                future = executor.submit(self._check_proxy_health, proxy)
                futures.append(future)

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"代理检查异常: {e}")

        healthy_count = len([p for p in self.proxies if p.status == ProxyStatus.HEALTHY])
        logger.info(f"代理健康检查完成，健康代理数: {healthy_count}/{len(self.proxies)}")

    def _check_proxy_health(self, proxy: ProxyInfo) -> bool:
        """检查单个代理的健康状态"""
        start_time = time.time()

        try:
            # 测试多个URL以提高准确性
            success_count = 0
            total_time = 0

            for url in self.test_urls[:2]:  # 只测试前2个URL
                try:
                    response = requests.get(
                        url,
                        proxies=proxy.get_dict(),
                        timeout=self.timeout,
                        headers={"User-Agent": "Mozilla/5.0"}
                    )
                    if response.status_code == 200:
                        success_count += 1
                        total_time += response.elapsed.total_seconds()
                except Exception:
                    continue

            # 更新代理状态
            with self.lock:
                proxy.last_check = time.time()

                if success_count > 0:
                    proxy.status = ProxyStatus.HEALTHY
                    proxy.response_time = total_time / success_count
                    proxy.success_count += 1
                else:
                    proxy.failure_count += 1
                    failure_rate = proxy.failure_count / (proxy.success_count + proxy.failure_count)

                    if failure_rate > self.max_failure_rate:
                        proxy.status = ProxyStatus.UNHEALTHY
                    else:
                        proxy.status = ProxyStatus.UNKNOWN

            return success_count > 0

        except Exception as e:
            with self.lock:
                proxy.last_check = time.time()
                proxy.failure_count += 1
                proxy.status = ProxyStatus.UNHEALTHY

            logger.debug(f"代理 {proxy.host}:{proxy.port} 健康检查失败: {e}")
            return False

    def get_best_proxy(self, exclude: Optional[List[str]] = None) -> Optional[ProxyInfo]:
        """获取最佳代理"""
        exclude = exclude or []

        with self.lock:
            # 过滤可用的代理
            available_proxies = [
                proxy for proxy in self.proxies
                if (proxy.status in [ProxyStatus.HEALTHY, ProxyStatus.UNKNOWN] and
                    f"{proxy.host}:{proxy.port}" not in exclude)
            ]

            if not available_proxies:
                logger.warning("没有可用的代理")
                return None

            # 按响应时间和成功率排序
            def proxy_score(proxy: ProxyInfo) -> tuple:
                success_rate = proxy.success_count / (proxy.success_count + proxy.failure_count + 1)
                return (-success_rate, proxy.response_time, proxy.last_used)

            available_proxies.sort(key=proxy_score)

            # 选择最佳代理
            best_proxy = available_proxies[0]
            best_proxy.last_used = time.time()

            return best_proxy

    def get_random_proxy(self, exclude: Optional[List[str]] = None) -> Optional[ProxyInfo]:
        """获取随机代理"""
        exclude = exclude or []

        with self.lock:
            available_proxies = [
                proxy for proxy in self.proxies
                if (proxy.status in [ProxyStatus.HEALTHY, ProxyStatus.UNKNOWN] and
                    f"{proxy.host}:{proxy.port}" not in exclude)
            ]

            if not available_proxies:
                return None

            return random.choice(available_proxies)

    def mark_proxy_failed(self, proxy: ProxyInfo, error_type: str = "unknown"):
        """标记代理失败"""
        with self.lock:
            proxy.failure_count += 1

            if error_type == "banned":
                proxy.status = ProxyStatus.BANNED
            elif error_type == "rate_limited":
                proxy.status = ProxyStatus.RATE_LIMITED
            else:
                failure_rate = proxy.failure_count / (proxy.success_count + proxy.failure_count)
                if failure_rate > self.max_failure_rate:
                    proxy.status = ProxyStatus.UNHEALTHY

    def mark_proxy_success(self, proxy: ProxyInfo, response_time: float = 0):
        """标记代理成功"""
        with self.lock:
            proxy.success_count += 1
            proxy.response_time = response_time
            proxy.status = ProxyStatus.HEALTHY

    def get_stats(self) -> Dict[str, Any]:
        """获取代理池统计信息"""
        with self.lock:
            stats = {
                "total": len(self.proxies),
                "healthy": len([p for p in self.proxies if p.status == ProxyStatus.HEALTHY]),
                "unhealthy": len([p for p in self.proxies if p.status == ProxyStatus.UNHEALTHY]),
                "unknown": len([p for p in self.proxies if p.status == ProxyStatus.UNKNOWN]),
                "banned": len([p for p in self.proxies if p.status == ProxyStatus.BANNED]),
                "rate_limited": len([p for p in self.proxies if p.status == ProxyStatus.RATE_LIMITED])
            }

            # 计算平均响应时间
            healthy_proxies = [p for p in self.proxies if p.status == ProxyStatus.HEALTHY]
            if healthy_proxies:
                stats["avg_response_time"] = sum(p.response_time for p in healthy_proxies) / len(healthy_proxies)
            else:
                stats["avg_response_time"] = 0

            return stats

    def export_proxies(self, file_path: str, status_filter: Optional[ProxyStatus] = None):
        """导出代理列表"""
        with self.lock:
            proxies_to_export = self.proxies
            if status_filter:
                proxies_to_export = [p for p in self.proxies if p.status == status_filter]

            data = [asdict(proxy) for proxy in proxies_to_export]

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"导出了 {len(data)} 个代理到 {file_path}")

class ProxyRotator:
    """代理轮换器"""

    def __init__(self, proxy_pool: ProxyPool, strategy: str = "best"):
        self.proxy_pool = proxy_pool
        self.strategy = strategy
        self.current_proxy = None
        self.exclude_list = []
        self.usage_count = {}

    def get_proxy(self) -> Optional[ProxyInfo]:
        """获取代理"""
        if self.strategy == "best":
            proxy = self.proxy_pool.get_best_proxy(self.exclude_list)
        elif self.strategy == "random":
            proxy = self.proxy_pool.get_random_proxy(self.exclude_list)
        elif self.strategy == "round_robin":
            proxy = self._get_round_robin_proxy()
        else:
            proxy = self.proxy_pool.get_best_proxy(self.exclude_list)

        if proxy:
            self.current_proxy = proxy
            proxy_key = f"{proxy.host}:{proxy.port}"
            self.usage_count[proxy_key] = self.usage_count.get(proxy_key, 0) + 1

        return proxy

    def _get_round_robin_proxy(self) -> Optional[ProxyInfo]:
        """轮询获取代理"""
        with self.proxy_pool.lock:
            available_proxies = [
                proxy for proxy in self.proxy_pool.proxies
                if (proxy.status in [ProxyStatus.HEALTHY, ProxyStatus.UNKNOWN] and
                    f"{proxy.host}:{proxy.port}" not in self.exclude_list)
            ]

            if not available_proxies:
                return None

            # 按使用次数排序
            available_proxies.sort(key=lambda p: self.usage_count.get(f"{p.host}:{p.port}", 0))
            return available_proxies[0]

    def mark_success(self, response_time: float = 0):
        """标记代理使用成功"""
        if self.current_proxy:
            self.proxy_pool.mark_proxy_success(self.current_proxy, response_time)

    def mark_failed(self, error_type: str = "unknown"):
        """标记代理使用失败"""
        if self.current_proxy:
            self.proxy_pool.mark_proxy_failed(self.current_proxy, error_type)
            # 将失败的代理加入排除列表
            proxy_key = f"{self.current_proxy.host}:{self.current_proxy.port}"
            self.exclude_list.append(proxy_key)

            # 限制排除列表长度
            if len(self.exclude_list) > 50:
                self.exclude_list = self.exclude_list[-25:]

    def reset(self):
        """重置轮换器状态"""
        self.current_proxy = None
        self.exclude_list = []

# 便捷函数
def create_proxy_pool(cfg: Dict[str, Any] = None) -> ProxyPool:
    """创建代理池"""
    return ProxyPool(cfg)

def create_proxy_rotator(proxy_pool: ProxyPool, strategy: str = "best") -> ProxyRotator:
    """创建代理轮换器"""
    return ProxyRotator(proxy_pool, strategy)