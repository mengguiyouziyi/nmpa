import dotenv from 'dotenv';
dotenv.config();

/**
 * 过滤URL，决定是否应该抓取
 * @param {string} url 
 * @param {Set} visitedUrls 
 */
export const shouldCrawlUrl = (url, visitedUrls) => {
  try {
    // 跳过已访问的URL
    if (visitedUrls.has(url)) return false;
    
    const parsedUrl = new URL(url);
    
    // 限制域名（如果配置了DOMAIN_RESTRICTION）
    if (process.env.DOMAIN_RESTRICTION && 
        !parsedUrl.hostname.includes(process.env.DOMAIN_RESTRICTION)) {
      return false;
    }
    
    // 跳过非HTTP(S)协议
    if (!['http:', 'https:'].includes(parsedUrl.protocol)) return false;
    
    // 跳过常见静态文件
    const excludedExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.zip'];//.pdf
    if (excludedExtensions.some(ext => parsedUrl.pathname.endsWith(ext))) {
      return false;
    }
    
    return true;
  } catch {
    return false;
  }
};

export const isDateAfterAprilFirst = (dateStr) => {
  // 去掉两边括号
  const cleanDateStr = dateStr.slice(1, -1);

  // 将字符串转换成Date对象
  const inputDate = new Date(cleanDateStr);

  // 验证日期是否有效
  if (isNaN(inputDate)) {
    throw new Error("无效的日期格式");
  }

  // 构造基准日期 4月15日，年份取输入日期的年份
  const year = inputDate.getFullYear();
  const baseDate = new Date(`2025-04-01`);

  // 比较日期大小
  return inputDate > baseDate;
};