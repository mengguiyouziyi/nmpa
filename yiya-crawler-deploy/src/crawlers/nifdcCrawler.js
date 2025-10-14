import { PuppeteerCrawler } from 'crawlee';
import { handleWeb2Pdf, createNewPage } from '../utils/fileHandler.js';
import { isDateAfterAprilFirst } from '../utils/urlFilter.js';
import { logger } from '../utils/logger.js';
import { SITE_CONFIG } from '../config/constants.js';


const siteCode = SITE_CONFIG.nifdc.code;
const siteName = SITE_CONFIG.nifdc.name;
const siteDomain = SITE_CONFIG.nifdc.domain;

export const nifdcCrawler = new PuppeteerCrawler({
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
    console.debug(`-------------(nifdc)request url: ${request.url}`);
    if (request.url.lastIndexOf('index.html') > -1) { // 常规列表页面
      console.log('check index.html:' + request.url);
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
      // submitCrawl(enqueueLinks, items, siteDomain, siteName, siteCode);
      for (const item of items) {
        if (!!item.date) {
          if (isDateAfterAprilFirst(item.date)) { // 检查时间字段
            logger.info(`${siteCode}: [time check passed]: ${item.date}, ${item.title}`);

            const baseUrl = new URL(item.href).origin + new URL(item.href).pathname;

            logger.info(`${siteCode}: baseUrl=${baseUrl}`);
            item.date = item.date.slice(1, -1);
            await createNewPage(siteDomain, siteName, siteCode, baseUrl, item);
            await enqueueLinks({ 
              urls: [baseUrl], 
              transformRequestFunction(req) { 
                logger.info(`>>> ${siteCode}: reqUrl=${req.url}`);
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
    } else if (request.url.indexOf('search.do?formAction=pqfGgtz') > -1 
      || request.url.indexOf('search.do?formAction=pqfJgtz') > -1
      || request.url.indexOf('search.do?formAction=pqfCyl') > -1
    ) {
      console.log('[check search.do]:' + request.url);
      await page.waitForSelector('table tr td[align="left"]');
      
      // 提取法规文件列表
      const items = await page.$$eval('table tr td[align="left"]', (elements) => {
        return elements.map((el) => {
            const title = el.querySelector('a font')?.innerText.trim();
            const href = el.querySelector('a')?.href;
            const dateRegex = /[(（](\d{4}[-年]\d{1,2}[-月]\d{1,2}(?:日)?)[)）]/;
            const match = el.querySelector('a font')?.innerText.match(dateRegex);
            const date = match ? match[1] : null;
            console.log(`>>>>>找到时间:${date}`);
            const parentUrl = window.location.href;
            return { title, href, date, parentUrl };
        });
      });
      // console.log(`-----${JSON.stringify(items)}`);
      for (const item of items) {
        if (item.href.indexOf('.pdf') == -1)
          continue;
        if (!!item.date) {
          logger.info(`${siteCode}: [time check passed]: ${item.date}, ${item.title}`);
          await createNewPage(siteDomain, siteName, siteCode, item.href, item);
          await enqueueLinks({ 
              urls: [item.href], 
              transformRequestFunction(req) { 
                logger.info(`>>> ${siteCode}: reqUrl=${req.url}`);
                return req; 
              },
              limit: parseInt(process.env.CRAWL_QUEUE_SIZE || 4)
            });
        } else {
          logger.warn(`${siteCode}: time not valid:${item.date}, href=${item.href}`);
        }
      }
    } else {
      console.log(`------nifdc>>>>>>url=${request.url}`);
      // 准备临时目录
      // await ensureTempDir();
      await handleWeb2Pdf(request, page, siteCode, siteName);
    }
  }
});
