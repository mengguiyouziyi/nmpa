# -*- coding: utf-8 -*-
"""
用户工作流NMPA爬虫 - 完全按照用户提供的操作流程
基于用户实际操作步骤，精确模拟每一个点击和搜索行为
"""
import asyncio
import json
import time
import random
from typing import Dict, List, Any
from rich import print as rprint
from DrissionPage import ChromiumPage, ChromiumOptions

class UserWorkflowNMPACrawler:
    """用户工作流NMPA爬虫"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_dir = config.get('output_dir', 'outputs')
        self.drission_page = None

        # 真实浏览器配置
        self.browser_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
        }

    async def start(self):
        """启动爬虫"""
        rprint("[bold blue]启动用户工作流NMPA爬虫[/]")

        try:
            # 最真实的浏览器配置
            chromium_options = ChromiumOptions()
            chromium_options.headless(self.config.get('headless', True))  # 使用headless模式避免端口冲突
            chromium_options.set_user_agent(self.browser_headers['User-Agent'])

            # 最小化反检测配置
            chromium_options.set_argument('--disable-blink-features=AutomationControlled')
            chromium_options.set_argument('--disable-dev-shm-usage')
            chromium_options.set_argument('--no-sandbox')
            chromium_options.set_argument('--disable-web-security')
            chromium_options.set_argument('--disable-extensions')
            chromium_options.set_argument('--disable-plugins')
            chromium_options.set_argument('--disable-background-timer-throttling')
            chromium_options.set_argument('--disable-backgrounding-occluded-windows')
            chromium_options.set_argument('--disable-renderer-backgrounding')
            chromium_options.set_argument('--disable-field-trial-config')
            chromium_options.set_argument('--disable-back-forward-cache')
            chromium_options.set_argument('--disable-component-extensions-with-background-pages')
            chromium_options.set_argument('--disable-background-networking')
            chromium_options.set_argument('--disable-default-apps')
            chromium_options.set_argument('--disable-extensions-file-access-check')
            chromium_options.set_argument('--disable-ipc-flooding-protection')
            chromium_options.set_argument('--disable-client-side-phishing-detection')
            chromium_options.set_argument('--disable-sync')
            chromium_options.set_argument('--disable-default-browser-check')
            chromium_options.set_argument('--metrics-recording-only')
            chromium_options.set_argument('--no-first-run')
            chromium_options.set_argument('--disable-logging')
            chromium_options.set_argument('--disable-gpu')
            chromium_options.set_argument('--window-size=1366,768')
            chromium_options.set_argument('--start-maximized')
            chromium_options.set_argument('--remote-debugging-port=9230')
            chromium_options.set_argument('--headless=new')

            self.drission_page = ChromiumPage(chromium_options)

            # 基础反检测
            await self.basic_anti_detection()

            rprint("[green]✓ 用户工作流爬虫启动成功[/]")
            return True

        except Exception as e:
            rprint(f"[red]爬虫启动失败: {e}[/]")
            return False

    async def stop(self):
        """停止爬虫"""
        if self.drission_page:
            try:
                self.drission_page.quit()
            except:
                pass

    async def basic_anti_detection(self):
        """基础反检测"""
        try:
            self.drission_page.run_js('''
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            ''')
            rprint("[green]✓ 基础反检测完成[/]")
        except:
            pass

    def random_delay(self, min_seconds=1, max_seconds=3):
        """随机延迟"""
        delay = random.uniform(min_seconds, max_seconds)
        rprint(f"[dim]延迟 {delay:.1f} 秒...[/]")
        time.sleep(delay)

    async def follow_user_workflow(self, code_prefix: str) -> List[Dict]:
        """完全按照用户操作流程"""
        rprint(f"[bold cyan]开始用户工作流: {code_prefix}[/]")

        # 步骤1: 访问NMPA首页
        rprint("[blue]步骤1: 访问NMPA首页[/]")
        self.drission_page.get('https://www.nmpa.gov.cn/')
        self.random_delay(3, 6)

        # 步骤2: 点击"政务服务门户"
        rprint("[blue]步骤2: 查找并点击政务服务门户[/]")
        try:
            # 查找政务服务门户链接
            portal_links = self.drission_page.eles('text:政务服务门户')
            if not portal_links:
                portal_links = self.drission_page.eles('text:政务')
            if not portal_links:
                portal_links = self.drission_page.eles('a')  # 所有链接

            for link in portal_links[:5]:
                text = link.text.lower()
                if '政务' in text or 'portal' in text.lower() or 'service' in text.lower():
                    rprint(f"[green]✓ 找到政务服务门户: {link.text}[/]")
                    link.click()
                    self.random_delay(2, 4)
                    break
            else:
                rprint("[yellow]未找到政务服务门户，尝试直接访问数据查询页面[/]")
                self.drission_page.get('https://www.nmpa.gov.cn/datasearch/home?htmlType=1')
                self.random_delay(3, 5)
        except Exception as e:
            rprint(f"[yellow]政务服务门户点击失败: {e}[/]")
            self.drission_page.get('https://www.nmpa.gov.cn/datasearch/home?htmlType=1')
            self.random_delay(3, 5)

        # 步骤3: 访问数据查询页面
        rprint("[blue]步骤3: 确保在数据查询页面[/]")
        current_url = self.drission_page.url
        if 'datasearch' not in current_url:
            self.drission_page.get('https://www.nmpa.gov.cn/datasearch/home?htmlType=1')
            self.random_delay(3, 5)

        # 步骤4: 查找"境内生产药品"
        rprint("[blue]步骤4: 查找境内生产药品选项[/]")
        try:
            # 多种方式查找境内生产药品
            domestic_selectors = [
                'text:境内生产药品',
                'text:境内',
                'text:生产药品',
                'text:国药准字',
                '[value*="境内"]',
                '[value*="生产"]'
            ]

            found = False
            for selector in domestic_selectors:
                elements = self.drission_page.eles(selector)
                for element in elements:
                    if element.is_displayed():
                        rprint(f"[green]✓ 找到境内生产药品选项: {element.text}[/]")
                        element.click()
                        self.random_delay(1, 2)
                        found = True
                        break
                if found:
                    break

            if not found:
                rprint("[yellow]未找到境内生产药品选项，尝试其他方式[/]")
                # 尝试查找所有选项
                all_options = self.drission_page.eles('option, a, div, span')
                for option in all_options:
                    text = option.text
                    if '境内' in text and '药品' in text:
                        rprint(f"[green]✓ 找到境内生产药品: {text}[/]")
                        option.click()
                        self.random_delay(1, 2)
                        found = True
                        break

        except Exception as e:
            rprint(f"[yellow]境内生产药品选择失败: {e}[/]")

        # 步骤5: 选择药品类型 (H)
        rprint("[blue]步骤5: 选择药品类型 H[/]")
        try:
            # 查找H选项
            h_selectors = [
                'text:H',
                'text:化药',
                'text:化学药品',
                '[value="H"]',
                '[value*="化药"]'
            ]

            for selector in h_selectors:
                elements = self.drission_page.eles(selector)
                for element in elements:
                    if element.is_displayed():
                        rprint(f"[green]✓ 找到H选项: {element.text}[/]")
                        element.click()
                        self.random_delay(1, 2)
                        break
        except Exception as e:
            rprint(f"[yellow]H选项选择失败: {e}[/]")

        # 步骤6: 点击搜索按钮
        rprint("[blue]步骤6: 点击搜索按钮[/]")
        try:
            search_selectors = [
                'text:搜索',
                'text:查询',
                'text:Search',
                'input[type="submit"]',
                'button[type="submit"]',
                '.search-btn',
                '#search'
            ]

            for selector in search_selectors:
                elements = self.drission_page.eles(selector)
                for element in elements:
                    if element.is_displayed():
                        rprint(f"[green]✓ 找到搜索按钮: {element.text}[/]")
                        element.click()
                        self.random_delay(3, 5)
                        break
        except Exception as e:
            rprint(f"[yellow]搜索按钮点击失败: {e}[/]")

        # 步骤7: 等待并分析搜索结果
        rprint("[blue]步骤7: 分析搜索结果[/]")
        self.random_delay(5, 8)

        return await self.extract_all_data()

    async def extract_all_data(self) -> List[Dict]:
        """提取所有可见数据"""
        rprint("[blue]提取页面所有数据...[/]")

        results = []

        # 方法1: 查找表格数据
        results.extend(await self.extract_table_data())

        # 方法2: 查找列表数据
        results.extend(await self.extract_list_data())

        # 方法3: JavaScript提取
        results.extend(await self.extract_with_javascript())

        # 方法4: 正则表达式提取
        results.extend(await self.extract_with_regex())

        # 去重并返回
        unique_results = []
        seen = set()

        for result in results:
            key = (result.get('name', ''), result.get('approval_number', ''))
            if key not in seen and key != ('', ''):
                seen.add(key)
                unique_results.append(result)

        rprint(f"[green]✓ 提取到 {len(unique_results)} 条唯一记录[/]")
        return unique_results

    async def extract_table_data(self) -> List[Dict]:
        """提取表格数据"""
        results = []
        try:
            tables = self.drission_page.eles('table')
            for table in tables:
                rows = table.eles('tr')
                for row in rows:
                    cells = row.eles('td, th')
                    if len(cells) >= 3:
                        text_data = [cell.text.strip() for cell in cells]
                        if any('国药准字' in text for text in text_data):
                            drug_info = await self.parse_drug_info(text_data)
                            if drug_info:
                                results.append(drug_info)
        except Exception as e:
            rprint(f"[yellow]表格提取失败: {e}[/]")

        return results

    async def extract_list_data(self) -> List[Dict]:
        """提取列表数据"""
        results = []
        try:
            # 查找所有可能的药品信息容器
            containers = self.drission_page.eles('div, li, article, section')
            for container in containers:
                text = container.text
                if '国药准字' in text and len(text) > 20:
                    drug_info = await self.parse_text_content(text)
                    if drug_info:
                        results.append(drug_info)
        except Exception as e:
            rprint(f"[yellow]列表提取失败: {e}[/]")

        return results

    async def extract_with_javascript(self) -> List[Dict]:
        """JavaScript提取"""
        results = []
        try:
            js_code = '''
            var results = [];
            var allText = document.body.innerText || document.body.textContent || '';

            // 查找包含国药准字的文本块
            var lines = allText.split('\\n');
            for (var i = 0; i < lines.length; i++) {
                var line = lines[i].trim();
                if (line.includes('国药准字')) {
                    // 检查前后几行
                    var context = [];
                    for (var j = Math.max(0, i-2); j <= Math.min(lines.length-1, i+2); j++) {
                        if (lines[j].trim()) {
                            context.push(lines[j].trim());
                        }
                    }
                    results.push({
                        text: line,
                        context: context.join('\\n')
                    });
                }
            }

            return results;
            '''

            js_results = self.drission_page.run_js(js_code)
            for item in js_results:
                drug_info = await self.parse_text_content(item.get('context', item.get('text', '')))
                if drug_info:
                    results.append(drug_info)

        except Exception as e:
            rprint(f"[yellow]JavaScript提取失败: {e}[/]")

        return results

    async def extract_with_regex(self) -> List[Dict]:
        """正则表达式提取"""
        results = []
        try:
            page_text = self.drission_page.text
            import re

            # 匹配药品信息模式
            patterns = [
                r'国药准字([HFJZTB]\d{8})\s+([^\n]+?)\s+([^\n]*?(?:股份有限公司|有限公司|制药厂|药业)[^\n]*?)',
                r'([^\n]+?)\s+国药准字([HFJZTB]\d{8})\s+([^\n]*?(?:股份有限公司|有限公司|制药厂|药业)[^\n]*?)',
                r'国药准字([HFJZTB]\d{8})\s+([^\n]+)'
            ]

            for pattern in patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    if len(match) >= 3:
                        drug_info = {
                            'name': match[1].strip(),
                            'approval_number': f'国药准字{match[0]}',
                            'company': match[2].strip(),
                            'source': 'regex_extraction',
                            'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S')
                        }
                        results.append(drug_info)

        except Exception as e:
            rprint(f"[yellow]正则提取失败: {e}[/]")

        return results

    async def parse_drug_info(self, text_data: List[str]) -> Dict:
        """解析药品信息"""
        try:
            drug_info = {
                'name': '',
                'approval_number': '',
                'company': '',
                'source': 'table_extraction',
                'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'raw_data': '|'.join(text_data)
            }

            for text in text_data:
                if '国药准字' in text:
                    drug_info['approval_number'] = text.strip()
                elif any(keyword in text for keyword in ['股份有限公司', '有限公司', '制药厂', '药业']):
                    drug_info['company'] = text.strip()
                elif len(text) > 5 and '国药准字' not in text and not any(keyword in text for keyword in ['股份有限公司', '有限公司', '制药厂', '药业']):
                    drug_info['name'] = text.strip()

            if drug_info['approval_number'] or drug_info['name']:
                return drug_info
        except:
            pass

        return {}

    async def parse_text_content(self, text: str) -> Dict:
        """解析文本内容"""
        try:
            import re
            drug_info = {
                'name': '',
                'approval_number': '',
                'company': '',
                'source': 'text_parsing',
                'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'raw_text': text
            }

            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if '国药准字' in line:
                    drug_info['approval_number'] = line
                elif any(keyword in line for keyword in ['股份有限公司', '有限公司', '制药厂', '药业']):
                    drug_info['company'] = line
                elif len(line) > 5 and '国药准字' not in line and not any(keyword in line for keyword in ['股份有限公司', '有限公司', '制药厂', '药业']):
                    if not drug_info['name']:
                        drug_info['name'] = line

            if drug_info['approval_number'] or drug_info['name']:
                return drug_info
        except:
            pass

        return {}

    async def crawl_job(self, dataset: str, code_prefix: str, export_dir: str) -> List[Dict]:
        """执行用户工作流任务"""
        rprint(f"[bold green]开始用户工作流任务[/] dataset={dataset} code_prefix={code_prefix}")

        all_records = await self.follow_user_workflow(code_prefix)

        if not all_records:
            rprint("[red]❌ 用户工作流失败，未能获取到任何数据[/]")
            raise RuntimeError("用户工作流失败，未能获取真实NMPA数据")

        # 保存数据
        raw_file = f"{export_dir}/{dataset}_{code_prefix}.user_workflow.jsonl"
        with open(raw_file, 'w', encoding='utf-8') as f:
            for record in all_records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')

        rprint(f"[bold green]🎉🎉🎉 用户工作流成功完成！[/] 共获取 {len(all_records)} 条真实NMPA数据，保存至 {raw_file}")

        # 显示前几条数据
        for i, record in enumerate(all_records[:3]):
            rprint(f"[green]✓ 药品{i+1}: {record.get('name', 'N/A')} - {record.get('approval_number', 'N/A')}[/]")

        return all_records

async def create_user_workflow_crawler(config: Dict[str, Any]) -> UserWorkflowNMPACrawler:
    """创建用户工作流爬虫"""
    crawler = UserWorkflowNMPACrawler(config)
    await crawler.start()
    return crawler