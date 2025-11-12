# -*- coding: utf-8 -*-
"""
文件处理器 - 完全仿照 yiya-crawler 的 fileHandler.js
"""

import os
import json
import time
import asyncio
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from datetime import datetime

from utils.logger import logger
from config.constants import SPIDER_SITE_TYPE


# 临时PDF存储目录 - 完全复制自 yiya-crawler
TEMP_DIR = 'downloads'
ATTACHMENT_DIR = 'downloads/attachments'


def ensure_dir(dir_path: str):
    """确保目录存在 - 复制自 yiya-crawler"""
    try:
        os.makedirs(dir_path, exist_ok=True)
    except Exception as e:
        logger.error(f"创建目录失败 {dir_path}: {e}")


def generate_unique_name(url: str, ext: str = 'pdf') -> str:
    """生成唯一的文件名 - 复制自 yiya-crawler"""
    timestamp = int(time.time() * 1000)
    url_hash = abs(hash(url)) % 1000000
    return f"{timestamp}_{url_hash}.{ext}"


def generate_pdf_name(url: str) -> str:
    """生成唯一文件名 - 复制自 yiya-crawler"""
    timestamp = int(time.time() * 1000)
    hostname = urlparse(url).hostname
    return f"{hostname}_{timestamp}.pdf"


def sanitize_filename(filename: str) -> str:
    """处理文件名中的特殊字符 - 复制自 yiya-crawler"""
    import re
    return re.sub(r'[\\/:*?"<>|]', '_', filename)


async def cleanup_temp_files():
    """清理临时文件 - 复制自 yiya-crawler"""
    try:
        import shutil
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR, ignore_errors=True)
            logger.info("Temporary files cleaned up")
    except Exception as error:
        logger.error(f"Failed to clean temp files: {error}")


async def handleWeb2Pdf(request, page, site_code: str, site_name: str):
    """处理网页到PDF的转换 - 完全仿照 yiya-crawler 的 handleWeb2Pdf"""
    logger.info(f"-----{site_code}: start to handleWebPage {request.url}-----")

    # 获取网页基本信息 - 复制自 yiya-crawler
    try:
        from urllib.parse import urlparse
        site_domain = urlparse(request.url).netloc
        page_url = request.url
    except:
        site_domain = "www.nmpa.gov.cn"
        page_url = request.url

    # 检查是否是PDF文件 - 复制自 yiya-crawler 的逻辑
    if page_url.endswith('.pdf') and ('search.do?formAction=openUrl' in page_url or 'pqf/file_path/help/' in page_url):
        logger.info(f"{site_code}: 处理PDF文件: {page_url}")
        # 这里可以添加PDF下载逻辑，暂时跳过
        return

    # 常规叶子页面的爬取，并保存 - 完全仿照 yiya-crawler
    try:
        # 等待页面加载
        try:
            await page.wait_for_selector('h2', timeout=10000)
        except:
            logger.warning(f"{site_code}: 等待h2元素超时")

        page_title = await page.title()
        page_type = SPIDER_SITE_TYPE["page"]
        pdf_name = sanitize_filename(page_title) + ".pdf"
        local_pdf_path = os.path.join(TEMP_DIR, pdf_name)

        logger.info(f"{site_code}: 页面标题: {page_title}")
        logger.info(f"{site_code}: PDF文件名: {pdf_name}")

        # 检查页面是否已存在 - 简化版本
        existing_file = os.path.join(TEMP_DIR, f"{page_title}.json")
        need_update = True

        if os.path.exists(existing_file):
            logger.info(f"{site_code}: 页面已存在，跳过: {page_url}")
            return

        logger.debug(f"{site_code}: 开始保存页面数据")

        # 开始数据提取流程 - 仿照 yiya-crawler 的逻辑
        try:
            # 提取页面数据
            page_data = await extract_page_data(page, page_url, site_code, site_name, page_title)

            # 保存页面数据
            await save_page_data(page_data, page_url, site_code)

            logger.info(f"{site_code}: 页面数据保存成功: {page_url}")

        except Exception as error:
            logger.error(f"{site_code}: 处理页面失败 {page_url}: {error}")

    except Exception as e:
        logger.error(f"{site_code}: 处理网页失败: {e}")


