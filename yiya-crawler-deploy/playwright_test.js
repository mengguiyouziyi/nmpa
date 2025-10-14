// 基于Playwright的yiya-crawler测试 - 不依赖外部库
import { chromium } from 'playwright';

console.log('🚀 启动Playwright版yiya-crawler测试');

// 简化配置 - 基于yiya-crawler的配置
const SITE_CONFIG = {
    nmpa: {
        code: "LG0001",
        domain: "www.nmpa.gov.cn",
        name: "国家药品监督管理局",
        pageList: [
            "https://www.nmpa.gov.cn/yaopin/ypjgdt/index.html",
            "https://www.nmpa.gov.cn/yaopin/ypggtg/index.html"
        ]
    }
};

// yiya-crawler风格的简化访问
async function yiyaStyleAccess(page, url) {
    console.log(`🎯 yiya-crawler风格访问: ${url}`);

    try {
        // 设置简单的请求头 - 仿照yiya-crawler的极简风格
        await page.setExtraHTTPHeaders({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        });

        // 简单直接访问 - yiya-crawler的成功模式
        const response = await page.goto(url, {
            waitUntil: 'domcontentloaded',
            timeout: 30000
        });

        const status = response.status();
        console.log(`📊 响应状态: ${status}`);

        if (status === 200) {
            // 等待页面稳定
            await page.waitForTimeout(3000);
            return true;
        } else {
            console.log(`⚠️ 访问失败，状态码: ${status}`);
            return false;
        }

    } catch (error) {
        console.log(`❌ 访问失败: ${error.message}`);
        return false;
    }
}

// 提取列表项 - 仿照yiya-crawler的方式
async function extractListItems(page) {
    try {
        console.log('🔍 提取列表项...');

        const items = await page.evaluate(() => {
            const selectors = ['.list li', 'ul li', '.content-list li', '.article-list li', 'tr'];

            for (const selector of selectors) {
                try {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        console.log(`使用选择器 ${selector} 找到 ${elements.length} 个元素`);

                        return Array.from(elements).map((el) => {
                            const title = el.querySelector('a')?.innerText.trim() ||
                                        el.innerText.trim();
                            const href = el.querySelector('a')?.href || '';
                            const date = el.querySelector('span, .date, .time')?.innerText.trim() || '';
                            return { title, href, date };
                        });
                    }
                } catch (e) {
                    continue;
                }
            }
            return [];
        });

        console.log(`📋 提取到 ${items.length} 个列表项`);
        return items;

    } catch (error) {
        console.error('提取列表项失败:', error);
        return [];
    }
}

// 主测试函数
async function runYiyaTest() {
    console.log('📁 启动基于Playwright的yiya-crawler测试');

    const browser = await chromium.launch({
        headless: true,
        executablePath: '/home/langchao6/.cache/ms-playwright/chromium-1187/chrome-linux/chrome',
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-blink-features=AutomationControlled'
        ]
    });

    const context = await browser.newContext({
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    });

    // 添加简单的反检测
    await context.addInitScript(`
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        console.log('反检测脚本加载完成');
    `);

    try {
        const siteConfig = SITE_CONFIG.nmpa;
        const pageList = siteConfig.pageList;

        console.log(`🎯 站点: ${siteConfig.name} (${siteConfig.code})`);
        console.log(`📋 页面数量: ${pageList.length}`);

        let successCount = 0;
        let totalItems = 0;

        for (const url of pageList) {
            console.log(`\n🔄 处理页面: ${url}`);

            const page = await context.newPage();

            try {
                // 使用yiya-crawler风格的访问
                const success = await yiyaStyleAccess(page, url);

                if (success) {
                    successCount++;
                    console.log(`✅ 成功访问页面: ${url}`);

                    // 尝试等待列表元素 - 仿照yiya-crawler
                    try {
                        await page.waitForSelector('.list li', { timeout: 5000 });
                        console.log('✅ 发现.list li元素');
                    } catch (e) {
                        console.log('⚠️ 未找到.list li元素，继续处理');
                    }

                    // 获取页面信息
                    const pageInfo = await page.evaluate(() => {
                        const bodyText = document.body ? document.body.innerText : '';
                        const title = document.title;
                        const links = document.querySelectorAll('a').length;

                        return {
                            title: title,
                            contentLength: bodyText.length,
                            hasLinks: links,
                            preview: bodyText.substring(0, 200)
                        };
                    });

                    console.log('📄 页面信息:', pageInfo);

                    // 提取列表项
                    const items = await extractListItems(page);
                    totalItems += items.length;

                    if (items.length > 0) {
                        console.log('📋 列表项示例:', items.slice(0, 3));
                    }

                } else {
                    console.log(`❌ 无法访问页面: ${url}`);
                }

            } catch (error) {
                console.error(`处理页面失败: ${url}`, error.message);
            } finally {
                await page.close();
            }
        }

        console.log(`\n🎉 yiya-crawler测试完成!`);
        console.log(`✅ 成功访问: ${successCount}/${pageList.length} 个页面`);
        console.log(`📋 总共提取: ${totalItems} 个列表项`);

    } catch (error) {
        console.error('测试失败:', error);
    } finally {
        await browser.close();
    }
}

// 启动测试
runYiyaTest().catch(console.error);