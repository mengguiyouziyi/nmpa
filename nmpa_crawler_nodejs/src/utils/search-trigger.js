// 搜索触发器 - 基于Python ultimate_solution.py的_trigger_real_search逻辑
import NMPASignatureCracker from './signature-cracker.js';
import RequestInterceptor from './request-interceptor.js';

export class SearchTrigger {
    constructor(page) {
        this.page = page;
        this.signatureCracker = new NMPASignatureCracker();
        this.interceptor = new RequestInterceptor();
    }

    /**
     * 触发真实搜索以捕获签名
     * 对应Python版本的_trigger_real_search
     */
    async triggerRealSearch(searchValue) {
        console.log(`🎯 触发真实搜索: ${searchValue}`);

        try {
            // 等待页面完全加载
            await this.page.waitForTimeout(5000);

            // 查找并触发搜索框的多种方式
            const searchInput = await this.findSearchInput();

            if (searchInput) {
                console.log(`✅ 找到搜索框，输入: ${searchValue}`);

                // 清空并输入搜索内容
                await searchInput.clear();
                await this.page.waitForTimeout(1000);
                await searchInput.type(searchValue);
                await this.page.waitForTimeout(1000);

                // 查找并点击搜索按钮
                const searchButton = await this.findSearchButton();

                if (searchButton) {
                    console.log('✅ 点击搜索按钮');
                    await searchButton.click();
                    await this.page.waitForTimeout(5000);
                    return true;
                } else {
                    console.log('⚡ 尝试按Enter键搜索');
                    await searchInput.press('Enter');
                    await this.page.waitForTimeout(5000);
                    return true;
                }
            }

            // 如果没找到搜索框，尝试JavaScript触发搜索
            console.log('⚡ 尝试JavaScript触发搜索');
            return await this.triggerJSSearch(searchValue);

        } catch (error) {
            console.error(`触发搜索失败: ${error.message}`);
            return false;
        }
    }

    /**
     * 查找搜索框
     */
    async findSearchInput() {
        const searchSelectors = [
            'input[placeholder*="搜索"]',
            'input[placeholder*="输入"]',
            'input[type="text"]',
            '.search-input',
            '#searchInput',
            'input[name*="search"]',
            'input[name*="keyword"]',
            '#qt', // NMPA特定搜索框ID
            '.search-text'
        ];

        for (const selector of searchSelectors) {
            try {
                const elements = await this.page.$$(selector);
                for (const element of elements) {
                    const isVisible = await element.isVisible();
                    const isEnabled = await element.isEnabled();
                    if (isVisible && isEnabled) {
                        console.log(`找到搜索框: ${selector}`);
                        return element;
                    }
                }
            } catch (error) {
                continue;
            }
        }

        return null;
    }

    /**
     * 查找搜索按钮
     */
    async findSearchButton() {
        const buttonSelectors = [
            'button[type="submit"]',
            '.search-btn',
            '.btn-search',
            'button[aria-label*="搜索"]',
            'input[type="submit"]',
            '.search-button',
            '#sosbtn', // NMPA特定搜索按钮ID
            '.search-btn'
        ];

        for (const selector of buttonSelectors) {
            try {
                const elements = await this.page.$$(selector);
                for (const element of elements) {
                    const isVisible = await element.isVisible();
                    const isEnabled = await element.isEnabled();
                    if (isVisible && isEnabled) {
                        return element;
                    }
                }
            } catch (error) {
                continue;
            }
        }

        return null;
    }