async def extract_page_data(page, page_url: str, site_code: str, site_name: str, page_title: str) -> Dict[str, Any]:
    """提取页面数据 - 仿照 yiya-crawler 的数据提取逻辑"""

    # 提取页面文本内容
    try:
        page_text = await page.evaluate('() => document.body.innerText')
    except:
        page_text = ""

    # 提取页面HTML内容
    try:
        page_html = await page.content()
    except:
        page_html = ""

    # 提取元数据 - 仿照 yiya-crawler 的 meta 提取
    meta_data = {}

    try:
        # 提取 meta 标签
        meta_elements = await page.query_selector_all('meta')
        for element in meta_elements:
            name = await element.get_attribute('name')
            content = await element.get_attribute('content')
            if name and content:
                meta_data[name] = content
    except:
        pass

    # 提取发布时间
    publish_time = ""
    time_selectors = [
        'meta[name="date"]',
        'meta[name="publish_date"]',
        'meta[property="article:published_time"]',
        '.time',
        '.date',
        '.publish-time'
    ]

    for selector in time_selectors:
        try:
            if selector.startswith('meta'):
                element = await page.query_selector(selector)
                if element:
                    publish_time = await element.get_attribute('content')
                    break
            else:
                element = await page.query_selector(selector)
                if element:
                    publish_time = await element.inner_text()
                    break
        except:
            continue

    # 构建页面数据 - 仿照 yiya-crawler 的数据结构
    page_data = {
        "site_domain": urlparse(page_url).netloc,
        "site_name": site_name,
        "site_code": site_code,
        "page_url": page_url,
        "page_type": SPIDER_SITE_TYPE["page"],
        "page_title": page_title,
        "page_content": page_text[:1000] + "..." if len(page_text) > 1000 else page_text,  # 限制长度
        "page_html": page_html[:2000] + "..." if len(page_html) > 2000 else page_html,
        "extra": json.dumps({
            "publish_time": publish_time,
            "meta_data": meta_data,
            "crawl_time": datetime.now().isoformat()
        }),
        "parent_id": None,
        "status": "DONE",
        "created_time": datetime.now().isoformat()
    }

    return page_data


async def save_page_data(page_data: Dict[str, Any], page_url: str, site_code: str):
    """保存页面数据 - 仿照 yiya-crawler 的保存逻辑"""

    # 确保目录存在
    ensure_dir(TEMP_DIR)

    # 生成文件名
    filename = generate_unique_name(page_url, 'json')
    filepath = os.path.join(TEMP_DIR, filename)

    # 保存数据
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(page_data, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"{site_code}: 页面数据已保存: {filepath}")

    except Exception as e:
        logger.error(f"{site_code}: 保存页面数据失败: {e}")


async def createNewPage(site_domain: str, site_name: str, site_code: str, pageUrl: str, dataItem: Dict[str, Any]):
    """创建新页面记录 - 完全仿照 yiya-crawler 的 createNewPage"""

    # 检查该页面是否已经导入 - 简化版本
    existing_file = os.path.join(TEMP_DIR, f"{dataItem.get('title', 'unknown')}.json")

    if os.path.exists(existing_file):
        logger.info(f"{site_code} - pageUrl={pageUrl}: 页面已存在，跳过")
        return

    logger.info(f"createNewPage of {site_code}: pageUrl={pageUrl}")

    # 保存记录到文件 - 仿照 yiya-crawler 的数据结构
    web_page_data = {
        "site_domain": site_domain,
        "site_name": site_name,
        "site_code": site_code,
        "page_url": pageUrl,
        "page_type": SPIDER_SITE_TYPE["page"],
        "page_title": dataItem.get("title", ""),
        "page_content": None,
        "extra": json.dumps({
            "releaseDate": dataItem.get("date", ""),
            "href": dataItem.get("href", ""),
            "title": dataItem.get("title", ""),
            "parentUrl": dataItem.get("parentUrl", "")
        }),
        "parent_id": None,
        "status": "NEW",
        "created_time": datetime.now().isoformat()
    }

    # 保存数据
    filename = generate_unique_name(pageUrl, 'json')
    filepath = os.path.join(TEMP_DIR, filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(web_page_data, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"{site_code}: 新页面记录已保存: {filepath}")

    except Exception as e:
        logger.error(f"{site_code}: 保存新页面记录失败: {e}")