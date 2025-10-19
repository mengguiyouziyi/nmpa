#!/usr/bin/env node

import { chromium, firefox, webkit } from 'playwright';
import fs from 'fs';
import fsExtra from 'fs-extra';
import path from 'path';
import os from 'os';

// 测试配置
const TEST_CONFIG = {
    outputDir: 'outputs/browser_test',
    timeout: 30000, // 30秒超时
    testSearch: '国药准字H0', // 小范围测试
    maxPages: 2, // 只测试2页
    pageSize: 10 // 小页面测试
};

const PLAYWRIGHT_ARGS = ['--no-sandbox', '--disable-setuid-sandbox', '--headless=new'];

// 浏览器配置
const BROWSERS = [
    {
        name: 'Chromium',
        type: chromium,
        executablePath: '/home/langchao6/.cache/ms-playwright/chromium-1187/chrome-linux/chrome',
        color: '\x1b[36m'
    },
    {
        name: 'Firefox',
        type: firefox,
        executablePath: '/home/langchao6/.cache/ms-playwright/firefox-1490/firefox/firefox',
        color: '\x1b[33m'
    },
    {
        name: 'WebKit',
        type: webkit,
        executablePath: '/home/langchao6/.cache/ms-playwright/webkit-2203/minibrowser-gtk/MiniBrowser',
        color: '\x1b[32m'
    }
];

console.log('🧪 隔离浏览器测试启动');
console.log('========================');
console.log(`📁 输出目录: ${TEST_CONFIG.outputDir}`);
console.log(`⏱️  超时设置: ${TEST_CONFIG.timeout}ms`);
console.log(`🔍 测试搜索: ${TEST_CONFIG.testSearch} (${TEST_CONFIG.maxPages}页)`);
console.log('');

