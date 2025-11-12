import { chromium } from "playwright";

const SEARCH_URL = "https://www.nmpa.gov.cn/datasearch/search-result.html";
const DOMESTIC_ITEM_ID = "ff80808183cad75001840881f848179f";
const DEFAULT_CHROMIUM = "/home/langchao6/.cache/ms-playwright/chromium-1140/chrome-linux/chrome";

(async () => {
  const proxy = process.env.NMPA_PROXY ? { server: process.env.NMPA_PROXY } : undefined;
  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXEC || DEFAULT_CHROMIUM;
  const browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--headless=new"],
    proxy,
    executablePath,
  });

  try {
    const page = await browser.newPage();
    await page.goto(SEARCH_URL, { waitUntil: "domcontentloaded", timeout: 120000 });
    await page.waitForFunction(() => window.api && window.pajax && window.itemFileUrl, { timeout: 120000 });

    const response = await page.evaluate(async () => {
      window.getUrl = window.getUrl || (() => "");
      const raw = await window.pajax.hasTokenGet(window.api.queryList, {
        itemId: "ff80808183cad75001840881f848179f",
        isSenior: "N",
        searchValue: "国药准字H",
        pageNum: 1,
        pageSize: 20,
      });
      return raw;
    });

    console.log(JSON.stringify(response, null, 2));
  } catch (error) {
    console.error("抓取失败:", error);
  } finally {
    await browser.close();
  }
})();
