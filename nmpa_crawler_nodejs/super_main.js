import { runDatasetCrawler } from './src/dataset_crawler.js';

(async () => {
    console.log('🚀 超级增强版 - 药品数据采集任务启动');
    try {
        const result = await runDatasetCrawler();
        if (result?.runId) {
            console.log(`📁 本次运行 ID: ${result.runId}`);
        }
        if (result?.datasetsDir) {
            console.log(`📂 数据输出目录: ${result.datasetsDir}`);
        }
        console.log('🎉 超级增强版任务完成，详情记录已写入上述目录');
    } catch (error) {
        console.error('❌ 超级增强版任务失败:', error);
        process.exitCode = 1;
    }
})();
