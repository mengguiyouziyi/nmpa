import { PuppeteerCrawler } from 'crawlee';
import { extractDomain } from '../services/storage.js';
import { WebPage } from '../models/WebPage.js';
import { ensureTempDir } from '../utils/fileHandler.js';
import { uploadToOSS } from '../utils/ossClient.js';
import path from 'path';

/**
 * 将网页保存为PDF并上传OSS
 */
export const page2PdfCrawler = new PuppeteerCrawler({
  async requestHandler({ request, page }) {
    console.log(`Processing URL: ${request.url}`);
    
    // 准备临时目录
    await ensureTempDir();

    // 等待关键元素加载
    await page.waitForSelector('body', { timeout: 10000 });
    
    // 移除干扰元素
    await page.evaluate(() => {
      const elements = document.querySelectorAll('.ad, .popup');
      elements.forEach(el => el.remove());
    });
    
    // 生成PDF文件名
    const siteDomain = extractDomain(request.url);
    const siteName = "国家药品监督管理局药品审评检查大湾区分中心";
    const siteCode = "";
    const pageUrl = request.url;
    const pageType = "PAGE"; // FILE
    const pageTitle = await page.title();
    const pageContent = await page.content();
    const pdfName = pageTitle + ".pdf";
    const localPdfPath = path.join('./temp_pdfs', pdfName);
    const ossKey = `spider/${pdfName}`;
    const extra = {
      fileKey: ossKey,
      filename: pdfName
    };
    
    try {
      // 调整页面设置
      await page.setViewport({ width: 1920, height: 1080 });
      
      // 生成PDF
      await page.pdf({
        path: localPdfPath,
        format: 'A4',
        printBackground: true,
        fullPage: true,
        margin: {
          top: '4mm',
          right: '4mm',
          bottom: '4mm',
          left: '4mm'
        }
      });
      
      console.log(`PDF saved locally: ${localPdfPath}`);
      
      // 上传到OSS
      await uploadToOSS(localPdfPath, ossKey);

      // 保存记录到数据库
      await WebPage.save(siteDomain, siteName, siteCode, pageUrl, pageType, pageTitle, pageContent, JSON.stringify(extra));
      console.log(`WebPage saved to mysql`);

    } catch (error) {
      console.error(`Failed to process ${request.url}:`, error);
    }
  },
  
  // 浏览器配置
  launchContext: {
    launchOptions: {
      headless: 'new',
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage'
      ]
    }
  },
  
  // 爬取配置
  maxConcurrency: 2,
  navigationTimeoutSecs: 60
});