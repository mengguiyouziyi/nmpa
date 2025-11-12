import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config();

const pool = mysql.createPool({
  host: process.env.MYSQL_HOST,
  user: process.env.MYSQL_USER,
  password: process.env.MYSQL_PASSWORD,
  database: process.env.MYSQL_DATABASE,
  port: process.env.MYSQL_PORT || 3306,
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
});

// 执行SQL查询
export const query = async (sql, params) => {
  const [rows] = await pool.query(sql, params);
  return rows;
};

export const queryIdByPageUrl = async (pageUrl) => {
  const [rows] = await pool.query(
    `SELECT id FROM spider_site_info WHERE delete_flag='N' and page_url = ?`,
    [pageUrl]
  );
  return rows.length > 0 ? rows[0].id : null;
};

export const queryEntityByPageUrl = async (pageUrl) => {
  const [rows] = await pool.query(
    `SELECT * FROM spider_site_info WHERE delete_flag='N' and page_url = ?`,
    [pageUrl]
  );
  return rows.length > 0 ? rows[0] : null;
};

export const queryEntitiesByStatus = async (pageUrl) => {
  const [rows] = await pool.query(
    `SELECT * FROM spider_site_info WHERE delete_flag='N' and status = ?`,
    [pageUrl]
  );
  return rows;
};

export const insertPage = async (webPage) => {
  const [result] = await pool.execute(
    `INSERT INTO spider_site_info (parent_id, site_domain, site_name, site_code, page_url, page_type, page_title, page_content, extra, created_time, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON DUPLICATE KEY UPDATE
        page_title = VALUES(page_title)`,
      [webPage.parentId, webPage.siteDomain, webPage.siteName, webPage.siteCode, webPage.pageUrl, webPage.pageType, webPage.pageTitle, webPage.pageContent, webPage.extra, new Date(), webPage.status]
  );
  return result.insertId;

};

export const updatePage = async (webPage) => {
  const [result] = await pool.execute(
    `UPDATE spider_site_info set extra=?, updated_time=?, status=?, page_type=? 
    WHERE id=? and delete_flag='N'`,
      [webPage.extra, new Date(), webPage.status, webPage.pageType, webPage.id]
  );
  return result.insertId;
};

export const updatePage2Synced = async (ids) => {
  const [result] = await pool.query(`UPDATE spider_site_info SET status='SYNCED' WHERE delete_flag='N' AND id IN (?)`, [ids]);
  console.log('changed results:', result);
  return result;
};