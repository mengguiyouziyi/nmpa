import dotenv from 'dotenv';
import { nmpaCrawler } from './src/crawlers/nmpaCrawler.js';
import { nmpaOnetimeCrawler } from './src/crawlers/nmpaOnetimeCrawler.js';
import { nifdcCrawler } from './src/crawlers/nifdcCrawler.js';
import { standaloneCrawler } from './src/crawlers/standaloneCrawler.js';
import { SITE_CONFIG } from './src/config/constants.js';
import { batchCreateYiyaJobs } from './src/services/yiya.js'
import { logger } from './src/utils/logger.js';

dotenv.config();
const YIYA_JOB_FREQUENCY = process.env.YIYA_JOB_FREQUENCY || 60;

// 每小时执行的任务
async function hourlyJob() {
  try {
    logger.info('每小时任务 - 开始...');
    await batchCreateYiyaJobs();
    logger.info('每小时任务 - 完成');
  } catch (error) {
    logger.error('每小时任务 - 失败:', error);
  }
}

(async () => {
  try {
    // 首次立即执行一次（可选）
    await hourlyJob();
    // 设置每小时执行一次
    setInterval(hourlyJob, 60 * YIYA_JOB_FREQUENCY * 1000);

    // 启动爬虫 - nmpa
    await nmpaCrawler.run(SITE_CONFIG.nmpa.pageList);
    await nmpaOnetimeCrawler.run(SITE_CONFIG.nmpa.oneTimePageList);
    // 启动爬虫 - nifdc
    await nifdcCrawler.run(SITE_CONFIG.nifdc.pageList);
    await standaloneCrawler.run(SITE_CONFIG.standalone);
    logger.info('Crawling and PDF upload completed!');
  } catch (err) {
    console.error('Crawler failed:', err);
  }
})();
