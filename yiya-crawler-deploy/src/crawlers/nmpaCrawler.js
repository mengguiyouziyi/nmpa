import { PuppeteerCrawler } from 'crawlee';
import { handleWeb2Pdf, createNewPage } from '../utils/fileHandler.js';
import { isDateAfterAprilFirst } from '../utils/urlFilter.js';
import { logger } from '../utils/logger.js';
import { SITE_CONFIG } from '../config/constants.js';

const siteCode = SITE_CONFIG.nmpa.code;
const siteName = SITE_CONFIG.nmpa.name;
const siteDomain = SITE_CONFIG.nmpa.domain;

export const nmpaCrawler = new PuppeteerCrawler({
  // 增加导航和请求超时
  navigationTimeoutSecs: 60,
  requestHandlerTimeoutSecs: 60,
  
  // 调整重试策略
  maxRequestRetries: parseInt(process.env.MAX_RETRIES || 3),          // 最大重试次数
  // retryOnBlocked: true,          // 被屏蔽时重试
  // sessionPoolOptions: {
  //   sessionOptions: {
  //     maxUsageCount: 5,          // 单个会话的最大使用次数
  //     maxAgeSecs: 1800           // 会话有效期（秒）
  //   }
  // },
  
  // 浏览器配置
  launchContext: {
    launchOptions: {
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
  },
  
  // 爬虫配置
  maxRequestsPerCrawl: parseInt(process.env.MAX_PAGES || 50),
  maxConcurrency: parseInt(process.env.MAX_CONCURRENCY || 2),
  headless: true,

  async requestHandler({ request, page, enqueueLinks }) {
    if (request.url.indexOf(siteDomain) == -1) {
      logger.info("not a nmpa site request:" + request.url);
      return;
    }
    logger.info(`-------------(nmpa) request url: ${request.url}`);
    if (request.url.indexOf('index.html') > -1) { // 常规列表页面
      await page.waitForSelector('.list li');
    
      // 提取法规文件列表
      const items = await page.$$eval('.list li', (elements) => {
        return elements.map((el) => {
            const title = el.querySelector('a')?.innerText.trim();
            const href = el.querySelector('a')?.href;
            const date = el.querySelector('span')?.innerText.trim();
            const parentUrl = window.location.href;
            return { title, href, date, parentUrl };
        });
      });
    
      // 处理url堆栈
      for (const item of items) {
        if (!!item.date) {
          if (isDateAfterAprilFirst(item.date)) { // 检查时间字段
            logger.info(`${SITE_CONFIG.nmpa.code}: [time check passed]: ${item.date}, ${item.title}`);
            item.date = item.date.slice(1, -1);
            await createNewPage(siteDomain, siteName, siteCode, item.href, item);
            await enqueueLinks({ 
              urls: [item.href], 
              transformRequestFunction(req) { 
                logger.info(`>>> reqUrl=${req.url}`);
                return req; 
              },
              limit: parseInt(process.env.CRAWL_QUEUE_SIZE || 4)
            });
          } else {
            logger.warn(`${siteCode}: time not valid:${item.date}, href=${item.href}`);
          }
        } else {
          logger.warn(`${siteCode}: not time found, href=${item.href}`);
        }
      }
    } else {
      // 准备临时目录
      // await ensureTempDir();
      await page.waitForSelector('h2.title');
      logger.info(`>>>>${siteCode}: im visiting page now! title=${await page.title()}, url=${request.url}`);
      await handleWeb2Pdf(request, page, siteCode, siteName);
    }
  }
});