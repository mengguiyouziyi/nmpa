import { query, queryIdByPageUrl, queryEntityByPageUrl, queryEntitiesByStatus, insertPage, updatePage, updatePage2Synced } from '../services/database.js';

export class WebPage {
  /**
   * 创建或更新网页记录
   * @param {string} domain 域名
   * @param {string} title 网页标题
   * @param {string} pdfPath PDF文件路径
   */
  static async save(webPage) {
    return await insertPage(webPage);
  }

  /**
   * 获取所有记录
   */
  static async findAll() {
    return await query('SELECT * FROM spider_site_info ORDER BY created_at DESC');
  }

  /**
   * 根据页面url查询记录id
   * @param {String} pageUrl 
   * @returns 
   */
  static async getIdByPageUrl(pageUrl) {
    return await queryIdByPageUrl(pageUrl);
  }

  /**
   * 根据pageUrl找到整条spider记录
   * @param {String} pageUrl 
   * @returns 
   */
  static async getEntityByPageUrl(pageUrl) {
    return await queryEntityByPageUrl(pageUrl);
  }

  /**
   * 返回需要同步到ragflow的
   * @returns 
   */
  static async queryEntitiesPendingSync() {
    return await queryEntitiesByStatus('DONE');
  }

  /**
   * 更新webpage
   * @param {object} webPage 
   * @returns 
   */
  static async updatePage(webPage) {
    return await updatePage(webPage);
  }

  /**
   * 批量更新status至已同步，并且更新update time
   * @param {Array} ids 
   * @returns 
   */
  static async updatePage2Synced(ids) {
    return await updatePage2Synced(ids);
  }

}