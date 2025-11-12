# -*- coding: utf-8 -*-
"""
主程序 - 完全仿照 yiya-crawler 的 main.js
使用 Crawlee 风格的 PuppeteerCrawler
"""

import asyncio
import os
import sys
from rich import print as rprint

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawlers.nmpaCrawler import nmpa_crawler
from config.constants import SITE_CONFIG
from utils.logger import logger


# 环境变量配置 - 复制自 yiya-crawler
os.environ.setdefault('MAX_CONCURRENCY', '2')
os.environ.setdefault('MAX_RETRIES', '3')
os.environ.setdefault('MAX_PAGES', '50')
os.environ.setdefault('CRAWL_QUEUE_SIZE', '4')


# 每小时执行的任务 - 复制自 yiya-crawler
async def hourly_job():
    """每小时执行的任务"""
    try:
        rprint("[blue]每小时任务 - 开始...[/]")
        # 这里可以添加其他任务逻辑
        rprint("[green]每小时任务 - 完成[/]")
    except Exception as error:
        rprint(f"[red]每小时任务 - 失败: {error}[/]")


async def main():
    """主函数 - 完全仿照 yiya-crawler 的主逻辑"""

    # 首次立即执行一次（可选）
    await hourly_job()

    # 启动爬虫 - nmpa - 完全仿照 yiya-crawler
    rprint("[bold blue]启动 NMPA 爬虫 (仿照 yiya-crawler Crawlee 风格)[/]")

    try:
        # 获取 NMPA 配置
        nmpa_config = SITE_CONFIG["nmpa"]
        page_list = nmpa_config["pageList"]

        rprint(f"[cyan]站点代码: {nmpa_config['code']}[/]")
        rprint(f"[cyan]站点名称: {nmpa_config['name']}[/]")
        rprint(f"[cyan]页面列表数量: {len(page_list)}[/]")

        # 运行爬虫
        results = await nmpa_crawler.run(page_list)

        # 显示结果
        if results:
            for result in results:
                stats = result.get("stats", {})
                processed_count = result.get("processed_count", 0)
                site_code = result.get("site_code", "N/A")
                site_name = result.get("site_name", "N/A")

                rprint(f"[green]✅ {site_code} 爬虫完成[/]")
                rprint(f"   站点名称: {site_name}")
                rprint(f"   处理页面数: {processed_count}")
                rprint(f"   成功请求: {stats.get('successful_requests', 0)}")
                rprint(f"   失败请求: {stats.get('failed_requests', 0)}")
                rprint(f"   提取条目: {stats.get('items_extracted', 0)}")

        rprint("[bold green]🎉 Crawling 完成！[/]")

    except Exception as err:
        rprint(f"[red]Crawler failed: {err}[/]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 完全仿照 yiya-crawler 的启动方式
    rprint("[bold blue]🚀 NMPA 爬虫启动 (仿照 yiya-crawler Crawlee 风格)[/]")

    # 检查依赖
    try:
        from playwright.async_api import async_playwright
        rprint("[green]✅ Playwright 依赖检查通过[/]")
    except ImportError:
        rprint("[red]❌ 缺少 Playwright 依赖，请安装: pip install playwright[/]")
        rprint("[yellow]然后运行: playwright install chromium[/]")
        sys.exit(1)

    # 运行主程序
    asyncio.run(main())