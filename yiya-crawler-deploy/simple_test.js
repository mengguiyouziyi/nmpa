// 简化版yiya-crawler测试 - 绕过依赖问题
import { PuppeteerCrawler } from 'crawlee';

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

console.log('🚀 启动简化版yiya-crawler测试');

// 创建简化的Crawlee爬虫 - 仿照yiya-crawler的配置
const testCrawler = new PuppeteerCrawler({
    // yiya-crawler的基础配置
    navigationTimeoutSecs: 60,
    requestHandlerTimeoutSecs: 60,
    maxRequestRetries: 3,

    // 极简浏览器配置 - 仿照yiya-crawler
    launchContext: {
        launchOptions: {
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        }
    },

    // 爬虫配置
    maxRequestsPerCrawl: 5,
    maxConcurrency: 1,

    // 简化的请求处理器 - 仿照yiya-crawler的逻辑
    async requestHandler({ request, page }) {
        const url = request.url;
        const siteConfig = SITE_CONFIG.nmpa;

        if (!url.includes(siteConfig.domain)) {
            console.log(`不是NMPA站点请求: ${url}`);
            return;
        }

        console.log(`-----------(yiya-test) 处理页面: ${url}`);

        try {
            // 等待页面加载 - 仿照yiya-crawler
            await page.waitForTimeout(3000);

            // 尝试等待列表元素
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

            // 检查是否是列表页面并提取链接
            if (url.includes('index.html')) {
                const items = await page.evaluate(() => {
                    const results = [];
                    const elements = document.querySelectorAll('.list li, ul li');

                    Array.from(elements).forEach((el) => {
                        const title = el.querySelector('a')?.innerText.trim() || el.innerText.trim();
                        const href = el.querySelector('a')?.href || '';
                        if (title && href) {
                            results.push({ title, href });
                        }
                    });

                    return results.slice(0, 5); // 只取前5个
                });

                console.log(`📋 发现 ${items.length} 个列表项:`, items);
            }

        } catch (error) {
            console.error(`处理页面失败: ${url}`, error.message);
        }
    },

    // 失败处理
    failedRequestHandler({ request, error }) {
        console.log(`请求失败: ${request.url} - ${error.message}`);
    }
});

// 主函数
async function runSimpleTest() {
    try {
        console.log(`🎯 站点: ${SITE_CONFIG.nmpa.name} (${SITE_CONFIG.nmpa.code})`);
        console.log(`📋 页面数量: ${SITE_CONFIG.nmpa.pageList.length}`);

        // 运行测试
        await testCrawler.run(SITE_CONFIG.nmpa.pageList);

        console.log('🎉 yiya-crawler简化测试完成!');

    } catch (error) {
        console.error('测试失败:', error);
    }
}

// 启动测试
runSimpleTest().catch(console.error);