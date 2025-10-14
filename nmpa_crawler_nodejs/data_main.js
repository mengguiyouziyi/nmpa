import { chromium } from 'playwright';
import fs from 'fs-extra';
import path from 'path';

// 配置常量 - 专门针对药品数据页面
const SITE_CONFIG = {
    nmpa: {
        code: "LG0001",
        domain: "www.nmpa.gov.cn",
        name: "国家药品监督管理局",
        // 针对药品数据的特定页面
        dataPageList: [
            // 药品查询相关页面
            "https://www.nmpa.gov.cn/datasearch/home-index.html#category=yp",
            // 药品批准文号相关页面
            "https://www.nmpa.gov.cn/yaowg/index.html",
            // 药品目录页面
            "https://www.nmpa.gov.cn/yaopin/ypml/index.html",
            // 药品说明书相关
            "https://www.nmpa.gov.cn/yaopin/ypsm/index.html"
        ]
    }
};

// 输出目录
const OUTPUT_DIR = 'outputs';
const TEMP_DIR = 'downloads';

// 确保目录存在
fs.ensureDirSync(OUTPUT_DIR);
fs.ensureDirSync(TEMP_DIR);

// 用户代理池 - 专注于真实浏览器
const USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
];

// 随机选择用户代理
function getRandomUserAgent() {
    return USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];
}

// 随机延迟
function randomDelay(min = 2000, max = 6000) {
    return Math.random() * (max - min) + min;
}

// 数据页面专用的绕过策略
async function dataPageBypass(page, url) {
    console.log(`🎯 数据页面专用绕过: ${url}`);

    const userAgent = getRandomUserAgent();
    console.log(`🎭 使用User-Agent: ${userAgent}`);

    // 设置适合数据查询的请求头
    await page.setExtraHTTPHeaders({
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
        'Connection': 'keep-alive',
        'DNT': '1'
    });

    try {
        // 策略1: 先访问首页建立会话
        console.log('🔄 建立会话访问NMPA首页');
        await page.goto('https://www.nmpa.gov.cn/', {
            waitUntil: 'domcontentloaded',
            timeout: 30000
        });

        await page.waitForTimeout(randomDelay(3000, 5000));

        // 模拟正常用户浏览路径
        await page.evaluate(() => {
            window.scrollBy(0, 100);
        });
        await page.waitForTimeout(1000);

        // 策略2: 访问药品频道
        console.log('🔄 访问药品频道页面');
        await page.goto('https://www.nmpa.gov.cn/yaopin/', {
            waitUntil: 'domcontentloaded',
            timeout: 30000
        });

        await page.waitForTimeout(randomDelay(2000, 4000));

        // 策略3: 访问目标数据页面
        console.log('🔄 访问目标数据页面');
        const response = await page.goto(url, {
            waitUntil: 'domcontentloaded',
            timeout: 45000
        });

        const status = response.status();
        console.log(`📊 响应状态: ${status}`);

        if (status === 200) {
            // 等待页面完全加载
            await page.waitForTimeout(3000);

            const content = await page.content();
            console.log(`📄 页面内容长度: ${content.length}`);

            if (content.length > 1000) {
                console.log('✅ 数据页面访问成功');
                return true;
            } else {
                console.log('⚠️ 页面内容过短，可能是错误页面');
            }
        }

    } catch (error) {
        console.log(`⚠️ 策略失败: ${error.message}`);
    }

    // 备用策略：直接访问
    try {
        console.log('🔄 尝试直接访问策略');
        const response = await page.goto(url, {
            waitUntil: 'load',
            timeout: 45000
        });

        if (response.status() === 200) {
            const content = await page.content();
            if (content.length > 1000) {
                console.log('✅ 直接访问策略成功');
                return true;
            }
        }
    } catch (error) {
        console.log(`⚠️ 直接访问失败: ${error.message}`);
    }

    console.log('❌ 所有策略都失败了');
    return false;
}

