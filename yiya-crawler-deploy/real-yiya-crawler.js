// 真实yiya-crawler - 不依赖复杂框架，直接获取NMPA数据
import fs from 'fs-extra';
import path from 'path';

console.log('🚀 启动真实yiya-crawler - 获取NMPA真实数据');

// 配置
const OUTPUT_DIR = 'outputs';
const NMPA_URLS = [
    'https://www.nmpa.gov.cn/yaopin/ypggtg/index.html',  // 药品公告通知
    'https://www.nmpa.gov.cn/yaopin/ypjgdt/index.html'   // 药品监管动态
];

// 确保输出目录存在
fs.ensureDirSync(OUTPUT_DIR);

// 简单的HTTP请求函数
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
                'Pragma': 'no-cache'
            },
            credentials: 'omit'
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
            url: url
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

    // 提取国药准字数据
    const drugRegex = /国药准字([A-Z]\d{8})[^\n\r]*?([^\n\r]{2,50}?)/g;
    let match;

    while ((match = drugRegex.exec(content)) !== null) {
        const code = `国药准字${match[1]}`;
        let name = match[2] ? match[2].trim() : '';

        // 清理药品名称
        name = name.replace(/[，。、；：""''（）【】\[\]《》\s]/g, '').trim();

        if (name.length > 1 && name.length < 50) {
            drugs.push({
                code: code,
                name: name,
                source: url,
                extractedAt: new Date().toISOString()
            });
            console.log(`💊 发现药品: ${code} - ${name}`);
        }
    }

    // 如果没有找到标准格式，尝试其他模式
    if (drugs.length === 0) {
        console.log(`🔍 尝试其他提取模式...`);

        // 查找药品相关的文本段落
        const paragraphs = content.split('\n');
        for (const paragraph of paragraphs) {
            if (paragraph.includes('药品') && paragraph.length > 20 && paragraph.length < 200) {
                const cleanText = paragraph.trim().replace(/[<>]/g, '');
                if (cleanText.length > 10) {
                    drugs.push({
                        code: '未知',
                        name: cleanText.substring(0, 50),
                        source: url,
                        extractedAt: new Date().toISOString(),
                        type: '相关文本'
                    });
                }
            }
        }
    }

    console.log(`📦 共提取到 ${drugs.length} 个药品信息`);
    return drugs;
}

// 保存数据
async function saveData(drugs, url) {
    if (drugs.length === 0) {
        console.log(`⚠️ 没有找到药品数据，跳过保存`);
        return;
    }

    try {
        const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
        const filename = `yiya_drugs_${timestamp}.jsonl`;
        const filepath = path.join(OUTPUT_DIR, filename);

        const jsonlData = drugs.map(drug => JSON.stringify(drug)).join('\n');
        await fs.writeFile(filepath, jsonlData, 'utf8');

        console.log(`💾 成功保存 ${drugs.length} 个药品到: ${filename}`);

        // 追加到汇总文件
        const summaryFile = path.join(OUTPUT_DIR, 'yiya_drugs_all.jsonl');
        await fs.appendFile(summaryFile, jsonlData + '\n', 'utf8');

    } catch (error) {
        console.error(`❌ 保存数据失败: ${error.message}`);
    }
}

// 主爬虫函数
async function runRealYiyaCrawler() {
    console.log('🎯 开始真实yiya-crawler运行...');
    console.log(`📋 目标URL数量: ${NMPA_URLS.length}`);

    let totalDrugs = 0;
    let successCount = 0;

    for (let i = 0; i < NMPA_URLS.length; i++) {
        const url = NMPA_URLS[i];
        console.log(`\n🔄 处理URL ${i + 1}/${NMPA_URLS.length}: ${url}`);

        try {
            // 获取页面内容
            const pageResult = await fetchPage(url);

            if (pageResult.success) {
                successCount++;
                console.log(`📄 页面信息: ${pageResult.status} - ${pageResult.content.length} 字符`);

                // 提取药品数据
                const drugs = extractDrugData(pageResult.content, url);
                totalDrugs += drugs.length;

                // 保存数据
                await saveData(drugs, url);

                // 显示页面预览
                const preview = pageResult.content.substring(0, 300);
                console.log(`📋 页面预览: ${preview}...`);

            } else {
                console.error(`❌ 页面获取失败: ${pageResult.error}`);
            }

            // 添加延迟避免被封锁
            if (i < NMPA_URLS.length - 1) {
                console.log(`⏳ 等待 3 秒后继续...`);
                await new Promise(resolve => setTimeout(resolve, 3000));
            }

        } catch (error) {
            console.error(`❌ 处理URL失败: ${error.message}`);
        }
    }

    // 显示运行结果
    console.log(`\n🎉 yiya-crawler 运行完成!`);
    console.log(`📊 结果统计:`);
    console.log(`  ✅ 成功页面: ${successCount}/${NMPA_URLS.length}`);
    console.log(`  💊 药品总数: ${totalDrugs}`);
    console.log(`  📁 输出目录: ${OUTPUT_DIR}`);

    // 显示文件列表
    try {
        const files = await fs.readdir(OUTPUT_DIR);
        const jsonlFiles = files.filter(f => f.includes('yiya_drugs'));

        if (jsonlFiles.length > 0) {
            console.log(`\n📄 生成的文件:`);
            for (const file of jsonlFiles) {
                const filepath = path.join(OUTPUT_DIR, file);
                const stats = await fs.stat(filepath);
                console.log(`  📋 ${file} (${stats.size} bytes)`);
            }
        }

    } catch (error) {
        console.log(`读取输出文件失败: ${error.message}`);
    }

    return {
        success: true,
        totalPages: NMPA_URLS.length,
        successPages: successCount,
        totalDrugs: totalDrugs,
        outputDir: OUTPUT_DIR
    };
}

// 启动爬虫
runRealYiyaCrawler().catch(error => {
    console.error('🚨 yiya-crawler 运行失败:', error.message);
    process.exit(1);
});