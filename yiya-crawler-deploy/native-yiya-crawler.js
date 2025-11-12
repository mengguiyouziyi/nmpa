// 原生yiya-crawler - 只使用Node.js内置模块，获取真实NMPA数据
import fs from 'fs';
import path from 'path';
import { createWriteStream } from 'fs';

console.log('🚀 启动原生yiya-crawler - 获取真实NMPA数据');

// 配置
const OUTPUT_DIR = 'outputs';
const NMPA_URLS = [
    'https://www.nmpa.gov.cn/yaopin/ypggtg/index.html',  // 药品公告通知
    'https://www.nmpa.gov.cn/yaopin/ypjgdt/index.html'   // 药品监管动态
];

// 确保输出目录存在
if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

// 简单的HTTP请求函数（使用原生fetch）
async function fetchPage(url) {
    try {
        console.log(`🔗 正在获取页面: ${url}`);

        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const text = await response.text();
        console.log(`✅ 页面获取成功，内容长度: ${text.length} 字符`);

        return {
            success: true,
            status: response.status,
            content: text,
            url: url,
            headers: Object.fromEntries(response.headers.entries())
        };

    } catch (error) {
        console.error(`❌ 页面获取失败: ${error.message}`);
        return {
            success: false,
            error: error.message,
            url: url
        };
    }
}

// 提取药品数据
function extractDrugData(content, url) {
    console.log(`🔍 开始提取药品数据...`);

    const drugs = [];

    // 策略1: 标准国药准字格式
    const standardRegex = /国药准字([A-Z]\d{8})[\s\S]{0,50}?([^\n\r]{2,50}?)(?:[\n\r]|$)/g;
    let match;

    while ((match = standardRegex.exec(content)) !== null) {
        const code = `国药准字${match[1]}`;
        let name = match[2] ? match[2].trim() : '';

        // 清理药品名称
        name = name.replace(/[，。、；：""''（）【】\[\]《》\s<>]/g, '').trim();

        if (name.length > 1 && name.length < 50) {
            drugs.push({
                code: code,
                name: name,
                source: url,
                extractedAt: new Date().toISOString(),
                strategy: 'standard'
            });
            console.log(`💊 发现药品(标准): ${code} - ${name}`);
        }
    }

    // 策略2: 宽松格式匹配
    if (drugs.length === 0) {
        const looseRegex = /国药准字([A-Z]\d{8})[^\n\r]*?([^\n\r]{2,50}?)/g;
        while ((match = looseRegex.exec(content)) !== null) {
            const code = `国药准字${match[1]}`;
            let name = match[2] ? match[2].trim() : '';

            name = name.replace(/[，。、；：""''（）【】\[\]《》\s<>]/g, '').trim();

            if (name.length > 1 && name.length < 50) {
                drugs.push({
                    code: code,
                    name: name,
                    source: url,
                    extractedAt: new Date().toISOString(),
                    strategy: 'loose'
                });
                console.log(`💊 发现药品(宽松): ${code} - ${name}`);
            }
        }
    }

    // 策略3: 药品相关文本提取
    if (drugs.length === 0) {
        console.log(`🔍 尝试提取药品相关文本...`);

        const drugKeywords = ['药品', '批准', '上市', '生产', '注册', '备案'];
        const lines = content.split('\n');

        for (const line of lines) {
            const cleanLine = line.trim().replace(/<[^>]*>/g, '');

            if (cleanLine.length > 10 && cleanLine.length < 200) {
                const hasDrugKeyword = drugKeywords.some(keyword =>
                    cleanLine.includes(keyword)
                );

                if (hasDrugKeyword) {
                    drugs.push({
                        code: '相关文本',
                        name: cleanLine.substring(0, 100),
                        source: url,
                        extractedAt: new Date().toISOString(),
                        strategy: 'text',
                        originalText: cleanLine
                    });
                    console.log(`📄 发现相关文本: ${cleanLine.substring(0, 50)}...`);
                }
            }
        }
    }

    console.log(`📦 共提取到 ${drugs.length} 个药品信息`);
    return drugs;
}

// 保存数据（原生方式）
function saveData(drugs, url) {
    if (drugs.length === 0) {
        console.log(`⚠️ 没有找到药品数据，跳过保存`);
        return;
    }

    try {
        const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
        const filename = `yiya_drugs_${timestamp}.jsonl`;
        const filepath = path.join(OUTPUT_DIR, filename);

        const jsonlData = drugs.map(drug => JSON.stringify(drug)).join('\n');
        fs.writeFileSync(filepath, jsonlData, 'utf8');

        console.log(`💾 成功保存 ${drugs.length} 个药品到: ${filename}`);

        // 追加到汇总文件
        const summaryFile = path.join(OUTPUT_DIR, 'yiya_drugs_all.jsonl');
        fs.appendFileSync(summaryFile, jsonlData + '\n', 'utf8');

    } catch (error) {
        console.error(`❌ 保存数据失败: ${error.message}`);
    }
}