// 确保输出目录存在
await fsExtra.ensureDir(TEST_CONFIG.outputDir);

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function testBrowser(browserConfig) {
    const { name, type, executablePath, color } = browserConfig;
    const result = {
        name,
        success: false,
        error: null,
        startTime: Date.now(),
        endTime: null,
        recordsCollected: 0,
        pagesTested: 0,
        browserStarted: false,
        navigationSuccess: false,
        jsExecutionSuccess: false,
        apiCallSuccess: false
    };

    console.log(`${color}🌐 测试 ${name} 浏览器...${color === '\x1b[36m' ? '\x1b[0m' : ''}`);

    let browser = null;
    let context = null;
    let page = null;

    try {
        // 1. 启动浏览器
        const launchStart = Date.now();

        if (!fs.existsSync(executablePath)) {
            throw new Error(`浏览器可执行文件不存在: ${executablePath}`);
        }

        browser = await type.launch({
            headless: true,
            args: PLAYWRIGHT_ARGS,
            executablePath
        });

        result.browserStarted = true;
        const launchTime = Date.now() - launchStart;
        console.log(`${color}   ✅ 浏览器启动成功 (${launchTime}ms)${color === '\x1b[36m' ? '\x1b[0m' : ''}`);

        // 2. 创建页面
        context = await browser.newContext();
        page = await context.newPage();

        // 3. 导航到搜索页面
        const navStart = Date.now();
        await page.goto('https://www.nmpa.gov.cn/datasearch/search-result.html', {
            waitUntil: 'domcontentloaded',
            timeout: 15000
        });

        result.navigationSuccess = true;
        const navTime = Date.now() - navStart;
        console.log(`${color}   ✅ 页面导航成功 (${navTime}ms)${color === '\x1b[36m' ? '\x1b[0m' : ''}`);

        // 4. 等待JavaScript环境
        await page.waitForFunction(() => {
            return window.api && window.pajax && window.itemFileUrl;
        }, { timeout: 10000 });

        result.jsExecutionSuccess = true;
        console.log(`${color}   ✅ JavaScript环境就绪${color === '\x1b[36m' ? '\x1b[0m' : ''}`);

        // 5. 注入必要脚本
        await page.addInitScript(() => {
            window.getUrl = window.getUrl || (() => '');
        });

        // 6. 测试API调用
        const apiStart = Date.now();
        const response = await page.evaluate(async (params) => {
            try {
                const raw = await window.pajax.hasTokenGet(window.api.queryList, {
                    itemId: params.itemId,
                    isSenior: 'N',
                    searchValue: params.searchValue,
                    pageNum: params.pageNum,
                    pageSize: params.pageSize,
                });
                return {
                    success: true,
                    data: raw?.data?.data,
                    message: raw?.message
                };
            } catch (error) {
                return {
                    success: false,
                    error: error.message,
                    message: error.message
                };
            }
        }, {
            itemId: 'ff80808183cad75001840881f848179f',
            searchValue: TEST_CONFIG.testSearch,
            pageNum: 1,
            pageSize: TEST_CONFIG.pageSize
        });

        const apiTime = Date.now() - apiStart;

        if (response.success && response.data && response.data.list) {
            result.apiCallSuccess = true;
            result.recordsCollected = response.data.list.length;
            result.pagesTested = 1;
            console.log(`${color}   ✅ API调用成功 (${apiTime}ms) - 获取${result.recordsCollected}条记录${color === '\x1b[36m' ? '\x1b[0m' : ''}`);

            // 7. 测试详情获取（获取第一条记录）
            if (response.data.list.length > 0) {
                const firstRecord = response.data.list[0];
                if (firstRecord.f4) {
                    const detailStart = Date.now();
                    const detailResponse = await page.evaluate(async (params) => {
                        try {
                            const raw = await window.pajax.hasTokenGet(window.api.queryDetail, {
                                id: params.id,
                                itemId: params.itemId,
                                isSenior: 'N',
                            });
                            return {
                                success: true,
                                data: raw?.data?.data?.detail ?? raw?.data?.detail ?? raw?.detail
                            };
                        } catch (error) {
                            return {
                                success: false,
                                error: error.message
                            };
                        }
                    }, {
                        id: firstRecord.f4,
                        itemId: 'ff80808183cad75001840881f848179f'
                    });

                    const detailTime = Date.now() - detailStart;
                    if (detailResponse.success) {
                        console.log(`${color}   ✅ 详情获取成功 (${detailTime}ms)${color === '\x1b[36m' ? '\x1b[0m' : ''}`);
                    } else {
                        console.log(`${color}   ⚠️  详情获取失败: ${detailResponse.error}${color === '\x1b[36m' ? '\x1b[0m' : ''}`);
                    }
                }
            }

            // 8. 测试第二页（如果有多页）
            if (response.data.total > TEST_CONFIG.pageSize) {
                const page2Start = Date.now();
                await sleep(2000); // 等待2秒

                const page2Response = await page.evaluate(async (params) => {
                    try {
                        const raw = await window.pajax.hasTokenGet(window.api.queryList, {
                            itemId: params.itemId,
                            isSenior: 'N',
                            searchValue: params.searchValue,
                            pageNum: params.pageNum,
                            pageSize: params.pageSize,
                        });
                        return {
                            success: true,
                            data: raw?.data?.data,
                            count: raw?.data?.data?.list?.length || 0
                        };
                    } catch (error) {
                        return {
                            success: false,
                            error: error.message
                        };
                    }
                }, {
                    itemId: 'ff80808183cad75001840881f848179f',
                    searchValue: TEST_CONFIG.testSearch,
                    pageNum: 2,
                    pageSize: TEST_CONFIG.pageSize
                });

                const page2Time = Date.now() - page2Start;
                if (page2Response.success) {
                    result.pagesTested = 2;
                    result.recordsCollected += page2Response.count;
                    console.log(`${color}   ✅ 第二页测试成功 (${page2Time}ms) - 获取${page2Response.count}条记录${color === '\x1b[36m' ? '\x1b[0m' : ''}`);
                } else {
                    console.log(`${color}   ⚠️  第二页测试失败: ${page2Response.error}${color === '\x1b[36m' ? '\x1b[0m' : ''}`);
                }
            }

            result.success = true;
        } else {
            result.error = `API调用失败: ${response?.message || response?.error || '未知错误'}`;
            console.log(`${color}   ❌ API调用失败: ${result.error}${color === '\x1b[36m' ? '\x1b[0m' : ''}`);
        }

    } catch (error) {
        result.error = error.message;
        console.log(`${color}   ❌ 测试失败: ${error.message}${color === '\x1b[36m' ? '\x1b[0m' : ''}`);
    } finally {
        result.endTime = Date.now();

        // 清理资源
        try {
            if (page) await page.close();
            if (context) await context.close();
            if (browser) await browser.close();
        } catch (cleanupError) {
            console.log(`${color}   ⚠️  清理资源时出错: ${cleanupError.message}${color === '\x1b[36m' ? '\x1b[0m' : ''}`);
        }
    }

    return result;
}

