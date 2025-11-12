#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NMPA HTTP引擎 V2 - 基于签名算法破解的高性能爬虫引擎
"""

import os
import json
import time
import logging
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from http_client import NMPAHTTPClient, create_nmpa_client
from utils import extract_required_fields, sleep_jitter
from exporter import export_records


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NMPAHTTPEngineV2:
    """NMPA HTTP引擎V2 - 基于签名算法破解"""

    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.client = None
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'start_time': None,
            'end_time': None
        }
        self._lock = threading.Lock()

    def _initialize_client(self):
        """初始化HTTP客户端"""
        if self.client is None:
            client_config = {
                'sign_algorithm': self.cfg.get('sign_algorithm', 'auto'),
                'max_retries': self.cfg.get('retry', 3),
                'proxy': self.cfg.get('proxy', {})
            }
            self.client = create_nmpa_client(client_config)
            logger.info("HTTP客户端初始化完成")

    def _update_stats(self, **kwargs):
        """更新统计信息"""
        with self._lock:
            for key, value in kwargs.items():
                if key in self.stats:
                    self.stats[key] = value
                elif hasattr(self, f'set_{key}'):
                    getattr(self, f'set_{key}')(value)

    def start(self):
        """启动引擎"""
        logger.info("启动NMPA HTTP引擎V2...")
        self._initialize_client()
        self._update_stats(start_time=time.time())

    def stop(self):
        """停止引擎"""
        if self.client:
            self.client.session.close()
        self._update_stats(end_time=time.time())
        logger.info("NMPA HTTP引擎V2已停止")

    def crawl_job(self, dataset: str, code_prefix: str, out_dir: str) -> List[Dict[str, Any]]:
        """爬取单个任务"""
        logger.info(f"开始爬取任务: {dataset} - {code_prefix}")

        max_pages = int(self.cfg.get("max_pages", 50))
        all_records = []

        try:
            # 使用HTTP客户端爬取数据
            records = self.client.crawl_dataset(dataset, code_prefix, max_pages)

            # 处理和格式化数据
            formatted_records = []
            for record in records:
                formatted_record = self._format_record(record, dataset, code_prefix)
                if formatted_record:
                    formatted_records.append(formatted_record)

            all_records = formatted_records

            logger.info(f"任务完成: {dataset} - {code_prefix}, 共 {len(all_records)} 条记录")

        except Exception as e:
            logger.error(f"任务失败: {dataset} - {code_prefix}, 错误: {e}")
            raise

        return all_records

    def _format_record(self, raw_record: Dict[str, Any], dataset: str, code_prefix: str) -> Optional[Dict[str, Any]]:
        """格式化单条记录"""
        try:
            # 提取详情数据
            detail_data = raw_record.get('detail_data', {})
            list_data = raw_record.get('list_data', {})

            # 使用utils中的字段提取函数
            extracted_fields = extract_required_fields(detail_data, dataset)

            # 添加元数据
            formatted_record = {
                **extracted_fields,
                'dataset': dataset,
                'code_prefix': code_prefix,
                'crawl_time': raw_record.get('crawl_time'),
                'doc_id': list_data.get('id') or list_data.get('docId'),
                'raw_data': raw_record  # 保留原始数据
            }

            return formatted_record

        except Exception as e:
            logger.warning(f"格式化记录失败: {e}")
            return None

    def get_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        duration = None
        if self.stats.get('start_time') and self.stats.get('end_time'):
            duration = self.stats['end_time'] - self.stats['start_time']
        elif self.stats.get('start_time'):
            duration = time.time() - self.stats['start_time']

        status = {
            'engine_type': 'HTTP_V2',
            'status': 'running' if self.client else 'stopped',
            'duration': duration,
            'stats': self.stats.copy()
        }

        if self.client:
            status.update(self.client.get_status())

        return status


class ConcurrentNMPAEngine:
    """并发NMPA爬虫引擎"""

    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.max_workers = cfg.get('concurrent', {}).get('max_workers', 3)
        self.engines = []
        self.stats = {
            'total_jobs': 0,
            'completed_jobs': 0,
            'failed_jobs': 0,
            'total_records': 0,
            'start_time': None,
            'end_time': None
        }

    def create_engine(self) -> NMPAHTTPEngineV2:
        """创建引擎实例"""
        return NMPAHTTPEngineV2(self.cfg)

    def run_jobs(self, jobs: List[Dict[str, Any]], output_dir: str) -> Dict[str, Any]:
        """并发运行多个任务"""
        logger.info(f"开始并发执行 {len(jobs)} 个任务，最大并发数: {self.max_workers}")
        self.stats['start_time'] = time.time()
        self.stats['total_jobs'] = len(jobs)

        results = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_job = {}
            for job in jobs:
                engine = self.create_engine()
                engine.start()

                dataset = job['dataset']
                code_prefix = job['code_prefix']

                future = executor.submit(
                    self._run_single_job,
                    engine, dataset, code_prefix, output_dir
                )
                future_to_job[future] = job

            # 收集结果
            for future in as_completed(future_to_job):
                job = future_to_job[future]
                dataset = job['dataset']
                code_prefix = job['code_prefix']

                try:
                    records, export_info = future.result()
                    results[f"{dataset}_{code_prefix}"] = {
                        'records': records,
                        'export_info': export_info,
                        'count': len(records),
                        'status': 'success'
                    }
                    self.stats['completed_jobs'] += 1
                    self.stats['total_records'] += len(records)
                    logger.info(f"任务完成: {dataset} - {code_prefix}, {len(records)} 条记录")

                except Exception as e:
                    logger.error(f"任务失败: {dataset} - {code_prefix}, 错误: {e}")
                    results[f"{dataset}_{code_prefix}"] = {
                        'records': [],
                        'export_info': {},
                        'count': 0,
                        'status': 'failed',
                        'error': str(e)
                    }
                    self.stats['failed_jobs'] += 1

        self.stats['end_time'] = time.time()
        logger.info(f"所有任务完成，成功: {self.stats['completed_jobs']}, 失败: {self.stats['failed_jobs']}")

        return results

    def _run_single_job(self, engine: NMPAHTTPEngineV2, dataset: str, code_prefix: str, output_dir: str) -> tuple:
        """运行单个任务"""
        try:
            # 爬取数据
            records = engine.crawl_job(dataset, code_prefix, output_dir)

            # 导出数据
            export_info = {}
            if records:
                # 创建输出目录
                os.makedirs(output_dir, exist_ok=True)

                # 生成文件名
                filename = f"{dataset}_{code_prefix}"
                export_info = export_records(
                    records,
                    output_dir,
                    filename,
                    self.cfg.get('export_format', 'excel')
                )

            return records, export_info

        finally:
            # 确保引擎停止
            engine.stop()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        duration = None
        if self.stats.get('start_time') and self.stats.get('end_time'):
            duration = self.stats['end_time'] - self.stats['start_time']
        elif self.stats.get('start_time'):
            duration = time.time() - self.stats['start_time']

        return {
            'concurrent_engine': {
                'total_jobs': self.stats['total_jobs'],
                'completed_jobs': self.stats['completed_jobs'],
                'failed_jobs': self.stats['failed_jobs'],
                'total_records': self.stats['total_records'],
                'duration': duration,
                'max_workers': self.max_workers,
                'success_rate': self.stats['completed_jobs'] / max(self.stats['total_jobs'], 1) * 100
            }
        }


def run_http_engine_v2(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """运行HTTP引擎V2"""
    logger.info("启动NMPA HTTP引擎V2...")

    # 创建输出目录
    output_dir = cfg.get('output_dir', 'outputs')
    os.makedirs(output_dir, exist_ok=True)

    # 获取任务列表
    jobs = cfg.get('jobs', [])

    if not jobs:
        logger.warning("没有配置任务")
        return {}

    # 检查是否启用并发
    concurrent_config = cfg.get('concurrent', {})
    if concurrent_config.get('enabled', False):
        # 并发模式
        engine = ConcurrentNMPAEngine(cfg)
        results = engine.run_jobs(jobs, output_dir)
        stats = engine.get_stats()
    else:
        # 单线程模式
        engine = NMPAHTTPEngineV2(cfg)
        engine.start()

        try:
            results = {}
            for job in jobs:
                dataset = job['dataset']
                code_prefix = job['code_prefix']

                logger.info(f"执行任务: {dataset} - {code_prefix}")

                records = engine.crawl_job(dataset, code_prefix, output_dir)

                # 导出数据
                export_info = {}
                if records:
                    filename = f"{dataset}_{code_prefix}"
                    export_info = export_records(
                        records,
                        output_dir,
                        filename,
                        cfg.get('export_format', 'excel')
                    )

                results[f"{dataset}_{code_prefix}"] = {
                    'records': records,
                    'export_info': export_info,
                    'count': len(records),
                    'status': 'success'
                }

            stats = {'engine_status': engine.get_status()}

        finally:
            engine.stop()

    return {
        'results': results,
        'stats': stats,
        'config': cfg
    }


if __name__ == "__main__":
    # 测试HTTP引擎V2
    test_config = {
        'mode': 'http',
        'sign_algorithm': 'auto',
        'max_pages': 2,  # 测试用少量页面
        'export_format': 'both',
        'output_dir': 'test_outputs',
        'concurrent': {
            'enabled': False,
            'max_workers': 2
        },
        'jobs': [
            {'dataset': 'domestic', 'code_prefix': '国药准字H'},
        ]
    }

    print("=== NMPA HTTP引擎V2测试 ===")
    result = run_http_engine_v2(test_config)

    print(f"测试完成，结果: {result}")