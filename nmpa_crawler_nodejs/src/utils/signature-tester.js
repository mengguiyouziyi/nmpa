// 签名测试器 - 验证破解算法
import NMPASignatureCracker from './signature-cracker.js';

console.log('🧪 启动NMPA签名算法测试器...');

const cracker = new NMPASignatureCracker();

// 测试参数（基于真实请求）
const testParams = {
    itemId: 'ff80808183cad75001840881f848179f',
    isSenior: 'N',
    searchValue: '国药准字H',
    pageNum: '1',
    pageSize: '10'
};

const testUrl = 'https://www.nmpa.gov.cn/datasearch/data/nmpadata/search';

console.log('\n📊 测试配置:');
console.log('测试URL:', testUrl);
console.log('测试参数:', testParams);
console.log('');

// 测试所有签名算法
console.log('🔍 开始测试所有签名算法...');
const results = cracker.testAllAlgorithms(testUrl, testParams);

// 测试真实请求签名生成
console.log('\n🎯 测试真实请求签名生成...');
const realResult = cracker.autoDetectAndCrack(testUrl, { ...testParams });

console.log('🔐 自动检测结果:');
console.log('  算法:', realResult.algorithm);
console.log('  签名:', realResult.sign);
console.log('  时间戳:', realResult.timestamp);
console.log('  其他参数:', realResult);

if (realResult.alternatives) {
    console.log('  备选签名:');
    realResult.alternatives.forEach((alt, index) => {
        console.log(`    ${index + 1}. ${alt.substring(0, 16)}...`);
    });
}

// 测试请求头生成
console.log('\n📡 测试请求头生成...');
const { headers, signData } = cracker.generateHeaders(testUrl, { ...testParams });

console.log('生成的请求头:');
Object.entries(headers).forEach(([key, value]) => {
    if (key.toLowerCase().includes('sign') || key.toLowerCase().includes('timestamp')) {
        console.log(`  ${key}: ${value}`);
    }
});

console.log('\n🎉 签名测试完成!');

// 导出用于外部使用
export { NMPASignatureCracker, testParams, testUrl };