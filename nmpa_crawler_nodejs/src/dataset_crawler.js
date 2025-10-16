
import { PlaywrightCrawler, log as crawlerLog } from 'crawlee';
import fs from 'fs';
import fsExtra from 'fs-extra';
import path from 'path';
import os from 'os';
import { once } from 'events';
import { fileURLToPath } from 'url';

const SEARCH_URL = 'https://www.nmpa.gov.cn/datasearch/search-result.html';
const OUTPUT_ROOT = path.resolve('outputs/datasets');
const DETAIL_CONCURRENCY = 4;
const PAGE_LOG_INTERVAL = 50;
const PLAYWRIGHT_ARGS = ['--no-sandbox', '--disable-setuid-sandbox', '--headless=new'];

const DOMESTIC_ITEM_ID = 'ff80808183cad75001840881f848179f';
const IMPORTED_ITEM_ID = 'ff80808183cad7500184088665711800';

crawlerLog.setLevel(crawlerLog.LEVELS.INFO);

function resolveChromiumExecutable() {
    const explicit = process.env.PLAYWRIGHT_CHROMIUM_EXEC;
    const candidates = [
        explicit,
        path.join(os.homedir(), '.cache/ms-playwright/chromium-1140/chrome-linux/chrome'),
        path.join(os.homedir(), '.cache/ms-playwright/chromium-1187/chrome-linux/chrome'),
        path.join(os.homedir(), '.cache/ms-playwright/chromium-1194/chrome-linux/chrome'),
    ];

    for (const candidate of candidates) {
        if (candidate && fs.existsSync(candidate)) {
            return candidate;
        }
    }
    return undefined;
}

async function writeJsonLine(stream, data) {
    const json = JSON.stringify(data, (_, value) => (value === null ? '' : value ?? ''));
    const line = `${json}\n`;
    if (!stream.write(line, 'utf8')) {
        await once(stream, 'drain');
    }
}

async function fetchListPage(page, { itemId, searchValue, pageNum }) {
    const response = await page.evaluate(async (params) => {
        window.getUrl = window.getUrl || (() => '');
        const raw = await window.pajax.hasTokenGet(window.api.queryList, {
            itemId: params.itemId,
            isSenior: 'N',
            searchValue: params.searchValue,
            pageNum: params.pageNum,
            pageSize: 20,
        });
        return raw;
    }, { itemId, searchValue, pageNum });

    const payload = response?.data?.data;
    if (!payload || !Array.isArray(payload.list)) {
        const message = response?.message || response?.data?.message || 'unknown response';
        throw new Error(`无法获取列表数据: ${message}`);
    }
    return payload;
}

async function fetchDetailsBatch(page, itemId, recordIds, concurrency = DETAIL_CONCURRENCY) {
    if (recordIds.length === 0) return [];

    const results = await page.evaluate(async (params) => {
        window.getUrl = window.getUrl || (() => '');
        const { itemId, recordIds, concurrency } = params;
        const output = new Array(recordIds.length);
        let index = 0;

        async function worker() {
            while (index < recordIds.length) {
                const current = index++;
                const id = recordIds[current];
                try {
                    const raw = await window.pajax.hasTokenGet(window.api.queryDetail, {
                        id,
                        itemId,
                        isSenior: 'N',
                    });
                    const detail = raw?.data?.data?.detail;
                    output[current] = { id, success: !!detail, detail, message: raw?.message };
                } catch (error) {
                    output[current] = { id, success: false, error: error?.message || String(error) };
                }
            }
        }

        const workerCount = Math.min(concurrency, recordIds.length);
        await Promise.all(Array.from({ length: workerCount }, () => worker()));
        return output;
    }, { itemId, recordIds, concurrency });

    return results;
}

async function fetchDetailWithRetry(page, itemId, id, retries = 2) {
    for (let attempt = 0; attempt <= retries; attempt++) {
        try {
            const result = await page.evaluate(async (params) => {
                window.getUrl = window.getUrl || (() => '');
                const raw = await window.pajax.hasTokenGet(window.api.queryDetail, {
                    id: params.id,
                    itemId: params.itemId,
                    isSenior: 'N',
                });
                return raw?.data?.data?.detail || null;
            }, { itemId, id });

            if (result) {
                return result;
            }
        } catch (error) {
            if (attempt === retries) {
                throw error;
            }
        }
        await new Promise((resolve) => setTimeout(resolve, 800 * (attempt + 1)));
    }
    return null;
}