// 智能药品数据提取 - 专门处理各种数据页面格式
async function extractDrugDataFromPage(page, url) {
    try {
        console.log(`🔍 开始分析页面: ${url}`);

        // 等待页面加载，但不强制等待body元素
        await page.waitForTimeout(3000);

        // 获取页面基本信息
        const pageInfo = await page.evaluate(() => {
            try {
                return {
                    title: document.title || '无标题',
                    url: window.location.href,
                    contentLength: document.body ? document.body.innerText.length : 0,
                    htmlLength: document.documentElement ? document.documentElement.innerHTML.length : 0,
                    hasTables: document.querySelectorAll ? document.querySelectorAll('table').length : 0,
                    hasLists: document.querySelectorAll ? document.querySelectorAll('ul, ol').length : 0,
                    hasLinks: document.querySelectorAll ? document.querySelectorAll('a').length : 0,
                    hasForms: document.querySelectorAll ? document.querySelectorAll('form').length : 0,
                    hasInputs: document.querySelectorAll ? document.querySelectorAll('input').length : 0,
                    hasButtons: document.querySelectorAll ? document.querySelectorAll('button').length : 0,
                    preview: document.body ? document.body.innerText.substring(0, 300) : '无body内容'
                };
            } catch (e) {
                return {
                    title: '获取失败',
                    url: window.location.href,
                    error: e.message
                };
            }
        });

        console.log('📄 页面基本信息:', pageInfo);

        // 如果页面内容很少，可能是动态页面或错误页面
        if (pageInfo.contentLength < 100) {
            console.log('⚠️ 页面内容很少，尝试等待动态内容加载');
            await page.waitForTimeout(5000);

            // 重新获取信息
            const retryInfo = await page.evaluate(() => {
                try {
                    return {
                        contentLength: document.body ? document.body.innerText.length : 0,
                        htmlLength: document.documentElement ? document.documentElement.innerHTML.length : 0,
                        preview: document.body ? document.body.innerText.substring(0, 300) : '无body内容'
                    };
                } catch (e) {
                    return { error: e.message };
                }
            });

            console.log('🔄 重试后页面信息:', retryInfo);
        }

        // 执行药品数据提取
        const drugs = await page.evaluate(() => {
            const results = [];

            try {
                // 获取页面文本
                const bodyText = document.body ? document.body.innerText : '';
                const htmlText = document.documentElement ? document.documentElement.innerHTML : '';

                console.log('页面文本长度:', bodyText.length);
                console.log('页面HTML长度:', htmlText.length);
                console.log('页面预览:', bodyText.substring(0, 200));

                // 多种药品数据提取策略
                const strategies = [
                    // 策略1: 标准国药准字格式
                    /国药准字([A-Z]\d{8})[\s\S]{0,100}?([^\n\r]{2,80}?)(?:[\n\r]|$)/g,
                    // 策略2: 宽松格式
                    /国药准字([A-Z]\d{8})[：:\s]*([^\n\r]{2,80}?)/g,
                    // 策略3: 包含各种字符的格式
                    /国药准字([A-Z]\d{8})[^\n\r]*?([^\n\r]{2,80}?)/g,
                    // 策略4: 表格格式
                    /国药准字([A-Z]\d{8})[\s\S]{1,300}?([^\n\r]{2,100}?)(?:[\n\r]|$)/g,
                    // 策略5: 括号格式
                    /国药准字([A-Z]\d{8})\s*[（\(][^）\)]*[）\)][\s\S]*?([^\n\r]{2,80}?)/g,
                    // 策略6: 药品通用名格式
                    /([^\n\r]{2,50}?)\s*国药准字([A-Z]\d{8})/g
                ];

                for (let i = 0; i < strategies.length; i++) {
                    const regex = strategies[i];
                    console.log(`使用策略 ${i + 1}:`, regex.toString());

                    let match;
                    regex.lastIndex = 0;

                    while ((match = regex.exec(bodyText)) !== null) {
                        let code, name;

                        if (i === 5) { // 策略6：药品名在前
                            name = match[1] ? match[1].trim() : '';
                            code = `国药准字${match[2]}`;
                        } else { // 其他策略：国药准字在前
                            code = `国药准字${match[1]}`;
                            name = match[2] ? match[2].trim() : '';
                        }

                        // 清理药品名称
                        name = name.replace(/[，。、；：""''（）【】\[\]《》\(\)]/g, '').trim();
                        name = name.replace(/\s+/g, ' ').trim();

                        if (name.length > 1 && name.length < 80 && !name.includes('http') && !name.includes('www')) {
                            results.push({
                                code: code,
                                zh: name,
                                en: '',
                                source: `strategy_${i + 1}`,
                                rawMatch: match[0],
                                url: window.location.href,
                                timestamp: new Date().toISOString()
                            });
                            console.log(`找到药品: ${code} - ${name}`);
                        }
                    }
                }

                // 去重处理
                const uniqueResults = [];
                const seen = new Set();

                results.forEach(item => {
                    const key = item.code;
                    if (!seen.has(key)) {
                        seen.add(key);
                        uniqueResults.push(item);
                    }
                });

                console.log(`去重后药品数量: ${uniqueResults.length}`);
                return uniqueResults;

            } catch (error) {
                console.error('页面提取过程出错:', error.message);
                return [];
            }
        });

        console.log(`📦 最终提取到 ${drugs.length} 个药品信息`);
        if (drugs.length > 0) {
            console.log('药品示例:', drugs.slice(0, 3));
        }

        return drugs;

    } catch (error) {
        console.error('提取药品数据失败:', error);
        return [];
    }
}

