#!/usr/bin/env node

import { chromium, firefox, webkit } from 'playwright';
import fs from 'fs';
import path from 'path';

const SEARCH_URL = 'https://www.nmpa.gov.cn/datasearch/search-result.html';
const PLAYWRIGHT_ARGS = ['--no-sandbox', '--disable-setuid-sandbox', '--headless=new'];

const TEST_CONFIG = {
    chromium: {
        name: 'Chromium',
        color: '\x1b[36m', // 青色
    },
    firefox: {
        name: 'Firefox',
        color: '\x1b[33m', // 黄色
    },
    webkit: {
        name: 'WebKit (Safari)',
        color: '\x1b[32m', // 绿色
    }
};

console.log('🔍 Playwright浏览器兼容性测试');
console.log('=====================================\n');

async function testBrowser(browserType, config) {
    const { name, color } = config;
    console.log(`${color}🌐 测试 ${name} 浏览器...\x1b[0m`);

    const results = {
        name,
        success: false,
        launchTime: null,
        navigationTime: null,
        jsExecutionTime: null,
        error: null,
        pageSize: null,
        memoryUsage: null
    };

    try {
        // 1. 测试浏览器启动
        const launchStart = Date.now();

        // 使用现有浏览器版本路径
        let launchOptions = {
            headless: true,
            args: PLAYWRIGHT_ARGS
        };

        // 为不同浏览器设置特定的可执行文件路径
        if (config.name === 'Chromium') {
            const chromiumPath = '/home/langchao6/.cache/ms-playwright/chromium-1187/chrome-linux/chrome';
            if (fs.existsSync(chromiumPath)) {
                launchOptions.executablePath = chromiumPath;
            }
        } else if (config.name === 'Firefox') {
            const firefoxPath = '/home/langchao6/.cache/ms-playwright/firefox-1490/firefox/firefox';
            if (fs.existsSync(firefoxPath)) {
                launchOptions.executablePath = firefoxPath;
            }
        } else if (config.name === 'WebKit (Safari)') {
            const webkitPath = '/home/langchao6/.cache/ms-playwright/webkit-2203/minibrowser-gtk/MiniBrowser';
            if (fs.existsSync(webkitPath)) {
                launchOptions.executablePath = webkitPath;
            }
        }

        const browser = await browserType.launch(launchOptions);
        results.launchTime = Date.now() - launchStart;
        console.log(`${color}   ✅ 启动成功 (${results.launchTime}ms)\x1b[0m`);

        try {
            // 2. 测试页面导航
            const context = await browser.newContext();
            const page = await context.newPage();

            const navStart = Date.now();
            const response = await page.goto(SEARCH_URL, {
                waitUntil: 'domcontentloaded',
                timeout: 60000
            });
            results.navigationTime = Date.now() - navStart;

            if (response && response.ok()) {
                console.log(`${color}   ✅ 导航成功 (${results.navigationTime}ms)\x1b[0m`);
            } else {
                throw new Error(`导航失败: ${response?.status()}`);
            }

            try {
                // 3. 测试JavaScript执行
                const jsStart = Date.now();
                await page.waitForFunction(() => {
                    return window.api && window.pajax && window.itemFileUrl;
                }, { timeout: 60000 });
                results.jsExecutionTime = Date.now() - jsStart;
                console.log(`${color}   ✅ JavaScript执行成功 (${results.jsExecutionTime}ms)\x1b[0m`);

                // 4. 测试API调用
                await page.addInitScript(() => {
                    window.getUrl = window.getUrl || (() => '');
                });

                const apiTest = await page.evaluate(async () => {
                    try {
                        const raw = await window.pajax.hasTokenGet(window.api.queryList, {
                            itemId: 'ff80808183cad75001840881f848179f',
                            isSenior: 'N',
                            searchValue: '国药准字H',
                            pageNum: 1,
                            pageSize: 20,
                        });
                        return {
                            success: !!raw?.data?.data?.list?.length,
                            count: raw?.data?.data?.list?.length || 0,
                            total: raw?.data?.data?.total || 0
                        };
                    } catch (error) {
                        return { success: false, error: error.message };
                    }
                });

                if (apiTest.success) {
                    console.log(`${color}   ✅ API调用成功 (获取${apiTest.count}条数据，总计${apiTest.total}条)\x1b[0m`);
                    results.pageSize = { count: apiTest.count, total: apiTest.total };
                } else {
                    console.log(`${color}   ⚠️  API调用失败: ${apiTest.error}\x1b[0m`);
                }

                // 5. 获取内存使用情况
                const memUsage = process.memoryUsage();
                results.memoryUsage = {
                    rss: Math.round(memUsage.rss / 1024 / 1024 * 100) / 100,
                    heapUsed: Math.round(memUsage.heapUsed / 1024 / 1024 * 100) / 100,
                    heapTotal: Math.round(memUsage.heapTotal / 1024 / 1024 * 100) / 100
                };

                results.success = true;
                console.log(`${color}   ✅ 所有测试通过!\x1b[0m`);

            } catch (jsError) {
                results.error = `JavaScript执行失败: ${jsError.message}`;
                console.log(`${color}   ❌ JavaScript执行失败: ${jsError.message}\x1b[0m`);
            }

            await context.close();

        } catch (navError) {
            results.error = `导航失败: ${navError.message}`;
            console.log(`${color}   ❌ 导航失败: ${navError.message}\x1b[0m`);
        }

        await browser.close();

    } catch (launchError) {
        results.error = `启动失败: ${launchError.message}`;
        console.log(`${color}   ❌ 启动失败: ${launchError.message}\x1b[0m`);
    }

    return results;
}

