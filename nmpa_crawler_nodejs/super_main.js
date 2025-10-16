import { runDatasetCrawler } from './src/dataset_crawler.js';

(async () => {
    console.log('🚀 超级增强版 - 药品数据采集任务启动');
    try {
        await runDatasetCrawler();
        console.log('🎉 超级增强版任务完成，数据已保存至 outputs/datasets');
    } catch (error) {
        console.error('❌ 超级增强版任务失败:', error);
        process.exitCode = 1;
    }
})();
