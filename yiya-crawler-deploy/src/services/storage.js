import { promises as fs } from 'fs';
import dotenv from 'dotenv';

dotenv.config();

const STORAGE_PATH = process.env.PDF_STORAGE_PATH || './storage/pdfs';

/**
 * 确保存储目录存在
 */
export const ensureStorageDir = async () => {
  try {
    await fs.access(STORAGE_PATH);
  } catch {
    await fs.mkdir(STORAGE_PATH, { recursive: true });
  }
};

/**
 * 生成PDF文件名
 * @param {string} url 网页URL
 */
export const generatePdfName = (url) => {
  const timestamp = Date.now();
  const domain = new URL(url).hostname.replace(/\./g, '_');
  return `${domain}_${timestamp}.pdf`;
};

/**
 * 提取域名
 * @param {string} url 
 */
export const extractDomain = (url) => {
  return new URL(url).hostname;
};