# -*- coding: utf-8 -*-
"""
DrissionPage浏览器引擎 - NMPA爬虫增强版
相比selenium，DrissionPage具有更好的反检测能力和操作效率
"""
import json, time, random
from typing import Any, Dict, List
from DrissionPage import ChromiumPage, ChromiumOptions
from utils import sleep_jitter, deep_find_item_id, extract_required_fields

NMPA_BASE = "https://www.nmpa.gov.cn"

class NMPADrissionCrawler:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.page = None

    def _build_page(self):
        """配置并创建ChromiumPage实例"""
        options = ChromiumOptions()

        # 基础配置
        if self.cfg.get("headless", True):
            options.headless()

        # 反检测配置
        options.set_argument('--disable-gpu')
        options.set_argument('--no-sandbox')
        options.set_argument('--disable-dev-shm-usage')
        options.set_argument('--disable-blink-features=AutomationControlled')
        options.set_argument('--disable-web-security')
        options.set_argument('--allow-running-insecure-content')
        options.set_argument('--disable-extensions')
        options.set_argument('--disable-plugins')
        options.set_argument('--disable-images')

        # 设置真实的User-Agent
        options.set_user_agent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36')

        # 代理配置
        proxy_cfg = self.cfg.get("proxy")
        if proxy_cfg and (proxy_cfg.get("http") or proxy_cfg.get("https")):
            proxy = proxy_cfg.get("https") or proxy_cfg.get("http")
            options.set_proxy(proxy)
            print(f"使用代理: {proxy}")

        # 创建页面实例
        self.page = ChromiumPage(options)

        # 移除webdriver标识
        self.page.remove_ele('navigator.webdriver')

    def start(self):
        """启动浏览器并访问NMPA主页"""
        self._build_page()
        self.page.get(f"{NMPA_BASE}/datasearch/home-index.html")
        # 等待页面加载完成
        sleep_jitter(2000, 3000)

    def stop(self):
        """关闭浏览器"""
        if self.page:
            try:
                self.page.quit()
            except Exception:
                pass

    def get_item_ids(self) -> Dict[str, str]:
        """获取境内/境外药品的itemId"""
        try:
            # 尝试通过API获取
            url = f"{NMPA_BASE}/datasearch/config/NMPA_DATA.json?date={int(time.time() * 1000)}"
            self.page.get(url)

            # 获取响应内容
            content = self.page.html
            if content:
                data = json.loads(content)
                domestic_id = deep_find_item_id(data, "境内生产药品") or ""
                imported_id = deep_find_item_id(data, "境外生产药品") or ""

                if domestic_id and imported_id:
                    return {"domestic": domestic_id, "imported": imported_id}
        except Exception as e:
            print(f"动态获取itemId失败: {e}")

        # 回退到静态配置
        try:
            with open("static_item_ids.json", "r", encoding="utf-8") as f:
                static_map = json.load(f)
            return static_map
        except Exception:
            return {"domestic": "", "imported": ""}

    def _execute_search(self, search_value: str) -> bool:
        """执行搜索操作"""
        try:
            # 等待搜索框加载
            search_input = self.page.ele('css:input[placeholder*="搜索"]', timeout=10)
            if not search_input:
                # 尝试其他可能的选择器
                search_input = self.page.ele('css:input.search-input', timeout=5) or \
                              self.page.ele('css:#searchValue', timeout=5)

            if not search_input:
                print("未找到搜索输入框")
                return False

            # 输入搜索内容
            search_input.clear()
            search_input.input(search_value)

            # 点击搜索按钮
            search_btn = self.page.ele('css:.search-btn', timeout=5) or \
                        self.page.ele('css:button[type="submit"]', timeout=5) or \
                        self.page.ele('css:.btn-search', timeout=5)

            if search_btn:
                search_btn.click()
            else:
                # 如果找不到按钮，尝试回车
                search_input.enter()

            # 等待搜索结果加载
            sleep_jitter(3000, 5000)
            return True

        except Exception as e:
            print(f"搜索操作失败: {e}")
            return False

    def _get_search_results(self) -> List[Dict[str, Any]]:
        """获取当前页面的搜索结果"""
        results = []
        try:
            # 尝试多种可能的结果项选择器
            result_items = self.page.eles('css:.result-item') or \
                          self.page.eles('css:.search-result-item') or \
                          self.page.eles('css:tr[data-id]') or \
                          self.page.eles('css:.data-row')

            for item in result_items:
                try:
                    # 尝试获取文档ID
                    doc_id = item.attr('data-id') or \
                            item.attr('id') or \
                            item.ele('css:[data-docid]').attr('data-docid')

                    if not doc_id:
                        # 尝试从链接中提取ID
                        link = item.ele('css:a')
                        if link:
                            href = link.attr('href')
                            if href and 'id=' in href:
                                doc_id = href.split('id=')[-1].split('&')[0]

                    if doc_id:
                        # 获取显示的文本信息
                        text_content = item.text
                        results.append({
                            'doc_id': str(doc_id),
                            'text_content': text_content,
                            'element': item  # 保存元素引用用于后续点击
                        })
                except Exception:
                    continue

        except Exception as e:
            print(f"获取搜索结果失败: {e}")

        return results

    def _get_detail_by_click(self, result_item: Dict[str, Any]) -> Dict[str, Any]:
        """通过点击获取详细信息"""
        try:
            element = result_item.get('element')
            if not element:
                return {}

            # 滚动到元素可见位置
            element.scroll.to_see()

            # 点击链接或按钮
            link = element.ele('css:a')
            if link:
                link.click()
            else:
                element.click()

            # 等待详情页面加载
            sleep_jitter(2000, 4000)

            # 获取详情页面内容
            detail_content = self.page.html

            # 尝试解析JSON格式的详情
            try:
                # 查找页面中的JSON数据
                scripts = self.page.eles('css:script')
                for script in scripts:
                    script_text = script.text
                    if 'detailData' in script_text or 'detail' in script_text:
                        # 尝试提取JSON
                        import re
                        json_pattern = r'\{[^{}]*"detail[^{}]*\}'
                        matches = re.findall(json_pattern, script_text)
                        for match in matches:
                            try:
                                detail_data = json.loads(match)
                                if isinstance(detail_data, dict):
                                    return detail_data
                            except:
                                continue
            except Exception:
                pass

            # 如果无法解析JSON，返回HTML内容
            return {"html_content": detail_content}

        except Exception as e:
            print(f"获取详情失败: {e}")
            return {}

    def search_once(self, item_id: str, search_value: str, page_num: int, page_size: int) -> List[Dict[str, Any]]:
        """执行一次搜索并返回结果"""
        # 如果是第一页，执行搜索
        if page_num == 1:
            if not self._execute_search(search_value):
                return []

        # 获取当前页结果
        results = self._get_search_results()

        # 如果不是第一页，尝试翻页
        if page_num > 1:
            try:
                # 查找分页控件
                next_btn = self.page.ele(f'css:.pagination a[href*="page={page_num}"]') or \
                           self.page.ele(f'css:.page-link[data-page="{page_num}"]')

                if next_btn:
                    next_btn.click()
                    sleep_jitter(3000, 5000)
                    results = self._get_search_results()
                else:
                    print(f"未找到第{page_num}页的翻页按钮")
                    return []
            except Exception as e:
                print(f"翻页失败: {e}")
                return []

        # 获取详细信息
        detailed_results = []
        for result in results:
            detail = self._get_detail_by_click(result)
            if detail:
                detailed_results.append({
                    'doc_id': result['doc_id'],
                    'detail': detail,
                    'summary': result.get('text_content', '')
                })

            # 返回上一页继续处理其他结果
            if len(detailed_results) > 0:
                self.page.back()
                sleep_jitter(1000, 2000)

        return detailed_results

    def crawl_job(self, dataset: str, code_prefix: str, out_dir: str) -> List[Dict[str, Any]]:
        """爬取指定任务的所有数据"""
        item_ids = self.get_item_ids()
        item_id = item_ids.get(dataset, "")
        if not item_id:
            raise RuntimeError(f"未能找到 {dataset} 的 itemId")

        max_pages = int(self.cfg.get("max_pages", 50))
        page_size = int(self.cfg.get("page_size", 30))

        all_records = []

        for page in range(1, max_pages + 1):
            print(f"正在爬取第 {page} 页...")

            results = self.search_once(item_id, code_prefix, page, page_size)
            if not results:
                break

            for result in results:
                detail = result.get('detail', {})
                fields = extract_required_fields(detail, dataset)
                all_records.append({
                    "fields": fields,
                    "raw": detail,
                    "summary": result.get('summary', '')
                })

            # 延迟防止被封
            sleep_jitter(
                self.cfg.get("delay_min_ms", 600),
                self.cfg.get("delay_max_ms", 1500)
            )

        return all_records