    /**
     * JavaScript触发搜索
     * 对应Python版本的_trigger_js_search
     */
    async triggerJSSearch(searchValue) {
        const jsCodes = [
            // 方式1: 使用fetch（基础版本）
            `
            const timestamp = Date.now();
            const url = '/datasearch/data/nmpadata/search?itemId=ff80808183cad75001840881f848179f&isSenior=N&searchValue=${encodeURIComponent(searchValue)}&pageNum=1&pageSize=10&timestamp=' + timestamp;

            fetch(url, {
                headers: {
                    'Accept': 'application/json, text/plain, */*',
                    'Referer': 'https://www.nmpa.gov.cn/datasearch/search-result.html'
                }
            }).then(response => response.json())
            .then(data => {
                console.log('Fetch搜索结果:', data);
                window.lastSearchResult = data;
            }).catch(error => console.error('Fetch搜索失败:', error));
            `,

            // 方式2: 使用XMLHttpRequest（更完整）
            `
            const timestamp = Date.now();
            const url = '/datasearch/data/nmpadata/search?itemId=ff80808183cad75001840881f848179f&isSenior=N&searchValue=${encodeURIComponent(searchValue)}&pageNum=1&pageSize=10&timestamp=' + timestamp;

            const xhr = new XMLHttpRequest();
            xhr.open('GET', url);
            xhr.setRequestHeader('Accept', 'application/json, text/plain, */*');
            xhr.setRequestHeader('Accept-Language', 'zh-CN,zh;q=0.9');
            xhr.setRequestHeader('Connection', 'keep-alive');
            xhr.setRequestHeader('Referer', 'https://www.nmpa.gov.cn/datasearch/search-result.html');
            xhr.setRequestHeader('Sec-Fetch-Dest', 'empty');
            xhr.setRequestHeader('Sec-Fetch-Mode', 'cors');
            xhr.setRequestHeader('Sec-Fetch-Site', 'same-origin');

            xhr.onload = function() {
                if (xhr.status === 200) {
                    try {
                        const data = JSON.parse(xhr.responseText);
                        console.log('XHR搜索结果:', data);
                        window.lastSearchResult = data;
                    } catch (e) {
                        console.error('JSON解析失败:', e);
                    }
                }
            };

            xhr.onerror = function() {
                console.error('XHR请求失败');
            };

            xhr.send();
            `,

            // 方式3: 访问搜索结果页面
            `
            window.location.href = '/datasearch/search-result.html?searchValue=' + encodeURIComponent('${searchValue}');
            `,

            // 方式4: 使用动态签名生成
            `
            // 动态生成签名并请求
            const timestamp = Date.now();
            const params = {
                itemId: 'ff80808183cad75001840881f848179f',
                isSenior: 'N',
                searchValue: '${searchValue}',
                pageNum: '1',
                pageSize: '10',
                timestamp: timestamp.toString()
            };

            // 生成签名（这里使用简化版本）
            const paramStr = Object.entries(params)
                .sort()
                .map(([k, v]) => k + '=' + v)
                .join('&');
            const sign = CryptoJS.MD5(paramStr + timestamp).toString();

            const url = '/datasearch/data/nmpadata/search?' + paramStr + '&sign=' + sign;

            fetch(url, {
                headers: {
                    'Accept': 'application/json, text/plain, */*',
                    'Referer': 'https://www.nmpa.gov.cn/datasearch/search-result.html',
                    'timestamp': timestamp.toString(),
                    'sign': sign
                }
            }).then(response => response.json())
            .then(data => {
                console.log('动态签名搜索结果:', data);
                window.lastSearchResult = data;
            }).catch(error => console.error('动态签名搜索失败:', error));
            `
        ];

        for (let i = 0; i < jsCodes.length; i++) {
            try {
                console.log(`🔧 尝试JavaScript方式 ${i + 1}`);

                // 注入CryptoJS（如果需要）
                if (i === 3) {
                    await this.page.addScriptTag({
                        content: `
                        // 简化的CryptoJS MD5实现
                        window.CryptoJS = window.CryptoJS || {};
                        window.CryptoJS.MD5 = function(string) {
                            function md5cycle(x, k) {
                                var a = 0, b = 0, c = 0, d = 0;
                                a = (a & 0x3FFFFFFF) + (x & 0xFFFFFFFF);
                                b = (b & 0x3FFFFFFF) + (y & 0xFFFFFFFF);
                                c = (c & 0x3FFFFFFF) + (z & 0xFFFFFFFF);
                                d = (d & 0x3FFFFFFF) + (w & 0xFFFFFFFF);
                                a = (a & 0xFFFFFFFF) + (b & 0xFFFFFFFF) + (c & 0xFFFFFFFF) + (d & 0xFFFFFFFF);
                                return a;
                            }
                            return md5cycle(0, 0, 0, 0, string);
                        };
                        `
                    });
                }

                await this.page.evaluate(jsCodes[i]);
                await this.page.waitForTimeout(3000);

                // 检查是否有结果
                const result = await this.page.evaluate(() => {
                    return window.lastSearchResult || null;
                });

                if (result && result.code === 200) {
                    console.log(`✅ JavaScript搜索成功: 方式${i + 1}`);
                    return true;
                }

            } catch (error) {
                console.log(`JavaScript方式 ${i + 1} 失败: ${error.message}`);
                continue;
            }
        }

        return false;
    }

    /**
     * 检查搜索结果
     */
    async checkSearchResults() {
        try {
            // 检查页面上的结果元素
            const resultsSelectors = [
                '.result-item',
                '.search-result',
                '.data-list',
                '.result-list',
                'table',
                '.table'
            ];

            for (const selector of resultsSelectors) {
                const elements = await this.page.$$(selector);
                if (elements.length > 0) {
                    console.log(`找到结果元素: ${selector}, 数量: ${elements.length}`);
                    return true;
                }
            }

            // 检查JavaScript中保存的结果
            const jsResult = await this.page.evaluate(() => {
                return window.lastSearchResult || null;
            });

            if (jsResult && jsResult.code === 200) {
                console.log(`JavaScript中找到搜索结果: ${jsResult.data?.list?.length || 0} 条`);
                return true;
            }

            console.log('❌ 未找到搜索结果');
            return false;

        } catch (error) {
            console.log('检查搜索结果失败:', error.message);
            return false;
        }
    }

    /**
     * 获取搜索结果数据
     */
    async getSearchResults() {
        try {
            // 首先尝试从JavaScript中获取
            const jsResult = await this.page.evaluate(() => {
                return window.lastSearchResult || null;
            });

            if (jsResult && jsResult.code === 200) {
                return {
                    success: true,
                    data: jsResult.data,
                    source: 'javascript'
                };
            }

            // 如果JavaScript中没有，尝试从页面内容提取
            const pageContent = await this.page.content();
            const drugs = this.extractDrugsFromContent(pageContent);

            if (drugs.length > 0) {
                return {
                    success: true,
                    data: {
                        code: 200,
                        data: {
                            list: drugs,
                            total: drugs.length
                        }
                    },
                    source: 'page_content'
                };
            }

            return { success: false, error: '未找到搜索结果' };

        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 从页面内容提取药品信息
     */
    extractDrugsFromContent(content) {
        const drugs = [];

        // 简化的药品提取逻辑
        const drugRegex = /国药准字([A-Z]\d{8})[\s\S]{0,100}?([^\n\r]{2,50}?)/g;
        let match;

        while ((match = drugRegex.exec(content)) !== null) {
            const code = `国药准字${match[1]}`;
            const name = match[2] ? match[2].trim() : '';

            if (name.length > 1 && name.length < 50) {
                drugs.push({
                    f0: code,
                    f1: name,
                    f2: '',
                    f3: '',
                    f4: ''
                });
            }
        }

        return drugs;
    }
}

export default SearchTrigger;