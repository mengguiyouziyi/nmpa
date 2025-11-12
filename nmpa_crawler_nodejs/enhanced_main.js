import { chromium } from 'playwright';
import fs from 'fs-extra';
import path from 'path';

// 配置常量
const SITE_CONFIG = {
    nmpa: {
        code: "LG0001",
        domain: "www.nmpa.gov.cn",
        name: "国家药品监督管理局",
        pageList: [
            "https://www.nmpa.gov.cn/yaopin/ypggtg/index.html"
        ]
    }
};

// 输出目录
const OUTPUT_DIR = 'outputs';
const TEMP_DIR = 'downloads';

// 确保目录存在
fs.ensureDirSync(OUTPUT_DIR);
fs.ensureDirSync(TEMP_DIR);

// 用户代理池
const USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
];

// 随机选择用户代理
function getRandomUserAgent() {
    return USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];
}

// 随机延迟
function randomDelay(min = 1000, max = 5000) {
    return Math.random() * (max - min) + min;
}

// 增强的412绕过函数
async function enhancedBypass412(page, url) {
    console.log(`🔓 增强版绕过412保护: ${url}`);

    // 随机用户代理
    const userAgent = getRandomUserAgent();
    console.log(`🎭 使用User-Agent: ${userAgent}`);

    // 设置上下文
    const context = page.context();
    await context.setExtraHTTPHeaders({
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'Connection': 'keep-alive'
    });

    // 策略1: 基础访问 + 随机延迟
    try {
        console.log('🔄 策略1: 基础访问');
        await page.waitForTimeout(randomDelay(2000, 4000));

        const response = await page.goto(url, {
            waitUntil: 'domcontentloaded',
            timeout: 45000
        });

        const status = response.status();
        console.log(`📊 响应状态: ${status}`);

        if (status === 200) {
            const content = await page.content();
            if (content.length > 1000) {
                console.log('✅ 策略1成功');
                return true;
            }
        }
    } catch (error) {
        console.log(`⚠️ 策略1失败: ${error.message}`);
    }

    // 策略2: 模拟人类浏览行为
    try {
        console.log('🔄 策略2: 模拟人类浏览');

        // 先访问首页
        await page.goto('https://www.nmpa.gov.cn/', {
            waitUntil: 'domcontentloaded',
            timeout: 30000
        });

        await page.waitForTimeout(randomDelay(3000, 6000));

        // 模拟鼠标移动
        await page.mouse.move(100, 100);
        await page.waitForTimeout(500);
        await page.mouse.move(200, 200);
        await page.waitForTimeout(500);

        // 再访问目标页面
        const response = await page.goto(url, {
            waitUntil: 'domcontentloaded',
            timeout: 45000
        });

        const status = response.status();
        console.log(`📊 响应状态: ${status}`);

        if (status === 200) {
            const content = await page.content();
            if (content.length > 1000) {
                console.log('✅ 策略2成功');
                return true;
            }
        }
    } catch (error) {
        console.log(`⚠️ 策略2失败: ${error.message}`);
    }

    // 策略3: 使用JavaScript重定向
    try {
        console.log('🔄 策略3: JavaScript重定向');
        await page.goto('about:blank');

        await page.evaluate(`
            window.location.href = '${url}';
        `);

        await page.waitForTimeout(randomDelay(5000, 8000));
        await page.waitForLoadState('domcontentloaded', { timeout: 30000 });

        const content = await page.content();
        if (content.length > 1000) {
            console.log('✅ 策略3成功');
            return true;
        }
    } catch (error) {
        console.log(`⚠️ 策略3失败: ${error.message}`);
    }

    // 策略4: 添加随机参数
    try {
        console.log('🔄 策略4: 添加随机参数');
        const timestamp = Date.now();
        const randomParam = Math.random().toString(36).substring(7);
        const modifiedUrl = `${url}?t=${timestamp}&r=${randomParam}`;

        const response = await page.goto(modifiedUrl, {
            waitUntil: 'domcontentloaded',
            timeout: 30000
        });

        const status = response.status();
        console.log(`📊 响应状态: ${status}`);

        if (status === 200) {
            const content = await page.content();
            if (content.length > 1000) {
                console.log('✅ 策略4成功');
                return true;
            }
        }
    } catch (error) {
        console.log(`⚠️ 策略4失败: ${error.message}`);
    }

    console.log('❌ 所有策略都失败了');
    return false;
}

