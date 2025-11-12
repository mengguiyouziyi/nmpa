// import fs from 'fs/promises';
import path from 'path';
import { extractDomain } from '../services/storage.js';
import { createYiyaJob } from '../services/yiya.js';
import { uploadToOSS } from '../utils/ossClient.js';
import { WebPage } from '../models/WebPage.js';
import { logger } from '../utils/logger.js';
import { SPIDER_SITE_TYPE } from '../config/constants.js';
import fs from 'fs';
import { pipeline } from 'stream';
import { promisify } from 'util';
import got from 'got';

// 临时PDF存储目录
const TEMP_DIR = 'downloads';
const ATTACHMENT_DIR = 'downloads/attachments';
const streamPipeline = promisify(pipeline);

/**
 * 确保目录存在
 * @param {string} dirPath 目录路径
 */
export const ensureDir = async (dirPath) => {
  try {
    await fs.access(dirPath);
  } catch {
    await fs.mkdir(dirPath, { recursive: true });
  }
};

/**
 * 生成唯一的文件名
 * @param {string} url 文件URL
 * @param {string} ext 文件扩展名
 */
export const generateUniqueName = (url, ext = 'pdf') => {
  const timestamp = Date.now();
  const urlHash = Buffer.from(url).toString('base64').slice(0, 10);
  return `${timestamp}_${urlHash}.${ext}`;
};


/**
 * 生成唯一文件名
 * @param {string} url 网页URL
 */
export const generatePdfName = (url) => {
  const timestamp = Date.now();
  const hostname = new URL(url).hostname;
  return `${hostname}_${timestamp}.pdf`;
};

/**
 * 清理临时文件
 */
export const cleanupTempFiles = async () => {
  try {
    await fs.rm(TEMP_DIR, { recursive: true, force: true });
    console.log('Temporary files cleaned up');
  } catch (error) {
    console.error('Failed to clean temp files:', error);
  }
};

/**
 * 下载pdf，oss上传，mysql插入，发起ragflow schedule job
 */
