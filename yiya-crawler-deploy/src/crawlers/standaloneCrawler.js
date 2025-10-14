import { PuppeteerCrawler } from 'crawlee';
import { handleWeb2Pdf } from '../utils/fileHandler.js';
import { logger } from '../utils/logger.js';
import { SITE_CONFIG } from '../config/constants.js';
// import fs from 'fs/promises';
import dotenv from 'dotenv';

dotenv.config();


export const standaloneCrawler = new PuppeteerCrawler({
  // 增加导航和请求超时
  navigationTimeoutSecs: 60,
  requestHandlerTimeoutSecs: 60,
  
  // 调整重试策略
  maxRequestRetries: 3,          // 最大重试次数
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
  maxConcurrency: 2,
  headless: true,

  async requestHandler({ request, page, enqueueLinks }) {
    console.debug(`-------------request url: ${request.url}`);
    // if (request.url.indexOf(SITE_CONFIG.nmpa.domain) == -1 && request.url.indexOf(SITE_CONFIG.nmpa.secondaryDomain) == -1) {
    //   logger.info("This is not a nmpa site request:" + request.url);
    //   return;
    // }
    if (request.url.indexOf('hasOldFixed') > -1) { // 常规列表页面
      // await page.waitForSelector('.main-inner-list li');
      // const items = await page.$$eval('.main-inner-list li', (elements) => {
      //   return elements.map((el) => {
      //       const title = el.querySelector('a')?.innerText.trim();
      //       const href = el.querySelector('a')?.href;
      //       return { title, href };
      //   });
      // });
    
      // // 处理url堆栈
      // for (const item of items) {
      //   if (!!item.href) {
          await enqueueLinks({ 
            urls: [item.href], 
            transformRequestFunction(req) { 
              logger.info(`>>> reqUrl=${req.url}`);
              return req; 
            },
            limit: parseInt(process.env.CRAWL_QUEUE_SIZE || 4)
          });
        // }
      // }
    } else {
      // 准备临时目录
      // await ensureTempDir();
      await page.waitForSelector('body');
      logger.debug(`>>>>im visiting page now! title=${await page.title()}, url=${request.url}`);
      await handleWeb2Pdf(request, page, SITE_CONFIG.nmpa.code, SITE_CONFIG.nmpa.name);
    }
  }
});