// 提取药品数据
async function extractDrugData(page) {
    try {
        // 等待页面加载
        await page.waitForSelector('body', { timeout: 10000 });

        // 获取页面信息
        const pageInfo = await page.evaluate(() => {
            const bodyText = document.body.innerText;
            const title = document.title;

            return {
                title: title,
                contentLength: bodyText.length,
                hasTables: document.querySelectorAll('table').length,
                hasLinks: document.querySelectorAll('a').length,
                preview: bodyText.substring(0, 300)
            };
        });

        console.log('📄 页面信息:', pageInfo);

        const drugs = await page.evaluate(() => {
            const results = [];
            const bodyText = document.body.innerText;

            console.log('页面文本长度:', bodyText.length);

            // 多种提取策略
            const strategies = [
                // 标准国药准字格式
                /国药准字([A-Z]\d{8})[\s\S]{0,50}?([^\n\r]{2,50}?)(?:[\n\r]|$)/g,
                // 宽松格式
                /国药准字([A-Z]\d{8})[：:\s]*([^\n\r]{2,50}?)/g,
                // 包含各种字符的格式
                /国药准字([A-Z]\d{8})[^\n\r]*?([^\n\r]{2,50}?)/g
            ];

            for (let i = 0; i < strategies.length; i++) {
                const regex = strategies[i];
                console.log(`使用策略 ${i + 1}:`, regex);

                let match;
                regex.lastIndex = 0;

                while ((match = regex.exec(bodyText)) !== null) {
                    const code = `国药准字${match[1]}`;
                    let name = match[2] ? match[2].trim() : '';

                    // 清理药品名称
                    name = name.replace(/[，。、；：""''（）【】\[\]《》]/g, '').trim();

                    if (name.length > 1 && name.length < 50) {
                        results.push({
                            code: code,
                            zh: name,
                            en: '', // 英文名暂时为空
                            source: `strategy_${i + 1}`,
                            rawMatch: match[0]
                        });
                        console.log(`找到药品: ${code} - ${name}`);
                    }
                }
            }

            // 去重
            const uniqueResults = [];
            const seen = new Set();

            results.forEach(item => {
                const key = item.code;
                if (!seen.has(key)) {
                    seen.add(key);
                    uniqueResults.push(item);
                }
            });

            return uniqueResults;
        });

        console.log(`📦 提取到 ${drugs.length} 个药品信息`);
        if (drugs.length > 0) {
            console.log('药品示例:', drugs.slice(0, 3));
        }

        return drugs;

    } catch (error) {
        console.error('提取药品数据失败:', error);
        return [];
    }
}

// 发现可能包含药品信息的链接
async function discoverDrugLinks(page) {
    try {
        const links = await page.evaluate(() => {
            const results = [];
            const links = document.querySelectorAll('a[href]');
            const currentDomain = window.location.hostname;

            // 药品相关关键词
            const drugKeywords = [
                '药品', '批准', '查询', '目录', '数据库', '准字', '说明书',
                'drug', 'approval', 'database', 'catalog', 'license'
            ];

            // NMPA特定路径模式
            const nmpaPatterns = [
                /\/yaopin\//,
                /\/yp[a-z]+\//,
                /\/WS\d+\//,
                /\/CL\d+\//,
                /\/药品\//,
                /\/query\//,
                /\/search\//,
                /\/list\//,
                /\/data\//
            ];

            links.forEach(link => {
                const href = link.getAttribute('href');
                const text = link.innerText.trim();

                if (href && (href.startsWith('http') || href.startsWith('/'))) {
                    const fullUrl = href.startsWith('http') ? href : new URL(href, window.location.origin).href;

                    // 检查是否是相关链接
                    const isDrugRelated = drugKeywords.some(keyword =>
                        text.toLowerCase().includes(keyword.toLowerCase()) ||
                        href.toLowerCase().includes(keyword.toLowerCase())
                    );

                    const isNMPAInternal = nmpaPatterns.some(pattern => pattern.test(href));

                    // 检查域名
                    const isSameDomain = fullUrl.includes(currentDomain) || fullUrl.includes('nmpa.gov.cn');

                    if ((isDrugRelated || isNMPAInternal) && isSameDomain) {
                        results.push(fullUrl);
                    }
                }
            });

            // 去重并返回前10个最相关的链接
            const uniqueLinks = [...new Set(results)];
            return uniqueLinks.slice(0, 10);
        });

        console.log(`🔗 发现 ${links.length} 个可能相关的链接`);
        return links;

    } catch (error) {
        console.error('发现链接失败:', error);
        return [];
    }
}

// 保存数据到文件
async function saveDrugData(drugs, pageUrl) {
    if (drugs.length === 0) return;

    try {
        const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
        const filename = `drugs_${timestamp}.jsonl`;
        const filepath = path.join(OUTPUT_DIR, filename);

        const jsonlData = drugs.map(drug => JSON.stringify(drug)).join('\n');
        await fs.writeFile(filepath, jsonlData, 'utf8');

        console.log(`💾 保存 ${drugs.length} 个药品到: ${filename}`);

        // 追加到主文件
        const mainFile = path.join(OUTPUT_DIR, 'drugs_all.jsonl');
        await fs.appendFile(mainFile, jsonlData + '\n', 'utf8');

    } catch (error) {
        console.error('保存数据失败:', error);
    }
}

