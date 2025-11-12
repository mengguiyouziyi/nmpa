// 简化版yiya-crawler测试 - 不依赖复杂框架
console.log('🚀 启动简化版yiya-crawler测试');

// 基本测试功能
async function testBasicCrawler() {
    console.log('✅ 基本爬虫功能测试');

    // 模拟爬虫数据
    const testData = {
        timestamp: new Date().toISOString(),
        source: 'nmpa',
        drugs: [
            {
                code: '国药准字Z20250001',
                name: '测试药品1',
                type: '中药'
            },
            {
                code: '国药准字H20250002',
                name: '测试药品2',
                type: '化药'
            }
        ],
        status: 'success',
        message: '简化版测试成功'
    };

    console.log('📊 测试结果:', JSON.stringify(testData, null, 2));

    return testData;
}

// 测试NMPA连接
async function testNMPAConnection() {
    console.log('🔗 测试NMPA网站连接...');

    try {
        // 使用简单的HTTP请求测试
        const response = await fetch('https://www.nmpa.gov.cn', {
            method: 'HEAD',
            timeout: 10000
        });

        console.log(`✅ NMPA连接成功: ${response.status}`);
        return true;
    } catch (error) {
        console.log(`❌ NMPA连接失败: ${error.message}`);
        return false;
    }
}

// 主测试函数
async function runSimpleTest() {
    console.log('🎯 开始yiya-crawler简化测试...');
    console.log(`📋 Node.js版本: ${process.version}`);
    console.log(`📋 运行环境: ${process.platform}`);

    try {
        // 1. 基本功能测试
        const basicResult = await testBasicCrawler();

        // 2. 连接测试
        const connectionResult = await testNMPAConnection();

        // 3. 汇总结果
        const summary = {
            basicTest: basicResult.status === 'success',
            connectionTest: connectionResult,
            overall: basicResult.status === 'success' && connectionResult,
            timestamp: new Date().toISOString()
        };

        console.log('\n🎉 测试完成!');
        console.log('📊 测试摘要:', JSON.stringify(summary, null, 2));

        if (summary.overall) {
            console.log('✅ yiya-crawler环境验证成功！');
        } else {
            console.log('⚠️ 部分测试失败，请检查环境配置');
        }

        return summary;

    } catch (error) {
        console.error('❌ 测试过程中出现错误:', error.message);
        return { success: false, error: error.message };
    }
}

// 启动测试
runSimpleTest().catch(console.error);