async function crawlDomesticCategory(page, { searchValue, prefix, outputName }, logger) {
    await fsExtra.ensureDir(OUTPUT_ROOT);
    const outputPath = path.join(OUTPUT_ROOT, outputName);
    const stream = fs.createWriteStream(outputPath, { flags: 'w', encoding: 'utf8' });
    let totalWritten = 0;

    try {
        let pageNum = 1;
        let totalPages = null;
        let totalRecords = null;

        while (true) {
            const payload = await fetchListPage(page, { itemId: DOMESTIC_ITEM_ID, searchValue, pageNum });
            if (totalPages === null) {
                totalRecords = payload.total;
                totalPages = Math.ceil((payload.total || 0) / (payload.pageSize || 20));
                logger.info(`${outputName}: 计划抓取 ${totalRecords} 条数据，共 ${totalPages} 页`);
            }

            const records = payload.list || [];
            if (records.length === 0) {
                break;
            }

            const ids = records.map((item) => item.f4).filter(Boolean);
            const batchDetails = await fetchDetailsBatch(page, DOMESTIC_ITEM_ID, ids);

            for (let index = 0; index < ids.length; index++) {
                const id = ids[index];
                let detailEntry = batchDetails[index];
                if (!detailEntry || !detailEntry.success || !detailEntry.detail) {
                    try {
                        const recovered = await fetchDetailWithRetry(page, DOMESTIC_ITEM_ID, id);
                        if (!recovered) {
                            logger.warning(`${outputName}: 无法获取记录 ${id} 详情，已跳过`);
                            continue;
                        }
                        detailEntry = { detail: recovered, success: true };
                    } catch (error) {
                        logger.warning(`${outputName}: 重试记录 ${id} 详情失败: ${error.message}`);
                        continue;
                    }
                }

                const detail = detailEntry.detail;
                if (!detail?.f0 || !detail.f0.startsWith(prefix)) {
                    continue;
                }

                const record = {
                    code: detail.f0 || '',
                    zh: detail.f1 || '',
                    en: detail.f2 || '',
                };

                await writeJsonLine(stream, record);
                totalWritten += 1;
            }

            if (pageNum % PAGE_LOG_INTERVAL === 0 || pageNum === totalPages) {
                logger.info(`${outputName}: 已完成第 ${pageNum}/${totalPages} 页，累计写入 ${totalWritten} 条`);
            }

            pageNum += 1;
            if (totalPages && pageNum > totalPages) {
                break;
            }
        }
    } finally {
        stream.end();
        await once(stream, 'finish');
        logger.info(`${outputName}: 写入完成，共 ${totalWritten} 条 => ${path.relative(process.cwd(), path.join(OUTPUT_ROOT, outputName))}`);
    }
}