// 主爬虫函数
async function runEnhancedNMPACrawler() {
    console.log('🚀 启动增强版NMPA药品数据爬虫');
    console.log('📁 输出目录:', OUTPUT_DIR);

    const browser = await chromium.launch({
        headless: true,
        executablePath: '/home/langchao6/.cache/ms-playwright/chromium-1187/chrome-linux/chrome',
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
            '--ignore-certificate-errors-spki-list'
        ]
    });

    const context = await browser.newContext({
        userAgent: getRandomUserAgent(),
        viewport: { width: 1920, height: 1080 },
        locale: 'zh-CN',
        timezoneId: 'Asia/Shanghai'
    });

    // 添加反检测脚本
    await context.addInitScript(`
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en']
        });
        Object.defineProperty(navigator, 'platform', {
            get: () => 'Win32'
        });
        window.chrome = { runtime: {} };
        console.log('反检测脚本加载完成');
    `);

    try {
        const siteConfig = SITE_CONFIG.nmpa;
        const pageList = siteConfig.pageList;

        console.log(`🎯 站点: ${siteConfig.name} (${siteConfig.code})`);
        console.log(`📋 页面数量: ${pageList.length}`);

        let totalDrugs = 0;

        for (const url of pageList) {
            console.log(`\n🔄 处理页面: ${url}`);

            const page = await context.newPage();

            try {
                // 使用增强的绕过策略
                const success = await enhancedBypass412(page, url);

                if (success) {
                    // 提取药品数据
                    const drugs = await extractDrugData(page);
                    totalDrugs += drugs.length;

                    // 保存数据
                    await saveDrugData(drugs, url);

                    // 如果当前页面没有药品数据，查找相关链接并跟进
                    if (drugs.length === 0) {
                        console.log('🔍 当前页面无药品数据，查找相关链接...');
                        const relatedLinks = await discoverDrugLinks(page);

                        if (relatedLinks.length > 0) {
                            console.log(`🔗 发现 ${relatedLinks.length} 个相关链接，开始跟进...`);

                            // 跟进前3个最有希望的链接
                            for (let i = 0; i < Math.min(relatedLinks.length, 3); i++) {
                                const linkUrl = relatedLinks[i];
                                console.log(`🔍 跟进链接 ${i + 1}/${Math.min(relatedLinks.length, 3)}: ${linkUrl}`);

                                try {
                                    const linkPage = await context.newPage();
                                    const linkSuccess = await enhancedBypass412(linkPage, linkUrl);

                                    if (linkSuccess) {
                                        const linkDrugs = await extractDrugData(linkPage);
                                        totalDrugs += linkDrugs.length;

                                        if (linkDrugs.length > 0) {
                                            console.log(`✅ 链接成功提取到 ${linkDrugs.length} 个药品信息`);
                                            await saveDrugData(linkDrugs, linkUrl);
                                        } else {
                                            console.log('⚠️ 链接页面也未发现药品数据');
                                        }
                                    } else {
                                        console.log(`❌ 链接访问失败: ${linkUrl}`);
                                    }

                                    await linkPage.close();
                                    await page.waitForTimeout(randomDelay(2000, 4000));

                                } catch (linkError) {
                                    console.error(`处理链接失败: ${linkUrl}`, linkError.message);
                                }
                            }
                        } else {
                            console.log('⚠️ 未发现相关链接');
                        }
                    }

                    // 添加延迟
                    await page.waitForTimeout(randomDelay(3000, 7000));
                } else {
                    console.log(`❌ 无法访问页面: ${url}`);
                }

            } catch (error) {
                console.error(`处理页面失败: ${url}`, error.message);
            } finally {
                await page.close();
            }
        }

        console.log(`\n🎉 爬虫运行完成! 总共提取 ${totalDrugs} 个药品信息`);

        // 显示结果统计
        try {
            const files = await fs.readdir(OUTPUT_DIR);
            const jsonlFiles = files.filter(f => f.endsWith('.jsonl'));

            console.log('\n📊 结果统计:');
            for (const file of jsonlFiles) {
                const filepath = path.join(OUTPUT_DIR, file);
                const stats = await fs.stat(filepath);
                const content = await fs.readFile(filepath, 'utf8');
                const lineCount = content.split('\n').filter(line => line.trim()).length;

                console.log(`  📄 ${file}: ${lineCount} 条记录 (${stats.size} bytes)`);
            }

        } catch (error) {
            console.log('读取结果统计失败:', error.message);
        }

    } catch (error) {
        console.error('爬虫运行失败:', error);
    } finally {
        await browser.close();
    }
}

// 启动应用
runEnhancedNMPACrawler().catch(console.error);