// 发现药品相关链接
async function discoverDataLinks(page) {
    try {
        const links = await page.evaluate(() => {
            const results = [];

            try {
                const links = document.querySelectorAll('a[href]');
                const currentDomain = window.location.hostname;

                // 扩展的药品相关关键词
                const drugKeywords = [
                    '药品', '批准', '查询', '目录', '数据库', '准字', '说明书', '注册', '备案',
                    '品种', '名录', '清单', '公示', '通告', '公告', '名单',
                    'drug', 'approval', 'database', 'catalog', 'license', 'registration',
                    '进口', '国产', '化学药', '中药', '生物制品', '疫苗', '血液制品'
                ];

                // NMPA数据页面特定路径模式
                const dataPatterns = [
                    /\/datasearch\//,
                    /\/yaopin\//,
                    /\/yp[a-z]+\//,
                    /\/WS\d+\//,
                    /\/CL\d+\//,
                    /\/药品\//,
                    /\/query\//,
                    /\/search\//,
                    /\/list\//,
                    /\/data\//,
                    /\/tg\//,
                    /\/gg\//,
                    /\/gs\//,
                    /\/ml\//,  // 目录
                    /\/pzwh\//, // 批准文号
                    /\/sms\//   // 说明书
                ];

                links.forEach(link => {
                    try {
                        const href = link.getAttribute('href');
                        const text = link.innerText.trim();

                        if (href && (href.startsWith('http') || href.startsWith('/'))) {
                            const fullUrl = href.startsWith('http') ? href : new URL(href, window.location.origin).href;

                            // 检查是否是相关链接
                            const isDrugRelated = drugKeywords.some(keyword =>
                                text.toLowerCase().includes(keyword.toLowerCase()) ||
                                href.toLowerCase().includes(keyword.toLowerCase())
                            );

                            const isDataPage = dataPatterns.some(pattern => pattern.test(href));
                            const isSameDomain = fullUrl.includes(currentDomain) || fullUrl.includes('nmpa.gov.cn');

                            // 排除一些不相关的链接
                            const isIrrelevant = href.includes('javascript:') ||
                                               href.includes('mailto:') ||
                                               href.includes('tel:') ||
                                               text.includes('更多') ||
                                               text.includes('查看更多') ||
                                               text.length < 2;

                            if ((isDrugRelated || isDataPage) && isSameDomain && !isIrrelevant) {
                                results.push({
                                    url: fullUrl,
                                    text: text,
                                    source: isDrugRelated ? 'keyword' : 'pattern'
                                });
                            }
                        }
                    } catch (e) {
                        // 忽略单个链接的错误
                    }
                });

                // 去重并返回最相关的链接
                const uniqueLinks = [];
                const seen = new Set();

                results.forEach(link => {
                    if (!seen.has(link.url)) {
                        seen.add(link.url);
                        uniqueLinks.push(link);
                    }
                });

                return uniqueLinks.slice(0, 20); // 增加链接数量

            } catch (error) {
                console.error('链接发现过程出错:', error.message);
                return [];
            }
        });

        console.log(`🔗 发现 ${links.length} 个可能相关的数据链接`);
        if (links.length > 0) {
            console.log('链接示例:', links.slice(0, 3).map(l => ({ text: l.text, url: l.url })));
        }

        return links;

    } catch (error) {
        console.error('发现链接失败:', error);
        return [];
    }
}