export const handleWeb2Pdf = async (request, page, siteCode, siteName) => {
  logger.info(`-----${siteCode}: start to handleWebPage ${request.url}-----`)
  // 获取网页基本信息
  const siteDomain = extractDomain(request.url);
  const pageUrl = request.url;
  // const pageContent = await page.content();
  
  if (pageUrl.indexOf('.pdf') > -1  // nifdc特殊页面, 仅保存页面的pdf
  && (pageUrl.indexOf('search.do?formAction=openUrl') > -1 || pageUrl.indexOf('pqf/file_path/help/') > -1)) {
    
    const existingRecord = await WebPage.getEntityByPageUrl(pageUrl);
    if (!!existingRecord && existingRecord != null) {
      const downloadDir = path.resolve(ATTACHMENT_DIR);
      logger.debug(`${JSON.stringify(existingRecord)}`);
      fs.mkdirSync(downloadDir, { recursive: true });
      const attachmentInfo = await saveAttachementFile(pageUrl, existingRecord.page_title + ".pdf", downloadDir, null, siteDomain, siteName, siteCode);
    logger.info(`finish attach download1-`);

      let extra = existingRecord.extra;
      extra.fileKey = attachmentInfo.ossKey;
      extra.filename = attachmentInfo.fileName;

      const webPage = {
        id: existingRecord.id,
        pageContent: null,
        pageType: 'FILE',
        extra: JSON.stringify(extra),
        status: 'DONE'
      };
      await WebPage.updatePage(webPage)
      logger.info(`${siteCode} WebPage updated, pageId=${existingRecord.id}`);

      // API发起ragflow写入任务
      // if (ids.length > 0) {
        // await createYiyaJob([existingRecord.id]);
      // }
    }
  } else { // 常规叶子页面的爬取，并保存
    // logger.info(`>>>>${siteCode}--1: im visiting page now! title=${pageTitle}, url=${pageUrl}`);
    await page.waitForSelector('h2');
    // logger.info(`>>>>${siteCode}: im visiting page now! title=${pageTitle}, url=${pageUrl}`);
    
    const pageTitle = await page.title();
    const pageType = SPIDER_SITE_TYPE.page;
    const pdfName = sanitizeFilename(pageTitle) + ".pdf";
    const localPdfPath = path.join(TEMP_DIR, pdfName);
    const ossKey = `${process.env.OSS_SUBDIR || 'spider'}/${pdfName}`;
      
    // 检查该页面是否已经导入数据库，是、则退出
    let pageId;
    let needUpdate = true;
    const existingRecord = await WebPage.getEntityByPageUrl(pageUrl);
    logger.info(`${siteCode}: existingRecord=${existingRecord.id}`);
    if (!!existingRecord || null != existingRecord) {
      pageId = existingRecord.id;
      if (existingRecord.status == 'NEW') {
        logger.info(`${siteCode}: this is a new page-00000, ${pageUrl}`);
      } else {
        logger.info(`${siteCode}: this page has alreay been imported before, pageId=${existingRecord.id}`);
        return;
      }
    } else {
      needUpdate = false;
      logger.info(`${siteCode}: this is a new page, ${pageUrl}`)
    }

    logger.debug("start to save page into pdf");
    
    // 开始下载流程
    try {
      await convertPageToLocalPdf(page, localPdfPath);
      logger.info(`${siteCode} WebPage PDF saved locally: ${localPdfPath}`);
      
      // 上传到OSS
      await uploadToOSS(localPdfPath, ossKey);

      if (needUpdate) {
        let extra = existingRecord.extra;
        extra.fileKey = ossKey;
        extra.filename = pdfName;

        const pageMetaNameEle = await page.$('meta[name="ColumnName"]');
        if (pageMetaNameEle) {
          extra.pageMetaName = page.$eval('meta[name="ColumnName"]', (el) => el.content);
        }
        const pageMetaDescriptionEle = await page.$('meta[name="ColumnDescription"]');
        if (pageMetaDescriptionEle) {
          extra.pageMetaDescription = page.$eval('meta[name="ColumnDescription"]', (el) => el.content);
        }

        logger.info(`updatePage: pageId: ${pageId}, extra: ${extra}`);

        const webPage = {
          id: pageId,
          pageContent: null,
          extra: JSON.stringify(extra),
          pageType: 'PAGE',
          status: 'DONE'
        };
        await WebPage.updatePage(webPage)
        logger.info(`${siteCode} WebPage updated, pageId=${pageId}`);
      } else { //insert
        let extra = {
          fileKey: ossKey,
          filename: pdfName
        };

        const pageMetaNameEle = await page.$('meta[name="ColumnName"]');
        if (pageMetaNameEle) {
          extra.pageMetaName = page.$eval('meta[name="ColumnName"]', (el) => el.content);
        }
        const pageMetaDescriptionEle = await page.$('meta[name="ColumnDescription"]');
        if (pageMetaDescriptionEle) {
          extra.pageMetaDescription = page.$eval('meta[name="ColumnDescription"]', (el) => el.content);
        }
        // 保存记录到数据库
        const webPage = {
          siteDomain: siteDomain, 
          siteName: siteName, 
          siteCode: siteCode, 
          pageUrl: pageUrl, 
          pageType: pageType, 
          pageTitle: pageTitle, 
          pageContent: null, 
          extra: JSON.stringify(extra),
          parentId: null,
          status: 'DONE'
        };
        pageId = await WebPage.save(webPage);
        logger.info(`${siteCode} WebPage saved to mysql, pageId=${pageId}`);
      }
      
      let ids = await attachmentCrawler(request, page, pageId, siteDomain, siteName, siteCode);
      // ids = attachmentIds;
      ids.concat(pageId);

      // API发起ragflow写入任务
      // if (ids.length > 0) {
      //   await createYiyaJob(ids);
      // }
  
    } catch (error) {
      logger.error(`Failed to process ${request.url}:`, error);
    }
  }
}

/**
 * 处理文件名中包含特殊字符，例如斜杠
 * @param {*} filename 
 * @returns 
 */
