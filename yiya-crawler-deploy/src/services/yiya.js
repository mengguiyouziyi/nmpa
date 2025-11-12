import dotenv from 'dotenv';
import axios from 'axios';
import { WebPage } from '../models/WebPage.js';
import { logger } from '../utils/logger.js';

dotenv.config();

/**
 * 写入ragflow 创建知识库的job
 * @param {*} ids 
 * @returns 
 */
export const createYiyaJob = async (ids) => {
  if (ids.length == 0) {
    return 0;
  }
  logger.info(`createYiyaJob ids:${ids}`);
  axios.post(`https://${process.env.YIYA_API_HOST}/release/v1/openapi/llm-tools/search/spider/push`, {ids: ids}, {
    headers: {
      'Authorization': `Bearer ${process.env.YIYA_OPENAI_KEY}`,
      'Content-Type': 'application/json'
    }
  })
  .then((response) => {
    logger.info(`createYiyaJob success(${ids}):`, response.data);
  })
  .catch((error) => {
    logger.error(`failed to createYiyaJob(${ids}):`, error);
  });
}

/**
 * 批量创建schedule job，即创建ragflow知识库
 */
export const batchCreateYiyaJobs = async() => {
  let pendingPages = await WebPage.queryEntitiesPendingSync();
  const ids = pendingPages.map(item => item.id);
  logger.info(`ids:${ids}`);
  if (ids && ids.length > 0) {
    await createYiyaJob(ids);
    await WebPage.updatePage2Synced(ids);
  } else {
    logger.warn('ids为空');
  }
}