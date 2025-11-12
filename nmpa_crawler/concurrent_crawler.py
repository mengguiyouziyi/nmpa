# -*- coding: utf-8 -*-
"""
并发爬虫模块 - 支持多任务并发处理
支持多种引擎并发和智能任务调度
"""
import asyncio
import concurrent.futures
import threading
import time
import queue
from typing import Any, Dict, List, Callable, Optional
from dataclasses import dataclass
from enum import Enum
import logging

from browser_engine import NMPABrowserCrawler
from drission_engine import NMPADrissionCrawler
from http_engine import NMPAHttpEngine
from utils import sleep_jitter

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EngineType(Enum):
    BROWSER = "browser"
    DRISSION = "drission"
    HTTP = "http"

@dataclass
class CrawlerTask:
    """爬虫任务数据结构"""
    dataset: str
    code_prefix: str
    engine_type: EngineType
    task_id: str
    priority: int = 1
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class TaskResult:
    """任务结果数据结构"""
    task: CrawlerTask
    success: bool
    records: List[Dict[str, Any]]
    error: Optional[str] = None
    execution_time: float = 0.0

class ConcurrentCrawlerManager:
    """
    并发爬虫管理器
    支持多引擎并发、任务调度、失败重试
    """

    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.max_workers = cfg.get("concurrent", {}).get("max_workers", 3)
        self.engine_type = cfg.get("concurrent", {}).get("engine_type", "auto")
        self.task_queue = queue.PriorityQueue()
        self.results = []
        self.active_tasks = {}
        self.lock = threading.Lock()

        # 引擎实例缓存
        self.engine_cache = {}
        self.engine_usage_count = {}

    def create_engine(self, engine_type: EngineType) -> Any:
        """创建引擎实例"""
        if engine_type == EngineType.BROWSER:
            return NMPABrowserCrawler(self.cfg)
        elif engine_type == EngineType.DRISSION:
            return NMPADrissionCrawler(self.cfg)
        elif engine_type == EngineType.HTTP:
            return NMPAHttpEngine(self.cfg)
        else:
            raise ValueError(f"不支持的引擎类型: {engine_type}")

    def get_engine(self, engine_type: EngineType) -> Any:
        """获取引擎实例（支持复用）"""
        with self.lock:
            # 检查是否可以使用缓存的引擎
            if engine_type in self.engine_cache:
                usage_count = self.engine_usage_count.get(engine_type, 0)
                max_usage = self.cfg.get("concurrent", {}).get("max_engine_usage", 5)

                if usage_count < max_usage:
                    self.engine_usage_count[engine_type] = usage_count + 1
                    return self.engine_cache[engine_type]

            # 创建新引擎
            engine = self.create_engine(engine_type)
            self.engine_cache[engine_type] = engine
            self.engine_usage_count[engine_type] = 1
            return engine

    def release_engine(self, engine_type: EngineType):
        """释放引擎实例"""
        with self.lock:
            if engine_type in self.engine_usage_count:
                self.engine_usage_count[engine_type] = max(0, self.engine_usage_count[engine_type] - 1)

    def select_best_engine(self) -> EngineType:
        """自动选择最佳引擎"""
        if self.engine_type != "auto":
            return EngineType(self.engine_type)

        # 根据配置和历史成功率选择引擎
        engine_weights = {
            EngineType.DRISSION: 0.5,  # 最推荐
            EngineType.BROWSER: 0.3,  # 次推荐
            EngineType.HTTP: 0.2      # 需要签名算法
        }

        # 可以根据实际情况调整权重
        return max(engine_weights.items(), key=lambda x: x[1])[0]

    def add_task(self, dataset: str, code_prefix: str, engine_type: Optional[str] = None):
        """添加爬虫任务"""
        if engine_type:
            task_engine = EngineType(engine_type)
        else:
            task_engine = self.select_best_engine()

        task = CrawlerTask(
            dataset=dataset,
            code_prefix=code_prefix,
            engine_type=task_engine,
            task_id=f"{dataset}_{code_prefix}_{int(time.time())}",
            priority=1
        )

        # 使用优先级队列，优先级值越小越优先
        self.task_queue.put((task.priority, task))
        logger.info(f"添加任务: {task.task_id}")

    def execute_task(self, task: CrawlerTask) -> TaskResult:
        """执行单个爬虫任务"""
        start_time = time.time()
        logger.info(f"开始执行任务: {task.task_id}")

        try:
            # 获取引擎实例
            engine = self.get_engine(task.engine_type)

            # 如果是浏览器或DrissionPage引擎，需要启动
            if task.engine_type in [EngineType.BROWSER, EngineType.DRISSION]:
                engine.start()

            # 执行爬取
            records = engine.crawl_job(task.dataset, task.code_prefix, "outputs")

            # 创建结果
            result = TaskResult(
                task=task,
                success=True,
                records=records,
                execution_time=time.time() - start_time
            )

            logger.info(f"任务完成: {task.task_id}, 获取记录数: {len(records)}")
            return result

        except Exception as e:
            error_msg = f"任务失败: {task.task_id}, 错误: {str(e)}"
            logger.error(error_msg)

            return TaskResult(
                task=task,
                success=False,
                records=[],
                error=error_msg,
                execution_time=time.time() - start_time
            )

        finally:
            # 释放引擎
            self.release_engine(task.engine_type)

            # 如果是浏览器引擎，停止它
            try:
                if task.engine_type in [EngineType.BROWSER, EngineType.DRISSION]:
                    engine.stop()
            except Exception:
                pass

    def worker_thread(self, worker_id: int):
        """工作线程"""
        logger.info(f"工作线程 {worker_id} 启动")

        while True:
            try:
                # 获取任务（带超时）
                priority, task = self.task_queue.get(timeout=5)

                # 检查是否应该停止
                if task.task_id == "STOP":
                    break

                # 执行任务
                result = self.execute_task(task)

                # 处理结果
                with self.lock:
                    self.results.append(result)

                    # 如果失败且未达到最大重试次数，重新加入队列
                    if not result.success and task.retry_count < task.max_retries:
                        task.retry_count += 1
                        task.priority += 1  # 降低优先级
                        self.task_queue.put((task.priority, task))
                        logger.info(f"任务重试: {task.task_id}, 重试次数: {task.retry_count}")

                # 标记任务完成
                self.task_queue.task_done()

            except queue.Empty:
                # 超时，继续等待
                continue
            except Exception as e:
                logger.error(f"工作线程 {worker_id} 错误: {e}")

        logger.info(f"工作线程 {worker_id} 停止")

    def run_concurrent(self) -> List[TaskResult]:
        """运行并发爬虫"""
        logger.info(f"启动并发爬虫，工作线程数: {self.max_workers}")

        # 创建并启动工作线程
        threads = []
        for i in range(self.max_workers):
            thread = threading.Thread(target=self.worker_thread, args=(i,))
            thread.start()
            threads.append(thread)

        # 等待所有任务完成
        self.task_queue.join()

        # 发送停止信号
        for _ in range(self.max_workers):
            self.task_queue.put((0, CrawlerTask("", "", EngineType.BROWSER, "STOP")))

        # 等待所有线程结束
        for thread in threads:
            thread.join()

        # 清理引擎缓存
        for engine in self.engine_cache.values():
            try:
                if hasattr(engine, 'stop'):
                    engine.stop()
                elif hasattr(engine, 'quit'):
                    engine.quit()
            except Exception:
                pass

        logger.info(f"并发爬虫完成，总结果数: {len(self.results)}")
        return self.results