function sanitizeFilename(filename) {
  return filename.replace(/[\\/:*?"<>|.]/g, '_');
}

export const createNewPage = async (siteDomain, siteName, siteCode, pageUrl, dataItem) => {
  // 检查该页面是否已经导入数据库，是、则退出
  const existingPage = await WebPage.getEntityByPageUrl(pageUrl);
  // logger.debug(JSON.stringify(existingPage))
  if (!!existingPage || null != existingPage) {
    if (existingPage.status != 'NEW') {
      logger.info(`${siteCode} - pageUrl=${pageUrl}: it is an existing page, id=${existingPage.id}`);
      return;
    } else {
      logger.info(`${siteCode} - waiting for crawlling: ${pageUrl}`);
    }
  } else {
    logger.info(`createNewPage of ${siteCode}: pageUrl=${pageUrl}`);
    if (existingPage == null) {
      // 保存记录到数据库
      const webPage = {
        siteDomain: siteDomain, 
        siteName: siteName,//SITE_CONFIG.nmpa.name, 
        siteCode: siteCode,//SITE_CONFIG.nmpa.code, 
        pageUrl: pageUrl, 
        pageType: SPIDER_SITE_TYPE.page, 
        pageTitle: dataItem.title, 
        pageContent: null, 
        extra: JSON.stringify({ releaseDate: dataItem.date, href: dataItem.href, title: dataItem.title, parentUrl: dataItem.parentUrl }),
        parentId: null,
        status: 'NEW'
      };
      const pageId = await WebPage.save(webPage);
      logger.info(`done createNewPage of ${siteCode}: pageUrl=${pageUrl}, pageUrl=${pageUrl}, pageId=${pageId}`);
    } else {
      logger.info(`${siteCode} - ${pageUrl} is an exsiting spider page record, but not yet crawled completely`);
    }
  }
}

// 解析页面上的附件
const attachmentCrawler = async (request, page, parentId, siteDomain, siteName, siteCode) => {
  let ids = [];
  const docLinks = await page.$$eval('a', (anchors, baseUrl) => {
    return anchors
      .filter(a => a.href.match(/\.(docx?|pdf|xlsx|xls|doc|ppt)$/i))
      .map(a => ({
        href: new URL(a.href, baseUrl).href,
        text: a.textContent.trim()
      }));
  }, request.loadedUrl);
  
  logger.info(`${siteCode}: parentId(${parentId}) has docLinks: ${docLinks}`);

  if (docLinks.length > 0) {
    logger.info(`${siteCode}: start to download attachments`);
    // 确保下载目录存在
    const downloadDir = path.resolve(ATTACHMENT_DIR);
    fs.mkdirSync(downloadDir, { recursive: true });

    for (const { href, text } of docLinks) {
      try {
        const attachmentInfo = await saveAttachementFile(href, text, downloadDir, request.loadedUrl, parentId, siteDomain, siteName, siteCode);
        logger.info(`finish attach download2-`);
        // 保存附件到mysql
        const attachmentEntity = {
          parentId: parentId,
          siteDomain: siteDomain,
          siteName: siteName,
          siteCode: siteCode,
          pageUrl: href,
          pageType: SPIDER_SITE_TYPE.file,
          pageTitle: attachmentInfo.fileName,
          pageContent: null,
          extra: JSON.stringify({
            fileKey: attachmentInfo.ossKey,
            filename: attachmentInfo.fileName
          }),
          status: 'DONE'
        };
        logger.info(`New attachment: ${attachmentEntity} of parentId(${parentId})`);
        const fileId = await WebPage.save(attachmentEntity);

        logger.info(`Attachment(parentId=${parentId}, attachmentId=${fileId}) saved to mysql`);
        // return fileId;
        ids.push(fileId);
      } catch (error) {
        logger.error(`下载失败：${href}，错误信息：${error.message}`);
      }
    }
  }
  return ids;
}

const saveAttachementFile = async (href, text, downloadDir, reqUrl, parentId, siteDomain, siteName, siteCode) => {
  const url = reqUrl != null ? new URL(href, reqUrl).toString() : href;
  const fileName = `${sanitizeFilename(text).split(".")[0]}${path.extname(url)}`;
  const filePath = path.join(downloadDir, fileName);

  logger.info(`正在下载：${url}, filePath:${filePath}`);

  const response = await got.stream(url);
  await streamPipeline(response, fs.createWriteStream(filePath));
  logger.info(`已保存：${filePath}`);

  const ossKey = `spider/attachment/${fileName}`;
  // 上传附件到oss
  await uploadToOSS(filePath, ossKey);

return {fileName, filePath, ossKey}
  
}

const convertPageToLocalPdf = async (page, localPdfPath) => {
  // 调整页面设置
    await page.setViewport({ width: 1920, height: 1080 });
    
    await page.addStyleTag({
        content: `
            body {
                overflow: visible !important;
                height: auto !important;
            }
            html, body {
                width: 100% !important;
            }
            @media print {
                body {
                    -webkit-print-color-adjust: exact;
                    print-color-adjust: exact;
                }
            }
        `,
    });

    // 生成PDF
    await page.pdf({
      path: localPdfPath,
      format: 'A2',
      printBackground: true,
      fullPage: true,
      margin: {
        top: '5mm',
        right: '5mm',
        bottom: '5mm',
        left: '5mm'
      }
    });
    
    
}