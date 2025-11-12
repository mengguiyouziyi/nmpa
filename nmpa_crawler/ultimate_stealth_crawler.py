# -*- coding: utf-8 -*-
"""
终极隐匿爬虫 - 对抗NMPA企业级多层防护系统
使用浏览器指纹随机化、Canvas指纹伪装、WebGL伪装等高级技术
"""
import asyncio
import json
import time
import random
import re
import hashlib
import base64
from typing import Dict, List, Any
from rich import print as rprint

class UltimateStealthCrawler:
    """终极隐匿爬虫 - 使用最先进的反检测技术"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_dir = config.get('output_dir', 'outputs')
        self.playwright = None
        self.browser = None
        self.page = None
        self.context = None

        # 生成随机化的浏览器指纹
        self.browser_fingerprint = self.generate_randomized_fingerprint()

    def generate_randomized_fingerprint(self) -> Dict:
        """生成随机化的浏览器指纹以对抗指纹识别"""

        # 随机选择Chrome版本
        chrome_versions = [
            "131.0.0.0", "130.0.6723.116", "129.0.6668.89",
            "128.0.6613.137", "127.0.6533.120"
        ]

        # 随机Windows版本
        windows_versions = [
            "Windows NT 10.0; Win64; x64",
            "Windows NT 10.0; WOW64",
            "Windows NT 6.1; Win64; x64"
        ]

        # 随机屏幕分辨率
        resolutions = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1440, "height": 900},
            {"width": 1536, "height": 864}
        ]

        selected_version = random.choice(chrome_versions)
        selected_windows = random.choice(windows_versions)
        selected_resolution = random.choice(resolutions)

        return {
            'user_agent': f'Mozilla/5.0 ({selected_windows}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{selected_version} Safari/537.36',
            'accept_language': random.choice([
                'zh-CN,zh;q=0.9,en;q=0.8',
                'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
                'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7'
            ]),
            'accept_encoding': 'gzip, deflate, br, zstd',
            'platform': 'Win32',
            'sec_ch_ua': f'"Google Chrome";v="{selected_version.split(".")[0]}", "Chromium";v="{selected_version.split(".")[0]}", "Not_A Brand";v="24"',
            'sec_ch_ua_mobile': '?0',
            'sec_ch_ua_platform': '"Windows"',
            'viewport': selected_resolution,
            'timezone': random.choice(['Asia/Shanghai', 'Asia/Beijing', 'Asia/Hong_Kong']),
            'geolocation': {
                'latitude': random.uniform(39.8, 40.1),
                'longitude': random.uniform(116.3, 116.5)
            },
            'permissions': ['geolocation', 'notifications'],
            'color_scheme': 'light',
            'reduced_motion': 'reduce',
            'hardware_concurrency': random.choice([4, 8, 12, 16]),
            'device_memory': random.choice([4, 8, 16])
        }

    async def start(self):
        """启动终极隐匿爬虫"""
        rprint("[bold blue]启动终极隐匿NMPA爬虫（企业级反检测技术）[/]")

        try:
            # 安装并导入Playwright
            try:
                from playwright.async_api import async_playwright
            except ImportError:
                rprint("[yellow]安装Playwright...[/]")
                import subprocess
                subprocess.run(['python', '-m', 'pip', 'install', 'playwright'], check=True)
                subprocess.run(['playwright', 'install', 'chromium'], check=True)
                from playwright.async_api import async_playwright

            self.playwright = await async_playwright().start()

            # 启动隐匿浏览器
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.get('headless', True),
                args=[
                    '--no-blink-features=AutomationControlled',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                    '--disable-background-networking',
                    '--disable-default-browser-check',
                    '--disable-component-extensions-with-background-pages',
                    '--disable-client-side-phishing-detection',
                    '--disable-sync',
                    '--disable-default-apps',
                    '--metrics-recording-only',
                    '--no-first-run',
                    '--disable-background-logging',
                    '--disable-logging',
                    '--disable-gpu',
                    '--enable-features=NetworkService,NetworkServiceInProcess',
                    '--password-store=basic',
                    '--use-mock-keychain',
                    '--excludeSwitches=enable-automation',
                    '--disable-infobars',
                    f'--window-size={self.browser_fingerprint["viewport"]["width"]},{self.browser_fingerprint["viewport"]["height"]}',
                    '--start-maximized',
                    '--disable-features=VizDisplayCompositor'
                ]
            )

            # 创建隐匿浏览器上下文
            self.context = await self.browser.new_context(
                viewport=self.browser_fingerprint['viewport'],
                user_agent=self.browser_fingerprint['user_agent'],
                locale='zh-CN',
                timezone_id=self.browser_fingerprint['timezone'],
                permissions=self.browser_fingerprint['permissions'],
                geolocation=self.browser_fingerprint['geolocation'],
                color_scheme=self.browser_fingerprint['color_scheme'],
                reduced_motion=self.browser_fingerprint['reduced_motion'],
                device_scale_factor=1.0,
                # 随机化额外参数
                extra_http_headers={
                    'Accept-Language': self.browser_fingerprint['accept_language'],
                    'Accept-Encoding': self.browser_fingerprint['accept_encoding'],
                    'sec-ch-ua': self.browser_fingerprint['sec_ch_ua'],
                    'sec-ch-ua-mobile': self.browser_fingerprint['sec_ch_ua_mobile'],
                    'sec-ch-ua-platform': self.browser_fingerprint['sec_ch_ua_platform'],
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1'
                }
            )

            # 添加终极反检测脚本
            await self.context.add_init_script(f"""
                // === 终极反检测脚本 ===

                // 1. 移除webdriver标识
                Object.defineProperty(navigator, 'webdriver', {{
                    get: () => undefined,
                    configurable: true
                }});

                // 2. 移除自动化标识
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Function;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_String;

                // 3. 伪造Chrome对象
                window.chrome = {{
                    runtime: {{
                        onConnect: undefined,
                        onMessage: undefined,
                        connect: function() {{ return {{}}; }}
                    }},
                    loadTimes: function() {{
                        return {{
                            requestTime: Math.random() * 100,
                            loadTime: Math.random() * 100 + 100
                        }};
                    }},
                    csi: function() {{
                        return {{
                            pageT: Math.random() * 1000,
                            startE: Math.random() * 1000,
                            tran: Math.random() * 100
                        }};
                    }},
                    app: {{
                        isInstalled: false,
                        InstallState: {{
                            DISABLED: 'disabled',
                            INSTALLED: 'installed',
                            NOT_INSTALLED: 'not_installed'
                        }}
                    }}
                }};

                // 4. 伪造Navigator属性
                Object.defineProperty(navigator, 'plugins', {{
                    get: () => [
                        {{
                            name: 'Chrome PDF Plugin',
                            filename: 'internal-pdf-viewer',
                            description: 'Portable Document Format'
                        }},
                        {{
                            name: 'Chrome PDF Viewer',
                            filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                            description: 'Portable Document Format'
                        }},
                        {{
                            name: 'Native Client',
                            filename: 'internal-nacl-plugin',
                            description: 'Native Client'
                        }}
                    ]
                }});

                // 5. 伪造语言
                Object.defineProperty(navigator, 'language', {{
                    get: () => '{self.browser_fingerprint['accept_language'].split(',')[0]}'
                }});

                // 6. 伪造硬件信息
                Object.defineProperty(navigator, 'hardwareConcurrency', {{
                    get: () => {self.browser_fingerprint['hardware_concurrency']}
                }});

                Object.defineProperty(navigator, 'deviceMemory', {{
                    get: () => {self.browser_fingerprint['device_memory']}
                }});

                // 7. 伪造Canvas指纹
                const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = function(type) {{
                    // 添加随机噪声
                    const context = this.getContext('2d');
                    if (context) {{
                        const imageData = context.getImageData(0, 0, this.width, this.height);
                        for (let i = 0; i < imageData.data.length; i += 4) {{
                            imageData.data[i] += Math.floor(Math.random() * 3) - 1;
                            imageData.data[i + 1] += Math.floor(Math.random() * 3) - 1;
                            imageData.data[i + 2] += Math.floor(Math.random() * 3) - 1;
                        }}
                        context.putImageData(imageData, 0, 0);
                    }}
                    return originalToDataURL.apply(this, arguments);
                }};

                // 8. 伪造WebGL指纹
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                    if (parameter === 37445) {{
                        // UNMASKED_VENDOR_WEBGL
                        return 'Intel Inc.';
                    }}
                    if (parameter === 37446) {{
                        // UNMASKED_RENDERER_WEBGL
                        return 'Intel Iris OpenGL Engine';
                    }}
                    return getParameter.apply(this, arguments);
                }};

                // 9. 伪造时区
                const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
                Date.prototype.getTimezoneOffset = function() {{
                    return -480; // UTC+8
                }};

                // 10. 移除自动化检测变量
                delete window._phantom;
                delete window.callPhantom;
                delete window.__nightmare;
                delete window._selenium;
                delete window.webdriver;
                delete window.__webdriver_evaluate;
                delete window.__selenium_evaluate;
                delete window.__webdriver_script_fn;
                delete window.fxdriver_id;
                delete window.__driver_unwrapped;
                delete window.webdriver_id;
                delete window.__fxdriver_unwrapped;
                delete window._Selenium_IDE_Recorder;

                // 11. 伪造权限API
                const originalQuery = navigator.permissions.query;
                navigator.permissions.query = function(parameters) {{
                    if (parameters.name === 'notifications') {{
                        return Promise.resolve({{ state: 'granted' }});
                    }}
                    return originalQuery.apply(this, arguments);
                }};

                // 12. 添加真实的交互历史
                window.performance = window.performance || {{}};
                window.performance.navigation = {{
                    type: 1,
                    redirectCount: 0
                }};

                // 13. 伪造cookieEnabled
                Object.defineProperty(navigator, 'cookieEnabled', {{
                    get: () => true
                }});

                // 14. 伪造doNotTrack
                Object.defineProperty(navigator, 'doNotTrack', {{
                    get: () => '1'
                }});

                console.log('🛡️ 终极反检测脚本加载完成');
            """)

            # 创建页面
            self.page = await self.context.new_page()

            # 设置额外的请求头
            await self.page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': self.browser_fingerprint['accept_language'],
                'Cache-Control': 'max-age=0',
                'sec-ch-ua': self.browser_fingerprint['sec_ch_ua'],
                'sec-ch-ua-mobile': self.browser_fingerprint['sec_ch_ua_mobile'],
                'sec-ch-ua-platform': self.browser_fingerprint['sec_ch_ua_platform'],
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'Connection': 'keep-alive'
            })

            rprint("[green]✅ 终极隐匿爬虫启动成功[/]")
            return True

        except Exception as e:
            rprint(f"[red]爬虫启动失败: {e}[/]")
            return False

    async def stop(self):
        """停止爬虫"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except:
            pass

    def smart_delay(self, base: float = 2.0, variation: float = 3.0):
        """智能延迟"""
        delay = base + random.uniform(0, variation)
        rprint(f"[dim]智能延迟 {delay:.1f} 秒...[/]")
        time.sleep(delay)

    async def simulate_natural_human_behavior(self):
        """模拟更自然的人类行为"""
        rprint("[blue]模拟自然人类浏览行为...[/]")

        try:
            # 随机鼠标轨迹（贝塞尔曲线移动）
            start_x = random.randint(100, 500)
            start_y = random.randint(100, 400)
            end_x = random.randint(800, 1200)
            end_y = random.randint(300, 600)

            # 分步骤移动鼠标，模拟真实轨迹
            steps = 10
            for i in range(steps):
                progress = (i + 1) / steps
                # 添加随机抖动
                jitter_x = random.randint(-20, 20)
                jitter_y = random.randint(-20, 20)

                current_x = int(start_x + (end_x - start_x) * progress + jitter_x)
                current_y = int(start_y + (end_y - start_y) * progress + jitter_y)

                await self.page.mouse.move(current_x, current_y)
                await asyncio.sleep(random.uniform(0.05, 0.15))

            # 随机滚动（模拟阅读行为）
            scroll_count = random.randint(2, 4)
            for _ in range(scroll_count):
                scroll_distance = random.randint(200, 500)
                await self.page.mouse.wheel(0, scroll_distance)
                await asyncio.sleep(random.uniform(0.8, 2.0))

            # 偶尔向上滚动（模拟回看）
            if random.random() > 0.6:
                scroll_up = random.randint(100, 300)
                await self.page.mouse.wheel(0, -scroll_up)
                await asyncio.sleep(random.uniform(0.5, 1.5))

            # 随机停顿（模拟思考）
            await asyncio.sleep(random.uniform(1.0, 3.0))

        except Exception as e:
            rprint(f"[yellow]人类行为模拟失败: {e}[/]")

    async def advanced_bypass_protection(self, url: str) -> bool:
        """高级绕过保护 - 使用多种策略"""
        rprint(f"[bold cyan]高级绕过保护: {url}[/]")

        try:
            # 策略1: 直接访问 + 渐进式加载
            rprint("[blue]策略1: 渐进式加载[/]")

            # 先访问一个简单的页面建立信任
            await self.page.goto('https://www.baidu.com', wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(2)

            # 然后访问目标页面
            response = await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)

            if response and response.status == 200:
                rprint("[green]✅ 策略1成功[/]")

                # 额外等待确保页面完全渲染
                await asyncio.sleep(5)

                # 检查页面是否有内容
                page_content = await self.page.content()
                if len(page_content) > 1000:
                    return True

            # 策略2: 通过iframe绕过
            rprint("[blue]策略2: iframe绕过[/]")

            # 创建iframe
            iframe_script = f"""
                const iframe = document.createElement('iframe');
                iframe.src = '{url}';
                iframe.style.width = '100%';
                iframe.style.height = '100vh';
                iframe.style.border = 'none';
                document.body.innerHTML = '';
                document.body.appendChild(iframe);
            """
            await self.page.evaluate(iframe_script)

            # 等待iframe加载
            await asyncio.sleep(8)

            # 检查iframe内容
            iframe_content = await self.page.evaluate("""
                const iframe = document.querySelector('iframe');
                if (iframe && iframe.contentDocument) {
                    return iframe.contentDocument.documentElement.outerHTML;
                }
                return '';
            """)

            if len(iframe_content) > 1000:
                rprint("[green]✅ 策略2成功[/]")
                return True

            # 策略3: JavaScript动态加载
            rprint("[blue]策略3: JavaScript动态加载[/]")

            # 清空页面并动态加载内容
            dynamic_script = f"""
                document.body.innerHTML = '';
                const script = document.createElement('script');
                script.text = `
                    fetch('{url}')
                        .then(response => response.text())
                        .then(html => {{
                            document.body.innerHTML = html;
                            const scripts = document.querySelectorAll('script');
                            scripts.forEach(script => {{
                                if (script.src) {{
                                    const newScript = document.createElement('script');
                                    newScript.src = script.src;
                                    document.head.appendChild(newScript);
                                }}
                            }});
                        }})
                        .catch(error => console.error('加载失败:', error));
                `;
                document.head.appendChild(script);
            """
            await self.page.evaluate(dynamic_script)

            # 等待动态加载完成
            await asyncio.sleep(10)

            # 检查加载结果
            dynamic_content = await self.page.content()
            if len(dynamic_content) > 1000:
                rprint("[green]✅ 策略3成功[/]")
                return True

        except Exception as e:
            rprint(f"[yellow]高级绕过保护失败: {e}[/]")
            return False

        return False

    async def extract_data_with_advanced_techniques(self) -> List[Dict]:
        """使用高级技术提取数据"""
        rprint("[bold magenta]高级数据提取方案[/]")

        try:
            # 等待页面稳定
            rprint("[blue]等待页面稳定加载...[/]")
            await asyncio.sleep(15)

            # 获取当前页面信息
            current_url = self.page.url
            rprint(f"[cyan]当前页面URL: {current_url}[/]")

            # 多种方法获取页面内容
            contents = {}

            # 方法1: 直接获取HTML
            try:
                html_content = await self.page.content()
                contents['direct_html'] = html_content
                rprint(f"[cyan]直接HTML长度: {len(html_content)} 字符[/]")
            except Exception as e:
                rprint(f"[yellow]直接HTML获取失败: {e}[/]")

            # 方法2: 获取渲染后的文本
            try:
                text_content = await self.page.evaluate("() => document.body.innerText || document.body.textContent || ''")
                contents['text'] = text_content
                rprint(f"[cyan]页面文本长度: {len(text_content)} 字符[/]")
            except Exception as e:
                rprint(f"[yellow]文本获取失败: {e}[/]")

            # 方法3: 获取所有链接
            try:
                links = await self.page.evaluate("""
                    () => Array.from(document.querySelectorAll('a')).map(a => ({
                        text: a.innerText,
                        href: a.href,
                        title: a.title
                    }))
                """)
                contents['links'] = links
                rprint(f"[cyan]找到 {len(links)} 个链接[/]")
            except Exception as e:
                rprint(f"[yellow]链接获取失败: {e}[/]")

            # 方法4: 获取表格数据
            try:
                tables = await self.page.evaluate("""
                    () => Array.from(document.querySelectorAll('table')).map(table =>
                        Array.from(table.querySelectorAll('tr')).map(row =>
                            Array.from(row.querySelectorAll('td')).map(cell => cell.innerText)
                        )
                    )
                """)
                contents['tables'] = tables
                rprint(f"[cyan]找到 {len(tables)} 个表格[/]")
            except Exception as e:
                rprint(f"[yellow]表格获取失败: {e}[/]")

            # 分析内容并提取药品数据
            all_results = []

            # 从文本中提取药品信息
            if 'text' in contents and contents['text']:
                text = contents['text']
                patterns = [
                    r'([^\\n]{2,50}?)\\s*[,，]\\s*国药准字([HFJZTB]\\d{8})\\s*[,，]\\s*([^\\n]{5,100}?(?:股份有限公司|有限公司|制药厂|药业)[^\\n]*)',
                    r'国药准字([HFJZTB]\\d{8})\\s*[,，]\\s*([^\\n]{2,50}?)\\s*[,，]\\s*([^\\n]{5,100}?(?:股份有限公司|有限公司|制药厂|药业)[^\\n]*)',
                ]

                for i, pattern in enumerate(patterns):
                    matches = re.findall(pattern, text)
                    rprint(f"[blue]文本模式{i+1}匹配到 {len(matches)} 条记录[/]")

                    for match in matches:
                        if len(match) >= 3:
                            drug_info = {
                                'name': match[0].strip() if not match[0].startswith('国药准字') else match[1].strip(),
                                'approval_number': f'国药准字{match[1]}' if not match[1].startswith('国药准字') else match[0].strip(),
                                'company': match[2].strip(),
                                'source': f'text_pattern_{i+1}',
                                'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S')
                            }

                            if drug_info['name'] and len(drug_info['name']) > 2 and drug_info['company']:
                                all_results.append(drug_info)

            # 从表格中提取药品信息
            if 'tables' in contents:
                for table_idx, table in enumerate(contents['tables']):
                    for row_idx, row in enumerate(table):
                        if len(row) >= 3 and any('国药准字' in cell for cell in row):
                            # 查找包含批准文号的单元格
                            approval_cell = ''
                            name_cell = ''
                            company_cell = ''

                            for cell in row:
                                if '国药准字' in cell:
                                    approval_cell = cell
                                elif len(cell) > 2 and not company_cell:
                                    name_cell = cell
                                elif any(keyword in cell for keyword in ['股份', '有限', '制药', '药业']):
                                    company_cell = cell

                            if approval_cell and name_cell:
                                drug_info = {
                                    'name': name_cell.strip(),
                                    'approval_number': approval_cell.strip(),
                                    'company': company_cell.strip() if company_cell else '',
                                    'source': f'table_{table_idx}_row_{row_idx}',
                                    'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S')
                                }

                                if len(drug_info['name']) > 2:
                                    all_results.append(drug_info)

            # 从链接中提取药品信息
            if 'links' in contents:
                for link in contents['links']:
                    text = link.get('text', '')
                    if '国药准字' in text and len(text) > 10:
                        # 使用正则表达式提取
                        patterns = [
                            r'([^，。\\n]*?)\\s*[,，]\\s*国药准字([HFJZTB]\\d{8})\\s*[,，]\\s*([^，。\\n]*?(?:股份有限公司|有限公司|制药厂|药业)[^，。\\n]*)',
                        ]

                        for pattern in patterns:
                            matches = re.findall(pattern, text)
                            for match in matches:
                                if len(match) >= 3:
                                    drug_info = {
                                        'name': match[0].strip(),
                                        'approval_number': f'国药准字{match[1]}',
                                        'company': match[2].strip(),
                                        'source': 'link_extraction',
                                        'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S')
                                    }

                                    if len(drug_info['name']) > 2:
                                        all_results.append(drug_info)

            # 去重并验证
            unique_results = []
            seen = set()

            for result in all_results:
                key = (result.get('approval_number', ''), result.get('name', ''))
                if key not in seen and key != ('', ''):
                    seen.add(key)
                    unique_results.append(result)

            rprint(f"[green]✅ 高级提取成功！去重后共 {len(unique_results)} 条药品数据[/]")

            # 显示前几条数据
            for i, result in enumerate(unique_results[:5]):
                rprint(f"[green]✓ 药品{i+1}: {result.get('name', 'N/A')} - {result.get('approval_number', 'N/A')}[/]")

            return unique_results

        except Exception as e:
            rprint(f"[red]高级数据提取失败: {e}[/]")
            return []

    async def crawl_job(self, dataset: str, code_prefix: str, export_dir: str) -> List[Dict]:
        """执行终极隐匿任务"""
        rprint(f"[bold green]开始终极隐匿任务[/] dataset={dataset} code_prefix={code_prefix}")

        all_records = []

        # 步骤1: 访问NMPA首页
        rprint("[blue]步骤1: 访问NMPA首页[/]")
        if not await self.advanced_bypass_protection('https://www.nmpa.gov.cn/'):
            rprint("[red]❌ 无法访问NMPA首页[/]")
            return []

        await self.simulate_natural_human_behavior()
        self.smart_delay(3, 6)

        # 步骤2: 访问数据查询页面
        rprint("[blue]步骤2: 访问数据查询页面[/]")
        if not await self.advanced_bypass_protection('https://www.nmpa.gov.cn/datasearch/home?htmlType=1'):
            rprint("[red]❌ 无法访问数据查询页面[/]")
            return []

        await self.simulate_natural_human_behavior()
        self.smart_delay(5, 8)

        # 步骤3: 尝试交互操作
        rprint("[blue]步骤3: 尝试交互操作[/]")

        # 尝试搜索
        try:
            search_selectors = [
                'input[placeholder*="搜索"]',
                'input[placeholder*="查询"]',
                'input[type="search"]',
                'input[name*="search"]'
            ]

            for selector in search_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        await element.click()
                        await element.type("阿司匹林", delay=random.uniform(100, 200))
                        rprint(f"[green]✅ 搜索框操作成功: {selector}[/]")

                        # 尝试提交搜索
                        await element.press('Enter')
                        self.smart_delay(3, 5)
                        break
                except:
                    continue
        except Exception as e:
            rprint(f"[yellow]搜索操作失败: {e}[/]")

        # 步骤4: 高级数据提取
        rprint("[blue]步骤4: 高级数据提取[/]")
        self.smart_delay(5, 10)

        results = await self.extract_data_with_advanced_techniques()

        if results:
            all_records.extend(results)
            rprint(f"[green]✅ 终极隐匿突破成功！获取 {len(results)} 条药品数据！[/]")
        else:
            rprint("[red]❌ 终极隐匿突破失败，未能获取到任何数据[/]")
            raise RuntimeError("终极隐匿突破失败，未能获取真实NMPA数据")

        # 保存数据
        raw_file = f"{export_dir}/{dataset}_{code_prefix}.ultimate_stealth.jsonl"
        with open(raw_file, 'w', encoding='utf-8') as f:
            for record in all_records:
                f.write(json.dumps(record, ensure_ascii=False) + '\\n')

        rprint(f"[bold green]🎉🎉🎉 终极隐匿突破成功完成！[/] 共获取 {len(all_records)} 条真实NMPA数据，保存至 {raw_file}")

        return all_records

async def create_ultimate_stealth_crawler(config: Dict[str, Any]) -> UltimateStealthCrawler:
    """创建终极隐匿爬虫"""
    crawler = UltimateStealthCrawler(config)
    await crawler.start()
    return crawler