async function runTests() {
    const results = [];
    const startTime = Date.now();

    for (const browserConfig of BROWSERS) {
        const result = await testBrowser(browserConfig);
        results.push(result);

        // 测试间隔
        if (results.length < BROWSERS.length) {
            console.log('');
            await sleep(3000);
        }
    }

    const totalTime = Date.now() - startTime;

    // 生成测试报告
    console.log('\n📋 测试报告');
    console.log('=====================================');
    console.log(`⏱️  总测试时间: ${Math.round(totalTime/1000)}秒`);
    console.log(`📊 成功测试: ${results.filter(r => r.success).length}/${results.length}`);
    console.log('');

    // 详细结果表格
    console.log('┌─────────────────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐');
    console.log('│ 浏览器               │ 启动时间 │ 导航时间 │ API调用   │ 获取记录 │ 测试页数 │ 结果   │');
    console.log('├─────────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤');

    for (const result of results) {
        const status = result.success ? '✅ 成功' : '❌ 失败';
        const launchTime = result.browserStarted ? `${Date.now() - result.startTime}ms` : '失败';
        const navTime = result.navigationSuccess ? '成功' : '失败';
        const apiStatus = result.apiCallSuccess ? '成功' : '失败';
        const records = result.recordsCollected || 0;
        const pages = result.pagesTested || 0;

        const name = result.name.padEnd(19);
        console.log(`│ ${name} │ ${launchTime.padStart(8)} │ ${navTime.padStart(8)} │ ${apiStatus.padStart(8)} │ ${records.toString().padStart(8)} │ ${pages.toString().padStart(8)} │ ${status.padStart(6)} │`);
    }

    console.log('└─────────────────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘');

    // 保存详细报告
    const reportPath = path.join(TEST_CONFIG.outputDir, `test_report_${Date.now()}.json`);
    const report = {
        timestamp: new Date().toISOString(),
        config: TEST_CONFIG,
        totalTime,
        results,
        summary: {
            total: results.length,
            successful: results.filter(r => r.success).length,
            failed: results.filter(r => !r.success).length,
            totalRecords: results.reduce((sum, r) => sum + r.recordsCollected, 0),
            totalPages: results.reduce((sum, r) => sum + r.pagesTested, 0)
        }
    };

    await fsExtra.writeJSON(reportPath, report, { spaces: 2 });
    console.log(`\n💾 详细报告已保存到: ${reportPath}`);

    // 推荐配置
    const successfulBrowsers = results.filter(r => r.success);
    if (successfulBrowsers.length > 0) {
        console.log('\n💡 推荐配置:');
        const browserNames = successfulBrowsers.map(r => r.name.toLowerCase().replace(' ', '')).join(',');
        console.log(`   NMPA_BROWSER_SEQUENCE=${browserNames}`);

        if (successfulBrowsers.length === 1) {
            console.log('   建议使用单浏览器模式以确保稳定性');
        } else {
            console.log(`   NMPA_BROWSER_PAGE_BATCH=50`);
            console.log(`   NMPA_BROWSER_SWAP_DELAY_MS=300000`);
        }
    } else {
        console.log('\n⚠️  没有浏览器通过测试，建议检查网络连接或配置');
    }

    return results;
}

// 运行测试
runTests().catch(console.error);