async function runCompatibilityTest() {
    const browsers = [
        { type: chromium, config: TEST_CONFIG.chromium },
        { type: firefox, config: TEST_CONFIG.firefox },
        { type: webkit, config: TEST_CONFIG.webkit }
    ];

    const results = {};

    console.log('📊 开始浏览器兼容性测试...\n');

    for (const { type, config } of browsers) {
        results[config.name.toLowerCase()] = await testBrowser(type, config);
        console.log(''); // 空行分隔
    }

    // 生成测试报告
    console.log('📋 测试报告');
    console.log('=====================================');

    const successful = Object.values(results).filter(r => r.success).length;
    const total = Object.keys(results).length;

    console.log(`\n📈 总体结果: ${successful}/${total} 浏览器测试通过\n`);

    // 详细结果表格
    console.log('┌─────────────────────┬──────────┬──────────┬──────────┬──────────┬──────────┐');
    console.log('│ 浏览器               │ 启动时间 │ 导航时间 │ JS执行   │ API调用   │ 内存使用 │');
    console.log('├─────────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤');

    for (const [key, result] of Object.entries(results)) {
        const launchTime = result.launchTime ? `${result.launchTime}ms` : '失败';
        const navTime = result.navigationTime ? `${result.navigationTime}ms` : '失败';
        const jsTime = result.jsExecutionTime ? `${result.jsExecutionTime}ms` : '失败';
        const apiStatus = result.pageSize ? '成功' : '失败';
        const memory = result.memoryUsage ? `${result.memoryUsage.heapUsed}MB` : '未知';

        const name = result.name.padEnd(19);
        console.log(`│ ${name} │ ${launchTime.padStart(8)} │ ${navTime.padStart(8)} │ ${jsTime.padStart(8)} │ ${apiStatus.padStart(8)} │ ${memory.padStart(8)} │`);
    }

    console.log('└─────────────────────┴──────────┴──────────┴──────────┴──────────┴──────────┘');

    // 保存详细报告
    const reportPath = path.join('browser_compatibility_report.json');
    fs.writeFileSync(reportPath, JSON.stringify({
        timestamp: new Date().toISOString(),
        summary: {
            total,
            successful,
            failed: total - successful
        },
        results
    }, null, 2));

    console.log(`\n💾 详细报告已保存到: ${reportPath}`);

    // 推荐配置
    console.log('\n💡 推荐配置:');
    const workingBrowsers = Object.entries(results)
        .filter(([_, result]) => result.success)
        .map(([key, result]) => key);

    if (workingBrowsers.length > 0) {
        console.log(`   NMPA_BROWSER_SEQUENCE=${workingBrowsers.join(',')}`);
        console.log(`   建议轮换间隔: NMPA_BROWSER_SWAP_DELAY_MS=300000`);
        console.log(`   建议批次大小: NMPA_BROWSER_PAGE_BATCH=50`);
    } else {
        console.log('   ⚠️  没有浏览器通过测试，建议检查网络连接或Playwright安装');
    }

    return results;
}

// 运行测试
runCompatibilityTest().catch(console.error);