// 保存页面内容用于调试
function savePageContent(content, url, status) {
    try {
        const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
        const filename = `page_${timestamp}_${status}.html`;
        const filepath = path.join(OUTPUT_DIR, filename);

        fs.writeFileSync(filepath, content, 'utf8');
        console.log(`📄 页面内容已保存: ${filename}`);

        return filepath;
    } catch (error) {
        console.error(`❌ 保存页面内容失败: ${error.message}`);
        return null;
    }
}

// 主爬虫函数
async function runNativeYiyaCrawler() {
    console.log('🎯 开始原生yiya-crawler运行...');
    console.log(`📋 目标URL数量: ${NMPA_URLS.length}`);
    console.log(`📁 输出目录: ${OUTPUT_DIR}`);

    let totalDrugs = 0;
    let successCount = 0;
    const results = [];

    for (let i = 0; i < NMPA_URLS.length; i++) {
        const url = NMPA_URLS[i];
        console.log(`\n🔄 处理URL ${i + 1}/${NMPA_URLS.length}: ${url}`);

        try {
            // 获取页面内容
            const pageResult = await fetchPage(url);

            if (pageResult.success) {
                successCount++;
                console.log(`📄 页面信息: ${pageResult.status} - ${pageResult.content.length} 字符`);

                // 保存页面内容用于调试
                const savedFile = savePageContent(pageResult.content, url, pageResult.status);

                // 显示页面预览
                const preview = pageResult.content.replace(/<[^>]*>/g, '').substring(0, 200);
                console.log(`📋 页面预览: ${preview}...`);

                // 提取药品数据
                const drugs = extractDrugData(pageResult.content, url);
                totalDrugs += drugs.length;

                // 保存数据
                saveData(drugs, url);

                // 记录结果
                results.push({
                    url: url,
                    status: pageResult.status,
                    contentLength: pageResult.content.length,
                    drugsFound: drugs.length,
                    savedFile: savedFile,
                    success: true
                });

            } else {
                console.error(`❌ 页面获取失败: ${pageResult.error}`);

                results.push({
                    url: url,
                    error: pageResult.error,
                    success: false
                });
            }

            // 添加延迟避免被封锁
            if (i < NMPA_URLS.length - 1) {
                console.log(`⏳ 等待 3 秒后继续...`);
                await new Promise(resolve => setTimeout(resolve, 3000));
            }

        } catch (error) {
            console.error(`❌ 处理URL失败: ${error.message}`);

            results.push({
                url: url,
                error: error.message,
                success: false
            });
        }
    }

    // 生成运行报告
    console.log(`\n🎉 原生yiya-crawler 运行完成!`);
    console.log(`📊 结果统计:`);
    console.log(`  ✅ 成功页面: ${successCount}/${NMPA_URLS.length}`);
    console.log(`  💊 药品总数: ${totalDrugs}`);
    console.log(`  📁 输出目录: ${OUTPUT_DIR}`);

    // 显示详细结果
    console.log(`\n📋 详细结果:`);
    results.forEach((result, index) => {
        if (result.success) {
            console.log(`  ${index + 1}. ✅ ${result.url}`);
            console.log(`     状态: ${result.status}, 内容: ${result.contentLength} 字符`);
            console.log(`     药品: ${result.drugsFound} 个`);
            if (result.savedFile) {
                console.log(`     文件: ${result.savedFile}`);
            }
        } else {
            console.log(`  ${index + 1}. ❌ ${result.url}`);
            console.log(`     错误: ${result.error}`);
        }
    });

    // 显示文件列表
    try {
        const files = fs.readdirSync(OUTPUT_DIR);
        const relevantFiles = files.filter(f =>
            f.includes('yiya_drugs') || f.includes('page_')
        );

        if (relevantFiles.length > 0) {
            console.log(`\n📄 生成的文件:`);
            for (const file of relevantFiles) {
                const filepath = path.join(OUTPUT_DIR, file);
                const stats = fs.statSync(filepath);
                console.log(`  📋 ${file} (${stats.size} bytes)`);
            }
        }

    } catch (error) {
        console.log(`读取输出文件失败: ${error.message}`);
    }

    // 保存运行报告
    const report = {
        timestamp: new Date().toISOString(),
        totalPages: NMPA_URLS.length,
        successPages: successCount,
        totalDrugs: totalDrugs,
        outputDir: OUTPUT_DIR,
        results: results,
        summary: {
            successRate: Math.round(successCount / NMPA_URLS.length * 100),
            avgDrugsPerPage: Math.round(totalDrugs / successCount * 10) / 10
        }
    };

    try {
        const reportFile = path.join(OUTPUT_DIR, `yiya_crawler_report_${new Date().toISOString().slice(0, 19).replace(/[:-]/g, '')}.json`);
        fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));
        console.log(`📊 运行报告已保存: ${reportFile}`);
    } catch (error) {
        console.error(`保存报告失败: ${error.message}`);
    }

    return report;
}

// 启动爬虫
runNativeYiyaCrawler().catch(error => {
    console.error('🚨 原生yiya-crawler 运行失败:', error.message);
    process.exit(1);
});