async function crawlImported(page, logger) {
    await fsExtra.ensureDir(OUTPUT_ROOT);
    const outputPathH = path.join(OUTPUT_ROOT, '进口H.jsonl');
    const outputPathS = path.join(OUTPUT_ROOT, '进口S.jsonl');
    const streamH = fs.createWriteStream(outputPathH, { flags: 'w', encoding: 'utf8' });
    const streamS = fs.createWriteStream(outputPathS, { flags: 'w', encoding: 'utf8' });

    let totalPages = null;
    let totalRecords = null;
    let pageNum = 1;
    let writtenH = 0;
    let writtenS = 0;

    try {
        while (true) {
            const payload = await fetchListPage(page, { itemId: IMPORTED_ITEM_ID, searchValue: '国药准字', pageNum });
            if (totalPages === null) {
                totalRecords = payload.total;
                totalPages = Math.ceil((payload.total || 0) / (payload.pageSize || 20));
                logger.info(`进口药品: 计划抓取 ${totalRecords} 条数据，共 ${totalPages} 页`);
            }

            const records = payload.list || [];
            if (records.length === 0) {
                break;
            }

            const ids = records.map((item) => item.f3).filter(Boolean);
            const batchDetails = await fetchDetailsBatch(page, IMPORTED_ITEM_ID, ids, 3);

            for (let index = 0; index < ids.length; index++) {
                const id = ids[index];
                let detailEntry = batchDetails[index];
                if (!detailEntry || !detailEntry.success || !detailEntry.detail) {
                    try {
                        const recovered = await fetchDetailWithRetry(page, IMPORTED_ITEM_ID, id);
                        if (!recovered) {
                            logger.warning(`进口药品: 无法获取记录 ${id} 详情，已跳过`);
                            continue;
                        }
                        detailEntry = { detail: recovered, success: true };
                    } catch (error) {
                        logger.warning(`进口药品: 重试记录 ${id} 详情失败: ${error.message}`);
                        continue;
                    }
                }

                const detail = detailEntry.detail;
                const registration = detail?.f1 || detail?.f0 || '';
                if (!registration) {
                    continue;
                }

                const baseRecord = {
                    code: registration,
                    product_zh: detail?.f14 || '',
                    product_en: detail?.f15 || '',
                    commodity_zh: detail?.f16 || '',
                    commodity_en: detail?.f17 || '',
                };

                if (registration.startsWith('H')) {
                    await writeJsonLine(streamH, baseRecord);
                    writtenH += 1;
                } else if (registration.startsWith('S')) {
                    await writeJsonLine(streamS, baseRecord);
                    writtenS += 1;
                }
            }

            if (pageNum % PAGE_LOG_INTERVAL === 0 || pageNum === totalPages) {
                logger.info(`进口药品: 已完成第 ${pageNum}/${totalPages} 页，累计 H=${writtenH}, S=${writtenS}`);
            }

            pageNum += 1;
            if (totalPages && pageNum > totalPages) {
                break;
            }
        }
    } finally {
        streamH.end();
        streamS.end();
        await Promise.all([once(streamH, 'finish'), once(streamS, 'finish')]);
        logger.info(`进口药品: 写入完成，H=${writtenH} (${path.relative(process.cwd(), outputPathH)}), S=${writtenS} (${path.relative(process.cwd(), outputPathS)})`);
    }
}

async function handleDatasetRequest(page, datasetKey, logger = crawlerLog) {
    await page.goto(SEARCH_URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForFunction(() => window.api && window.pajax && window.itemFileUrl, { timeout: 60000 });

    if (datasetKey === 'domestic-h') {
        await crawlDomesticCategory(page, { searchValue: '国药准字H', prefix: '国药准字H', outputName: '国内H.jsonl' }, logger);
    } else if (datasetKey === 'domestic-s') {
        await crawlDomesticCategory(page, { searchValue: '国药准字S', prefix: '国药准字S', outputName: '国内S.jsonl' }, logger);
    } else if (datasetKey === 'imported') {
        await crawlImported(page, logger);
    } else {
        throw new Error(`未知的数据集标识: ${datasetKey}`);
    }
}

async function runDatasetCrawler(options = {}) {
    const executablePath = resolveChromiumExecutable();
    if (!executablePath) {
        crawlerLog.warning('未找到 Playwright Chromium 缓存，尝试使用默认浏览器配置。');
    } else {
        crawlerLog.info(`使用 Chromium 可执行文件: ${executablePath}`);
    }

    const datasetKeys = options.datasets ?? ['domestic-h', 'domestic-s', 'imported'];

    const crawler = new PlaywrightCrawler({
        headless: true,
        maxConcurrency: 1,
        requestHandlerTimeoutSecs: 7200,
        navigationTimeoutSecs: 120,
        maxRequestsPerCrawl: 3,
        launchContext: {
            launchOptions: {
                executablePath,
                args: PLAYWRIGHT_ARGS,
            },
        },
        preNavigationHooks: [
            async ({ page }) => {
                await page.addInitScript(() => {
                    window.getUrl = window.getUrl || (() => '');
                });
            },
        ],
        requestHandler: async ({ page, request, log: requestLog }) => {
            const datasetKey = request.userData.datasetKey;
            const logger = requestLog ?? crawlerLog;
            await handleDatasetRequest(page, datasetKey, logger);
        },
    });

    const requests = datasetKeys.map((datasetKey) => ({
        url: SEARCH_URL,
        userData: { datasetKey },
    }));

    await crawler.addRequests(requests);

    await crawler.run();
    crawlerLog.info('全部数据集抓取完成。');
}

const invokedPath = process.argv[1] ? path.resolve(process.argv[1]) : null;
const isDirectRun = invokedPath && fileURLToPath(import.meta.url) === invokedPath;

export { runDatasetCrawler };

if (isDirectRun) {
    runDatasetCrawler().catch((error) => {
        crawlerLog.error(`抓取失败: ${error.stack || error.message}`);
        process.exitCode = 1;
    });
}
