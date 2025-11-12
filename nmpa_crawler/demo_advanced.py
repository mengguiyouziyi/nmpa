#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NMPA 爬虫高级功能演示脚本
展示所有新增功能的使用方法
"""
import asyncio
import time
import json
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from drission_engine import NMPADrissionCrawler
from sign_cracker import NMPASignCracker
from concurrent_crawler import create_concurrent_crawler, create_async_crawler
from proxy_manager import create_proxy_pool, create_proxy_rotator
from http_engine import NMPAHttpEngine

console = Console()

def demo_drission_page():
    """演示DrissionPage引擎"""
    rprint("\n[bold blue]🚀 演示 DrissionPage 引擎[/]")

    cfg = {
        "headless": True,
        "max_pages": 2,
        "delay_min_ms": 1000,
        "delay_max_ms": 2000
    }

    crawler = NMPADrissionCrawler(cfg)

    try:
        rprint("启动 DrissionPage 引擎...")
        crawler.start()

        rprint("获取 itemId...")
        item_ids = crawler.get_item_ids()
        rprint(f"获取到的 itemId: {item_ids}")

        # 演示搜索功能
        if item_ids.get("domestic"):
            rprint("执行搜索...")
            results = crawler.search_once(
                item_ids["domestic"],
                "国药准字H",
                1,
                10
            )
            rprint(f"搜索到 {len(results)} 条结果")

            if results:
                rprint("获取第一条详情...")
                detail = crawler.fetch_detail(
                    item_ids["domestic"],
                    results[0].get("doc_id", "")
                )
                rprint(f"详情数据类型: {type(detail)}")

    except Exception as e:
        rprint(f"[bold red]DrissionPage 演示失败: {e}[/]")
    finally:
        crawler.stop()

def demo_sign_cracking():
    """演示签名算法破解"""
    rprint("\n[bold blue]🔐 演示 JS 签名算法破解[/]")

    cfg = {
        "sign_engine": {
            "secret_key": "demo_secret_key"
        }
    }

    cracker = NMPASignCracker(cfg)

    # 测试数据
    test_url = "https://www.nmpa.gov.cn/datasearch/data/nmpadata/search"
    test_params = {
        "itemId": "test123",
        "searchValue": "国药准字H",
        "pageNum": 1,
        "pageSize": 30
    }

    # 演示不同签名算法
    algorithms = [
        ("V1-MD5签名", cracker.crack_sign_v1),
        ("V2-HMAC-SHA256签名", cracker.crack_sign_v2),
        ("V3-AES加密签名", cracker.crack_sign_v3),
        ("V4-复合签名", cracker.crack_sign_v4),
        ("自动检测", cracker.auto_detect_and_crack)
    ]

    table = Table(title="签名算法对比")
    table.add_column("算法类型", style="cyan")
    table.add_column("签名值", style="green")
    table.add_column("时间戳", style="yellow")
    table.add_column("其他参数", style="magenta")

    for name, func in algorithms:
        try:
            result = func(test_url, test_params.copy())
            sign = result.get("sign", "")[:32] + "..."  # 只显示前32位
            timestamp = str(result.get("timestamp", ""))
            other_params = []

            for key, value in result.items():
                if key not in ["sign", "timestamp"]:
                    other_params.append(f"{key}={str(value)[:16]}...")

            table.add_row(
                name,
                sign,
                timestamp,
                ", ".join(other_params)
            )
        except Exception as e:
            table.add_row(name, f"错误: {e}", "", "")

    console.print(table)

def demo_concurrent_crawler():
    """演示并发爬虫"""
    rprint("\n[bold blue]⚡ 演示并发爬虫[/]")

    cfg = {
        "mode": "drission",
        "headless": True,
        "max_pages": 1,
        "delay_min_ms": 2000,
        "delay_max_ms": 3000,
        "concurrent": {
            "enabled": True,
            "max_workers": 2,
            "engine_type": "drission"
        },
        "jobs": [
            {"dataset": "domestic", "code_prefix": "国药准字H"},
            {"dataset": "domestic", "code_prefix": "国药准字S"}
        ]
    }

    manager = create_concurrent_crawler(cfg)

    # 添加任务
    for job in cfg["jobs"]:
        manager.add_task(job["dataset"], job["code_prefix"])

    # 运行并发任务
    start_time = time.time()
    results = manager.run_concurrent()
    execution_time = time.time() - start_time

    # 显示结果
    rprint(f"[bold green]并发爬虫完成[/] 耗时: {execution_time:.2f}s")

    table = Table(title="并发任务结果")
    table.add_column("任务ID", style="cyan")
    table.add_column("状态", style="green")
    table.add_column("记录数", style="yellow")
    table.add_column("耗时", style="magenta")

    for result in results:
        status = "✅ 成功" if result.success else "❌ 失败"
        table.add_row(
            result.task.task_id,
            status,
            str(len(result.records)),
            f"{result.execution_time:.2f}s"
        )

    console.print(table)

async def demo_async_crawler():
    """演示异步爬虫"""
    rprint("\n[bold blue]🔄 演示异步爬虫[/]")

    cfg = {
        "mode": "http",
        "headless": True,
        "max_pages": 1,
        "delay_min_ms": 1000,
        "delay_max_ms": 2000,
        "async": {
            "enabled": True,
            "max_async_tasks": 3
        },
        "jobs": [
            {"dataset": "domestic", "code_prefix": "国药准字H", "engine_type": "http"},
            {"dataset": "domestic", "code_prefix": "国药准字S", "engine_type": "http"}
        ]
    }

    async_manager = create_async_crawler(cfg)

    # 创建任务列表
    from concurrent_crawler import CrawlerTask, EngineType

    tasks = []
    for job in cfg["jobs"]:
        task = CrawlerTask(
            dataset=job["dataset"],
            code_prefix=job["code_prefix"],
            engine_type=EngineType(job["engine_type"]),
            task_id=f"{job['dataset']}_{job['code_prefix']}"
        )
        tasks.append(task)

    # 运行异步任务
    start_time = time.time()
    results = await async_manager.run_async(tasks)
    execution_time = time.time() - start_time

    # 显示结果
    rprint(f"[bold green]异步爬虫完成[/] 耗时: {execution_time:.2f}s")

    table = Table(title="异步任务结果")
    table.add_column("任务ID", style="cyan")
    table.add_column("状态", style="green")
    table.add_column("记录数", style="yellow")
    table.add_column("耗时", style="magenta")

    for result in results:
        status = "✅ 成功" if result.success else "❌ 失败"
        table.add_row(
            result.task.task_id,
            status,
            str(len(result.records)),
            f"{result.execution_time:.2f}s"
        )

    console.print(table)

def demo_proxy_manager():
    """演示代理管理"""
    rprint("\n[bold blue]🌐 演示代理管理[/]")

    # 模拟代理配置
    cfg = {
        "proxy": {
            "enabled": True,
            "check_interval": 60,  # 1分钟检查一次
            "test_urls": ["http://httpbin.org/ip"],
            "proxies": [
                {
                    "host": "proxy1.example.com",
                    "port": 8080,
                    "type": "http",
                    "country": "US"
                },
                {
                    "host": "proxy2.example.com",
                    "port": 1080,
                    "type": "socks5",
                    "country": "JP"
                }
            ]
        }
    }

    pool = create_proxy_pool(cfg)

    # 显示代理池统计
    stats = pool.get_stats()
    rprint(f"代理池统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")

    # 演示代理轮换
    rotator = create_proxy_rotator(pool, "best")

    rprint("获取最佳代理...")
    proxy = rotator.get_proxy()
    if proxy:
        rprint(f"最佳代理: {proxy.host}:{proxy.port} ({proxy.proxy_type.value})")
    else:
        rprint("没有可用的代理")

    # 演示代理状态
    table = Table(title="代理状态")
    table.add_column("代理", style="cyan")
    table.add_column("类型", style="green")
    table.add_column("状态", style="yellow")
    table.add_column("成功次数", style="magenta")
    table.add_column("失败次数", style="red")

    for proxy in pool.proxies[:5]:  # 只显示前5个
        table.add_row(
            f"{proxy.host}:{proxy.port}",
            proxy.proxy_type.value,
            proxy.status.value,
            str(proxy.success_count),
            str(proxy.failure_count)
        )

    console.print(table)

def demo_http_engine():
    """演示HTTP引擎"""
    rprint("\n[bold blue]📡 演示HTTP引擎[/]")

    cfg = {
        "sign_engine": {
            "secret_key": "demo_secret_key",
            "algorithm": "v2"
        }
    }

    engine = NMPAHttpEngine(cfg)

    # 演示签名生成
    test_url = "https://www.nmpa.gov.cn/datasearch/data/nmpadata/search"
    test_params = {
        "itemId": "ff80808183cad75001840881f848179f",
        "searchValue": "国药准字H",
        "pageNum": 1,
        "pageSize": 10
    }

    try:
        headers, sign_data = engine.sign_cracker.generate_headers(test_url, test_params)

        rprint("生成的签名数据:")
        for key, value in sign_data.items():
            if key != 'encData':
                rprint(f"  {key}: {value}")

        rprint("\n请求头:")
        for key, value in headers.items():
            if key not in ['User-Agent', 'Accept']:  # 跳过常见头部
                rprint(f"  {key}: {value}")

        # 注意：这里不会实际发送请求，只演示签名生成
        rprint("\n[bold yellow]注意：演示模式，未实际发送请求[/]")

    except Exception as e:
        rprint(f"[bold red]HTTP引擎演示失败: {e}[/]")

def main():
    """主演示函数"""
    console.print("[bold green]🎯 NMPA 爬虫高级功能演示[/]")
    console.print("=" * 50)

    try:
        # 演示各项功能
        demo_drission_page()
        demo_sign_cracking()
        demo_concurrent_crawler()
        asyncio.run(demo_async_crawler())
        demo_proxy_manager()
        demo_http_engine()

        console.print("\n[bold green]✅ 所有演示完成！[/]")

    except KeyboardInterrupt:
        console.print("\n[bold yellow]演示被用户中断[/]")
    except Exception as e:
        console.print(f"\n[bold red]演示过程中出现错误: {e}[/]")

if __name__ == "__main__":
    main()