class AsyncTaskManager:
    """
    异步任务管理器
    支持异步IO操作，适合HTTP引擎的高并发
    """

    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.max_concurrent = cfg.get("concurrent", {}).get("max_async_tasks", 10)
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        self.results = []

    async def execute_async_task(self, task: CrawlerTask) -> TaskResult:
        """异步执行任务"""
        async with self.semaphore:
            start_time = time.time()
            logger.info(f"异步任务开始: {task.task_id}")

            try:
                # 在异步环境中运行同步代码
                loop = asyncio.get_event_loop()

                if task.engine_type == EngineType.HTTP:
                    # HTTP引擎可以在异步中直接使用
                    engine = NMPAHttpEngine(self.cfg)
                    records = await loop.run_in_executor(
                        None,
                        lambda: self._crawl_with_http_engine(engine, task)
                    )
                else:
                    # 其他引擎需要在线程池中运行
                    records = await loop.run_in_executor(
                        None,
                        lambda: self._crawl_with_sync_engine(task)
                    )

                result = TaskResult(
                    task=task,
                    success=True,
                    records=records,
                    execution_time=time.time() - start_time
                )

                logger.info(f"异步任务完成: {task.task_id}, 记录数: {len(records)}")
                return result

            except Exception as e:
                error_msg = f"异步任务失败: {task.task_id}, 错误: {str(e)}"
                logger.error(error_msg)

                return TaskResult(
                    task=task,
                    success=False,
                    records=[],
                    error=error_msg,
                    execution_time=time.time() - start_time
                )

    def _crawl_with_http_engine(self, engine: NMPAHttpEngine, task: CrawlerTask) -> List[Dict[str, Any]]:
        """使用HTTP引擎爬取"""
        # 获取item_id
        item_ids = {"domestic": "ff80808183cad75001840881f848179f", "imported": ""}
        item_id = item_ids.get(task.dataset, "")

        all_records = []
        max_pages = int(self.cfg.get("max_pages", 50))
        page_size = int(self.cfg.get("page_size", 30))

        for page in range(1, max_pages + 1):
            try:
                # 搜索
                search_data = engine.search(item_id, task.code_prefix, page, page_size)
                if not search_data:
                    break

                # 提取列表数据
                node = search_data.get('data', search_data)
                lst = node.get('list') or node.get('resultList') or node.get('rows') or []

                if not lst:
                    break

                # 获取详情
                for row in lst:
                    doc_id = str(row.get('id') or row.get('ID') or row.get('docId') or '')
                    if doc_id:
                        detail = engine.detail(item_id, doc_id)
                        all_records.append({"detail": detail, "list_data": row})

                # 延迟
                sleep_jitter(
                    self.cfg.get("delay_min_ms", 600),
                    self.cfg.get("delay_max_ms", 1500)
                )

            except Exception as e:
                logger.error(f"HTTP引擎爬取失败，页面 {page}: {e}")
                break

        return all_records

    def _crawl_with_sync_engine(self, task: CrawlerTask) -> List[Dict[str, Any]]:
        """使用同步引擎爬取"""
        manager = ConcurrentCrawlerManager(self.cfg)
        engine = manager.get_engine(task.engine_type)

        try:
            if hasattr(engine, 'start'):
                engine.start()
            records = engine.crawl_job(task.dataset, task.code_prefix, "outputs")
            return records
        finally:
            if hasattr(engine, 'stop'):
                engine.stop()
            manager.release_engine(task.engine_type)

    async def run_async(self, tasks: List[CrawlerTask]) -> List[TaskResult]:
        """运行异步任务"""
        logger.info(f"启动异步爬虫，任务数: {len(tasks)}, 最大并发: {self.max_concurrent}")

        # 创建异步任务
        async_tasks = [self.execute_async_task(task) for task in tasks]

        # 等待所有任务完成
        self.results = await asyncio.gather(*async_tasks, return_exceptions=True)

        # 过滤异常结果
        valid_results = []
        for result in self.results:
            if isinstance(result, TaskResult):
                valid_results.append(result)
            else:
                logger.error(f"异步任务异常: {result}")

        logger.info(f"异步爬虫完成，有效结果数: {len(valid_results)}")
        return valid_results

# 便捷函数
def create_concurrent_crawler(cfg: Dict[str, Any]) -> ConcurrentCrawlerManager:
    """创建并发爬虫管理器"""
    return ConcurrentCrawlerManager(cfg)

def create_async_crawler(cfg: Dict[str, Any]) -> AsyncTaskManager:
    """创建异步爬虫管理器"""
    return AsyncTaskManager(cfg)