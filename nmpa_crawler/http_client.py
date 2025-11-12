#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NMPA HTTP客户端
基于签名算法的HTTP请求客户端
"""

import requests
import json
import time
import random
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from sign_engine import sign_engine, generate_nmpa_sign


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NMPAHTTPClient:
    """NMPA HTTP客户端"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.base_url = "https://www.nmpa.gov.cn"
        self.session = requests.Session()

        # 设置默认请求头（基于真实抓包）
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.nmpa.gov.cn/datasearch/search-result.html',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
        })

        # NMPA已知的itemId（基于真实抓包）
        self.item_ids = {
            "domestic": "ff80808183cad75001840881f848179f",  # 境内生产药品
            "imported": "ff80808183cad75001840881f84817a0"   # 境外生产药品（待确认）
        }

        # 代理配置
        self.proxy_config = self.config.get('proxy', {})
        if self.proxy_config:
            self.setup_proxies()

        # 重试配置
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 1)

        # 算法配置
        self.sign_algorithm = self.config.get('sign_algorithm', 'auto')

    def setup_proxies(self):
        """设置代理"""
        proxies = {}
        if self.proxy_config.get('http'):
            proxies['http'] = self.proxy_config['http']
        if self.proxy_config.get('https'):
            proxies['https'] = self.proxy_config['https']

        if proxies:
            self.session.proxies.update(proxies)
            logger.info(f"已配置代理: {proxies}")

    def _add_delay(self, min_ms: int = 500, max_ms: int = 1500):
        """添加随机延迟"""
        delay = random.uniform(min_ms / 1000, max_ms / 1000)
        time.sleep(delay)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, requests.Timeout))
    )
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """发起HTTP请求（带重试）"""
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.warning(f"请求失败，准备重试: {e}")
            raise

    def get_item_ids(self) -> Dict[str, str]:
        """获取数据库ID"""
        logger.info(f"使用预配置的数据库ID - 境内: {self.item_ids.get('domestic')}, 境外: {self.item_ids.get('imported')}")
        return self.item_ids.copy()

    def _find_item_id(self, data: Dict[str, Any], target_name: str) -> Optional[str]:
        """递归查找目标数据库ID"""
        if isinstance(data, dict):
            # 检查当前层级的name和id
            if data.get('name') == target_name and 'id' in data:
                return data['id']

            # 递归搜索子节点
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    result = self._find_item_id(value, target_name)
                    if result:
                        return result

        elif isinstance(data, list):
            for item in data:
                result = self._find_item_id(item, target_name)
                if result:
                    return result

        return None

    def search_data(self, item_id: str, search_value: str, page_num: int = 1, page_size: int = 30) -> Optional[Dict[str, Any]]:
        """搜索数据"""
        url = urljoin(self.base_url, "/datasearch/data/nmpadata/search")

        # 基础参数
        params = {
            "itemId": item_id,
            "isSenior": "N",
            "searchValue": search_value,
            "pageNum": page_num,
            "pageSize": page_size
        }

        # 生成签名
        signed_params = generate_nmpa_sign(params, self.sign_algorithm)

        # 添加必要的请求头（基于真实抓包）
        headers = {
            'sign': signed_params['sign'],
            'timestamp': str(signed_params['timestamp']),
            'token': 'false'
        }

        try:
            # 添加延迟避免请求过快
            self._add_delay()

            response = self._make_request('GET', url, params=params, headers=headers)
            data = response.json()

            # 检查响应状态
            if data.get('code') == 200:
                list_data = data.get('data', {}).get('list', [])
                logger.info(f"搜索成功 - 页码: {page_num}, 数据量: {len(list_data)}")
                return data
            else:
                error_msg = data.get('message', '未知错误')
                logger.error(f"搜索失败: {error_msg}")

                # 如果是签名错误，尝试切换算法
                if 'sign' in error_msg.lower() or 'timestamp' in error_msg.lower():
                    return self._try_fallback_algorithms(params, url, headers)

                return None

        except Exception as e:
            logger.error(f"搜索请求异常: {e}")
            return None

    def _try_fallback_algorithms(self, params: Dict[str, Any], url: str, headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """尝试备用签名算法"""
        algorithms = ['v1_md5', 'v2_hmac', 'v3_aes', 'v4_composite']

        for algorithm in algorithms:
            if algorithm == self.sign_algorithm:
                continue

            try:
                logger.info(f"尝试备用算法: {algorithm}")
                signed_params = generate_nmpa_sign(params, algorithm)

                # 更新请求头
                fallback_headers = headers.copy() if headers else {}
                fallback_headers.update({
                    'sign': signed_params['sign'],
                    'timestamp': str(signed_params['timestamp']),
                    'token': 'false'
                })

                response = self._make_request('GET', url, params=params, headers=fallback_headers)
                data = response.json()

                if data.get('code') == 200:
                    logger.info(f"备用算法 {algorithm} 成功")
                    self.sign_algorithm = algorithm
                    return data

            except Exception as e:
                logger.warning(f"备用算法 {algorithm} 失败: {e}")
                continue

        logger.error("所有算法都失败了")
        return None

    def get_detail(self, item_id: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取详情数据"""
        url = urljoin(self.base_url, "/datasearch/data/nmpadata/queryDetail")

        # 基础参数
        params = {
            "itemId": item_id,
            "id": doc_id
        }

        # 生成签名
        signed_params = generate_nmpa_sign(params, self.sign_algorithm)

        try:
            self._add_delay(200, 500)  # 详情请求延迟较短

            response = self._make_request('GET', url, params=signed_params)
            data = response.json()

            if data.get('code') == 200:
                return data.get('data')
            else:
                error_msg = data.get('message', '未知错误')
                logger.error(f"获取详情失败: {error_msg}")
                return None

        except Exception as e:
            logger.error(f"详情请求异常: {e}")
            return None

    def crawl_dataset(self, dataset: str, code_prefix: str, max_pages: int = 50) -> List[Dict[str, Any]]:
        """爬取完整数据集"""
        logger.info(f"开始爬取数据集: {dataset} - {code_prefix}")

        # 获取数据库ID
        item_ids = self.get_item_ids()
        item_id = item_ids.get(dataset)

        if not item_id:
            logger.error(f"未找到数据集ID: {dataset}")
            return []

        all_records = []

        for page in range(1, max_pages + 1):
            logger.info(f"爬取第 {page} 页...")

            # 搜索列表数据
            search_result = self.search_data(item_id, code_prefix, page, 30)

            if not search_result:
                logger.info(f"第 {page} 页无数据，停止爬取")
                break

            data_list = search_result.get('data', {}).get('list', [])

            if not data_list:
                logger.info(f"第 {page} 页列表为空，停止爬取")
                break

            # 获取每条记录的详情
            for record in data_list:
                doc_id = record.get('id') or record.get('docId') or record.get('dataId')

                if doc_id:
                    # 获取详情数据
                    detail_data = self.get_detail(item_id, doc_id)

                    if detail_data:
                        # 合并列表数据和详情数据
                        full_record = {
                            'list_data': record,
                            'detail_data': detail_data,
                            'crawl_time': time.time(),
                            'dataset': dataset,
                            'code_prefix': code_prefix
                        }
                        all_records.append(full_record)

                    # 添加延迟避免请求过快
                    self._add_delay(300, 800)

            logger.info(f"第 {page} 页完成，获取 {len(data_list)} 条记录")

            # 检查是否还有更多数据
            if len(data_list) < 30:
                break

        logger.info(f"数据集 {dataset} - {code_prefix} 爬取完成，共 {len(all_records)} 条记录")
        return all_records

    def get_status(self) -> Dict[str, Any]:
        """获取客户端状态"""
        return {
            'base_url': self.base_url,
            'sign_algorithm': self.sign_algorithm,
            'proxy_configured': bool(self.proxy_config),
            'session_cookies': len(self.session.cookies),
            'algorithm_info': sign_engine.get_algorithm_info()
        }


# 便捷函数
def create_nmpa_client(config: Optional[Dict[str, Any]] = None) -> NMPAHTTPClient:
    """创建NMPA HTTP客户端"""
    return NMPAHTTPClient(config)


if __name__ == "__main__":
    # 测试HTTP客户端
    config = {
        'sign_algorithm': 'auto',
        'max_retries': 3
    }

    client = create_nmpa_client(config)

    print("=== NMPA HTTP客户端测试 ===")
    print(f"客户端状态: {client.get_status()}")

    # 测试获取数据库ID
    print("\n测试获取数据库ID...")
    item_ids = client.get_item_ids()
    print(f"数据库ID: {item_ids}")

    # 测试搜索（使用少量数据）
    print("\n测试搜索功能...")
    if item_ids.get('domestic'):
        search_result = client.search_data(item_ids['domestic'], "国药准字H", 1, 5)
        if search_result:
            print(f"搜索成功，数据结构: {list(search_result.keys())}")
        else:
            print("搜索失败")

    print("测试完成")