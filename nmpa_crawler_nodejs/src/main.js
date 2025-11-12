// NMPA高级爬虫 - 基于Crawlee + Python破解逻辑
import { PlaywrightCrawler } from 'crawlee';
import { Dataset } from 'crawlee';
import fs from 'fs-extra';
import path from 'path';

import NMPASignatureCracker from './utils/signature-cracker.js';
import SearchTrigger from './utils/search-trigger.js';
import RequestInterceptor from './utils/request-interceptor.js';

console.log('🚀 启动NMPA高级爬虫 - 基于Crawlee + Python破解逻辑');

// 配置常量
const OUTPUT_DIR = 'outputs';
const BASE_URL = 'https://www.nmpa.gov.cn';
const SEARCH_API_URL = 'https://www.nmpa.gov.cn/datasearch/data/nmpadata/search';
const SEARCH_PAGE_URL = 'https://www.nmpa.gov.cn/datasearch/search-result.html';

// 确保输出目录存在
fs.ensureDirSync(OUTPUT_DIR);

// 数据库ID映射（来自Python版本）
const ITEM_IDS = {
    domestic: 'ff80808183cad75001840881f848179f', // 国内药品
    imported: 'ff80808183cad75001840881f84817a0'  // 进口药品
};

// 创建高级NMPA爬虫
const advancedNMPACrawler = new PlaywrightCrawler({
    // 基础配置
    headless: true,
    maxRequestRetries: 3,
    requestHandlerTimeoutSecs: 60,
    navigationTimeoutSecs: 60,

    // 浏览器配置
    launchContext: {
        launchOptions: {
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-background-networking',
                '--disable-default-apps',
                '--disable-extensions',
                '--disable-sync',
                '--disable-translate',
                '--hide-scrollbars',
                '--metrics-recording-only',
                '--mute-audio',
                '--no-first-run',
                '--safebrowsing-disable-auto-update',
                '--ignore-certificate-errors',
                '--ignore-ssl-errors',
                '--ignore-certificate-errors-spki-list',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]
        }
    },

    // 爬虫配置
    maxRequestsPerCrawl: 50,
    maxConcurrency: 2,

    async requestHandler({ request, page, sendRequest, enqueueLinks, log }) {
        const url = request.url;

        // 只处理NMPA相关URL
        if (!url.includes('nmpa.gov.cn')) {
            log.info(`跳过非NMPAURL: ${url}`);
            return;
        }

        // 初始化拦截器和触发器
        if (!page._nmpaInterceptor) {
            page._nmpaInterceptor = new RequestInterceptor();
            page._nmpaSearchTrigger = new SearchTrigger(page);
        }

        const interceptor = page._nmpaInterceptor;
        const searchTrigger = page._nmpaSearchTrigger;

        try {
            // 处理不同的页面类型
            if (url.includes('/datasearch/data/nmpadata/search')) {
                // 处理搜索API请求
                await this.handleSearchAPIRequest(page, url, log);
            } else if (url.includes('/datasearch/search-result.html') || url.includes('/datasearch/home-index.html')) {
                // 处理搜索页面
                await this.handleSearchPage(page, url, log);
            } else if (url.includes('/yaopin/')) {
                // 处理药品页面（公告、监管动态等）
                await this.handleDrugPage(page, url, log);
            } else {
                // 处理其他NMPA页面
                await this.handleGeneralPage(page, url, log);
            }

        } catch (error) {
            log.error(`处理URL失败: ${url}`, error);
        }
    },

    /**
     * 处理搜索API请求
     */
    async handleSearchAPIRequest(page, url, log) {
        log.info(`🔍 处理搜索API请求: ${url}`);

        try {
            // 使用原生fetch请求（绕过412防护）
            const response = await page.evaluate(async (apiUrl) => {
                const response = await fetch(apiUrl, {
                    method: 'GET',
                    headers: {
                        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36',
                        'Accept': 'application/json, text/plain, */*',
                        'Accept-Language': 'zh-CN,zh;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Referer': 'https://www.nmpa.gov.cn/datasearch/search-result.html',
                        'Sec-Fetch-Dest': 'empty',
                        'Sec-Fetch-Mode': 'cors',
                        'Sec-Fetch-Site': 'same-origin'
                    }
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const text = await response.text();
                return { success: true, status: response.status, content: text };
            }, url);

            if (response.success && response.content) {
                const data = JSON.parse(response.content);

                if (data.code === 200 && data.data) {
                    log.info(`✅ 搜索API成功: ${data.data.list?.length || 0} 条记录，总计 ${data.data.total || 0} 条`);

                    // 处理和保存数据
                    await this.saveSearchData(data, page.url(), log);

                    // 保存请求到数据集
                    await this.saveToDataset(data, url);
                } else {
                    log.warning(`搜索API返回异常: ${data}`);
                }
            }

        } catch (error) {
            log.error(`搜索API请求失败: ${error.message}`);
        }
    },

    /**
     * 处理搜索页面（尝试触发搜索以捕获签名）
     */
    async handleSearchPage(page, url, log) {
        log.info(`📄 处理搜索页面: ${url}`);

        try {
            // 等待页面加载
            await page.waitForLoadState('networkidle');

            // 尝试触发搜索
            const searchTerms = ['国药准字H', '国药准字Z', '阿司匹林'];

            for (const searchTerm of searchTerms) {
                log.info(`🔍 尝试搜索: ${searchTerm}`);

                const searchSuccess = await page._nmpaSearchTrigger.triggerRealSearch(searchTerm);

                if (searchSuccess) {
                    // 等待搜索完成
                    await page.waitForTimeout(3000);

                    // 检查是否有结果
                    const hasResults = await page._nmpaSearchTrigger.checkSearchResults();

                    if (hasResults) {
                        const results = await page._nmpaSearchTrigger.getSearchResults();

                        if (results.success) {
                            log.info(`✅ 搜索成功获取数据: ${results.data.data?.list?.length || 0} 条`);
                            await this.saveSearchData(results.data, url, log);
                        }
                    }
                }

                await page.waitForTimeout(2000); // 搜索间隔
            }

        } catch (error) {
            log.error(`搜索页面处理失败: ${error.message}`);
        }
    },

    /**
     * 处理药品页面
     */
    async handleDrugPage(page, url, log) {
        log.info(`💊 处理药品页面: ${url}`);

        try {
            // 等待页面加载
            await page.waitForLoadState('networkidle');

            // 获取页面内容
            const content = await page.content();
            log.info(`页面内容长度: ${content.length} 字符`);

            // 提取药品信息
            const drugs = this.extractDrugData(content, url);

            if (drugs.length > 0) {
                log.info(`✅ 提取到 ${drugs.length} 个药品信息`);
                await this.saveDrugData(drugs, url, log);
            } else {
                log.info('⚠️ 未找到药品信息');
            }

        } catch (error) {
            log.error(`药品页面处理失败: ${error.message}`);
        }
    },

    /**
     * 处理一般页面
     */
    async handleGeneralPage(page, url, log) {
        log.info(`📄 处理一般页面: ${url}`);

        try {
            await page.waitForLoadState('networkidle');
            const content = await page.content();

            // 保存页面内容用于调试
            const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
            const filename = `page_${timestamp}.html`;
            const filepath = path.join(OUTPUT_DIR, filename);

            await fs.writeFile(filepath, content);
            log.info(`📄 页面内容已保存: ${filename}`);

        } catch (error) {
            log.error(`一般页面处理失败: ${error.message}`);
        }
    },

    /**
     * 提取药品数据
     */
    extractDrugData(content, url) {
        const drugs = [];

        // 策略1: 标准国药准字格式
        const standardRegex = /国药准字([A-Z]\d{8})[\s\S]{0,100}?([^\n\r]{2,50}?)(?:[\n\r]|$)/g;
        let match;

        while ((match = standardRegex.exec(content)) !== null) {
            const code = `国药准字${match[1]}`;
            let name = match[2] ? match[2].trim() : '';

            name = name.replace(/[，。、；：""''（）【】\[\]《》\s<>]/g, '').trim();

            if (name.length > 1 && name.length < 50 && !name.includes('批准') && !name.includes('文号')) {
                drugs.push({
                    code: code,
                    name: name,
                    source: url,
                    extractedAt: new Date().toISOString(),
                    strategy: 'standard'
                });
            }
        }

        // 策略2: 药品相关文本提取
        if (drugs.length === 0) {
            const drugKeywords = ['药品', '批准', '上市', '生产', '注册', '备案', '国药准字'];
            const lines = content.split('\n');

            for (const line of lines) {
                const cleanLine = line.trim().replace(/<[^>]*>/g, '');

                if (cleanLine.length > 10 && cleanLine.length < 200) {
                    const keywordCount = drugKeywords.filter(keyword =>
                        cleanLine.includes(keyword)
                    ).length;

                    if (keywordCount >= 2) {
                        drugs.push({
                            code: '相关文本',
                            name: cleanLine.substring(0, 100),
                            source: url,
                            extractedAt: new Date().toISOString(),
                            strategy: 'text',
                            originalText: cleanLine
                        });
                    }
                }
            }
        }

        return drugs;
    },

    /**
     * 保存搜索数据
     */
    async saveSearchData(data, url, log) {
        try {
            const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
            const filename = `search_data_${timestamp}.jsonl`;
            const filepath = path.join(OUTPUT_DIR, filename);

            // 转换数据格式
            const jsonData = data.data.list.map(item => {
                const drug = {
                    code: item.f0 || '',
                    name: item.f1 || '',
                    company: item.f2 || '',
                    approvalNumber: item.f3 || '',
                    source: 'search_api',
                    extractedAt: new Date().toISOString(),
                    searchUrl: url,
                    totalRecords: data.data.total,
                    rawItem: item
                };

                return JSON.stringify(drug);
            }).join('\n');

            await fs.writeFile(filepath, jsonData, 'utf8');
            log.info(`💾 搜索数据已保存: ${filename} (${data.data.list.length} 条记录)`);

        } catch (error) {
            log.error(`保存搜索数据失败: ${error.message}`);
        }
    },

    /**
     * 保存药品数据
     */
    async saveDrugData(drugs, url, log) {
        try {
            const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
            const filename = `drug_data_${timestamp}.jsonl`;
            const filepath = path.join(OUTPUT_DIR, filename);

            const jsonData = drugs.map(drug => JSON.stringify(drug)).join('\n');
            await fs.writeFile(filepath, jsonData, 'utf8');

            log.info(`💾 药品数据已保存: ${filename} (${drugs.length} 条记录)`);

        } catch (error) {
            log.error(`保存药品数据失败: ${error.message}`);
        }
    },

    /**
     * 保存到Crawlee数据集
     */
    async saveToDataset(data, url) {
        try {
            if (data.data && data.data.list) {
                for (const item of data.data.list) {
                    await Dataset.pushData({
                        url: url,
                        data: {
                            code: item.f0 || '',
                            name: item.f1 || '',
                            company: item.f2 || '',
                            approvalNumber: item.f3 || '',
                            extractedAt: new Date().toISOString(),
                            totalRecords: data.data.total
                        }
                    });
                }
            }
        } catch (error) {
            console.error('保存到数据集失败:', error);
        }
    }
});

// 启动爬虫
async function runAdvancedCrawler() {
    console.log('🎯 启动高级NMPA爬虫...');

    // 添加起始URL
    await advancedNMPACrawler.addRequests([
        {
            url: `${BASE_URL}/datasearch/search-result.html`,
            userData: { type: 'search_page' }
        },
        {
            url: `${BASE_URL}/datasearch/home-index.html`,
            userData: { type: 'home_page' }
        },
        {
            url: `${BASE_URL}/yaopin/ypggtg/index.html`,
            userData: { type: 'announcements' }
        },
        {
            url: `${BASE_URL}/yaopin/ypjgdt/index.html`,
            userData: { type: 'regulatory' }
        }
    ]);

    // 运行爬虫
    await advancedNMPACrawler.run({
        // 清理失败请求处理器
        failedRequestHandler({ request, error }, log) {
            log.error(`请求失败: ${request.url}`, error);
        },

        // 清理请求处理完成处理器
        requestHandlerTimeoutSecs: 60,
    });

    console.log('🎉 高级NMPA爬虫运行完成!');
    console.log('📊 查看输出目录:', OUTPUT_DIR);
}

// 启动爬虫
runAdvancedCrawler().catch(error => {
    console.error('🚨 高级NMPA爬虫运行失败:', error);
    process.exit(1);
});