// 保存数据到文件
async function saveDrugData(drugs, pageUrl, source = 'unknown') {
    if (drugs.length === 0) return;

    try {
        const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
        const filename = `drugs_${source}_${timestamp}.jsonl`;
        const filepath = path.join(OUTPUT_DIR, filename);

        // 为每条记录添加来源信息
        const enrichedDrugs = drugs.map(drug => ({
            ...drug,
            source_page: pageUrl,
            source_type: source,
            crawl_time: new Date().toISOString()
        }));

        const jsonlData = enrichedDrugs.map(drug => JSON.stringify(drug)).join('\n');
        await fs.writeFile(filepath, jsonlData, 'utf8');

        console.log(`💾 保存 ${drugs.length} 个药品到: ${filename}`);

        // 追加到主文件
        const mainFile = path.join(OUTPUT_DIR, 'drugs_all.jsonl');
        await fs.appendFile(mainFile, jsonlData + '\n', 'utf8');

        // 保存详细的页面分析报告
        const reportFile = path.join(TEMP_DIR, `page_analysis_${timestamp}.json`);
        const report = {
            url: pageUrl,
            source: source,
            timestamp: new Date().toISOString(),
            drugs_found: drugs.length,
            drugs_sample: drugs.slice(0, 3),
            analysis: '数据页面专用爬虫'
        };
        await fs.writeFile(reportFile, JSON.stringify(report, null, 2), 'utf8');

    } catch (error) {
        console.error('保存数据失败:', error);
    }
}

// 主数据爬虫函数
async function runDataNMPACrawler() {
    console.log('🚀 启动NMPA药品数据专用爬虫');
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
        timezoneId: 'Asia/Shanghai',
        permissions: [],
        ignoreHTTPSErrors: true
    });

    // 添加反检测脚本
    await context.addInitScript(`
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        window.chrome = { runtime: {} };
        console.log('反检测脚本加载完成');
    `);

    try {
        const siteConfig = SITE_CONFIG.nmpa;
        const dataPageList = siteConfig.dataPageList;

        console.log(`🎯 站点: ${siteConfig.name} (${siteConfig.code})`);
        console.log(`📋 数据页面数量: ${dataPageList.length}`);

        let totalDrugs = 0;
        const visitedUrls = new Set();

        for (const url of dataPageList) {
            if (visitedUrls.has(url)) {
                console.log(`⚠️ 跳过已访问的URL: ${url}`);
                continue;
            }

            console.log(`\n🔄 处理数据页面: ${url}`);
            visitedUrls.add(url);

            const page = await context.newPage();

            try {
                // 使用数据页面专用绕过策略
                const success = await dataPageBypass(page, url);

                if (success) {
                    // 提取药品数据
                    const drugs = await extractDrugDataFromPage(page, url);
                    totalDrugs += drugs.length;

                    // 保存数据
                    await saveDrugData(drugs, url, 'data_page');

                    // 如果当前页面有药品数据或链接，查找更多相关链接
                    if (drugs.length > 0 || true) { // 总是查找链接以探索更多页面
                        console.log('🔍 查找相关数据链接...');
                        const relatedLinks = await discoverDataLinks(page);

                        if (relatedLinks.length > 0) {
                            console.log(`🔗 发现 ${relatedLinks.length} 个相关链接，开始跟进...`);

                            // 跟进最有希望的链接
                            for (let i = 0; i < Math.min(relatedLinks.length, 8); i++) {
                                const linkInfo = relatedLinks[i];
                                const linkUrl = linkInfo.url;

                                if (visitedUrls.has(linkUrl)) {
                                    console.log(`⚠️ 跳过已访问的链接: ${linkUrl}`);
                                    continue;
                                }

                                console.log(`🔍 跟进链接 ${i + 1}/${Math.min(relatedLinks.length, 8)}: ${linkInfo.text} -> ${linkUrl}`);
                                visitedUrls.add(linkUrl);

                                try {
                                    const linkPage = await context.newPage();
                                    const linkSuccess = await dataPageBypass(linkPage, linkUrl);

                                    if (linkSuccess) {
                                        const linkDrugs = await extractDrugDataFromPage(linkPage, linkUrl);
                                        totalDrugs += linkDrugs.length;

                                        if (linkDrugs.length > 0) {
                                            console.log(`✅ 链接成功提取到 ${linkDrugs.length} 个药品信息`);
                                            await saveDrugData(linkDrugs, linkUrl, 'discovered_link');
                                        } else {
                                            console.log('⚠️ 链接页面未发现药品数据，但可能包含其他有用信息');
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
                    console.log(`❌ 无法访问数据页面: ${url}`);
                }

            } catch (error) {
                console.error(`处理数据页面失败: ${url}`, error.message);
            } finally {
                await page.close();
            }
        }

        console.log(`\n🎉 数据爬虫运行完成! 总共提取 ${totalDrugs} 个药品信息`);

        // 显示详细结果统计
        try {
            const files = await fs.readdir(OUTPUT_DIR);
            const jsonlFiles = files.filter(f => f.endsWith('.jsonl'));

            console.log('\n📊 详细结果统计:');
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
        console.error('数据爬虫运行失败:', error);
    } finally {
        await browser.close();
    }
}

// 启动应用
runDataNMPACrawler().catch(console.error);