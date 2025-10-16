import { PlaywrightCrawler, log as crawlerLog } from 'crawlee';
import fs from 'fs';
import fsExtra from 'fs-extra';
import path from 'path';
import os from 'os';
import { once } from 'events';
import { fileURLToPath } from 'url';

const SEARCH_URL = 'https://www.nmpa.gov.cn/datasearch/search-result.html';
const OUTPUT_ROOT = path.resolve('outputs/datasets');

const DOMESTIC_ITEM_ID = 'ff80808183cad75001840881f848179f';
const IMPORTED_ITEM_ID = 'ff80808183cad7500184088665711800';

const DEFAULT_SEGMENT_LIMIT = 9000;
const DEFAULT_SEGMENT_DEPTH = 4;
const SEGMENT_DIGITS = (process.env.NMPA_SEGMENT_DIGITS || '0,1,2,3,4,5,6,7,8,9')
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean);

const DOMESTIC_SEGMENT_LIMIT = parseInt(process.env.NMPA_DOMESTIC_SEGMENT_LIMIT ?? `${DEFAULT_SEGMENT_LIMIT}`, 10);
const DOMESTIC_MAX_SEGMENT_DEPTH = parseInt(process.env.NMPA_DOMESTIC_SEGMENT_DEPTH ?? `${DEFAULT_SEGMENT_DEPTH}`, 10);

const SEGMENT_DELAY_RANGE = createRange(
    parseInt(process.env.NMPA_SEGMENT_DELAY_MIN ?? '1200', 10),
    parseInt(process.env.NMPA_SEGMENT_DELAY_MAX ?? '2800', 10),
);
const SEGMENT_PAUSE_RANGE = createRange(
    parseInt(process.env.NMPA_SEGMENT_PAUSE_MIN ?? '2000', 10),
    parseInt(process.env.NMPA_SEGMENT_PAUSE_MAX ?? '5000', 10),
);
const PAGE_DELAY_RANGE = createRange(
    parseInt(process.env.NMPA_PAGE_DELAY_MIN ?? '450', 10),
    parseInt(process.env.NMPA_PAGE_DELAY_MAX ?? '900', 10),
);
const DETAIL_DELAY_RANGE = createRange(
    parseInt(process.env.NMPA_DETAIL_DELAY_MIN ?? '250', 10),
    parseInt(process.env.NMPA_DETAIL_DELAY_MAX ?? '600', 10),
);
const LIST_DELAY_RANGE = createRange(
    parseInt(process.env.NMPA_LIST_DELAY_MIN ?? '900', 10),
    parseInt(process.env.NMPA_LIST_DELAY_MAX ?? '2000', 10),
);
const RECORD_DELAY_RANGE = createRange(
    parseInt(process.env.NMPA_RECORD_DELAY_MIN ?? '80', 10),
    parseInt(process.env.NMPA_RECORD_DELAY_MAX ?? '180', 10),
);

const LIST_RETRY_LIMIT = parseInt(process.env.NMPA_LIST_RETRY_LIMIT ?? '3', 10);
const DETAIL_RETRY_LIMIT = parseInt(process.env.NMPA_DETAIL_RETRY_LIMIT ?? '2', 10);

crawlerLog.setLevel(crawlerLog.LEVELS.INFO);

function createRange(min, max) {
    const safeMin = Number.isFinite(min) ? Math.max(0, min) : 0;
    const safeMax = Number.isFinite(max) ? Math.max(safeMin, max) : safeMin;
    return { min: safeMin, max: safeMax };
}

const randomBetween = (min, max) => {
    if (!Number.isFinite(min) || !Number.isFinite(max) || max <= min) return Math.max(0, min);
    return Math.floor(Math.random() * (max - min + 1)) + min;
};

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function sleepRange(range) {
    if (!range) return;
    const duration = randomBetween(range.min, range.max);
    if (duration > 0) await sleep(duration);
}

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

function resolveProxySettings() {
    const raw = process.env.NMPA_PROXY || process.env.HTTPS_PROXY || process.env.HTTP_PROXY || process.env.ALL_PROXY;
    if (!raw) return undefined;

    try {
        const hasScheme = /:\/\//.test(raw);
        const parsed = new URL(hasScheme ? raw : `http://${raw}`);
        const username = process.env.NMPA_PROXY_USERNAME || (parsed.username ? decodeURIComponent(parsed.username) : undefined);
        const password = process.env.NMPA_PROXY_PASSWORD || (parsed.password ? decodeURIComponent(parsed.password) : undefined);
        const server = `${parsed.protocol}//${parsed.hostname}${parsed.port ? `:${parsed.port}` : ''}`;
        const proxyOptions = { server };
        if (username) proxyOptions.username = username;
        if (password) proxyOptions.password = password;
        return proxyOptions;
    } catch (error) {
        crawlerLog.warning(`代理地址解析失败: ${error.message}`);
        return undefined;
    }
}

async function writeJsonLine(stream, data) {
    const json = JSON.stringify(data, (_, value) => (value === null ? '' : value ?? ''));
    const line = `${json}
`;
    if (!stream.write(line, 'utf8')) {
        await once(stream, 'drain');
    }
}

async function fetchListPage(page, { itemId, searchValue, pageNum }, attempt = 0) {
    await sleepRange(LIST_DELAY_RANGE);
    const result = await page.evaluate(async (params) => {
        try {
            const raw = await window.pajax.hasTokenGet(window.api.queryList, {
                itemId: params.itemId,
                isSenior: 'N',
                searchValue: params.searchValue,
                pageNum: params.pageNum,
                pageSize: 20,
            });
            return { ok: true, payload: raw };
        } catch (error) {
            return { ok: false, message: error?.message || String(error) };
        }
    }, { itemId, searchValue, pageNum });

    if (!result.ok) {
        if (attempt + 1 >= LIST_RETRY_LIMIT) {
            throw new Error(result.message || '无法获取列表数据');
        }
        const delay = randomBetween(1500, 3000) * (attempt + 1);
        crawlerLog.warning(`列表请求失败(${attempt + 1}/${LIST_RETRY_LIMIT})，${result.message || '未知错误'}，${delay}ms 后重试`);
        await sleep(delay);
        return fetchListPage(page, { itemId, searchValue, pageNum }, attempt + 1);
    }

    const payload = result.payload?.data;
    if (!payload || !Array.isArray(payload.list)) {
        const message = result.payload?.message || '返回数据缺失 list 字段';
        throw new Error(`无法获取列表数据: ${message}`);
    }

    return {
        searchValue,
        pageNum,
        pageSize: payload.pageSize || (payload.list?.length ?? 20),
        total: payload.total || 0,
        list: payload.list,
    };
}

async function fetchDetailsBatch(page, itemId, recordIds, concurrency = 3) {
    if (recordIds.length === 0) return [];

    return page.evaluate(async (params) => {
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
                    const detail = raw?.data?.detail;
                    output[current] = { id, success: !!detail, detail, message: raw?.message };
                } catch (error) {
                    output[current] = { id, success: false, error: error?.message || String(error) };
                }
            }
        }

        const workers = [];
        const limit = Math.min(concurrency, recordIds.length);
        for (let i = 0; i < limit; i++) workers.push(worker());
        await Promise.all(workers);
        return output;
    }, { itemId, recordIds, concurrency });
}

async function fetchDetailWithRetry(page, itemId, id, retries = DETAIL_RETRY_LIMIT) {
    for (let attempt = 0; attempt <= retries; attempt++) {
        try {
            await sleepRange(DETAIL_DELAY_RANGE);
            const payload = await page.evaluate(async (params) => {
                try {
                    const raw = await window.pajax.hasTokenGet(window.api.queryDetail, {
                        id: params.id,
                        itemId: params.itemId,
                        isSenior: 'N',
                    });
                    return { ok: true, detail: raw?.data?.detail || null };
                } catch (error) {
                    return { ok: false, message: error?.message || String(error) };
                }
            }, { itemId, id });

            if (payload.ok && payload.detail) {
                return payload.detail;
            }
            throw new Error(payload.message || '未知错误');
        } catch (error) {
            if (attempt === retries) throw error;
            const delay = randomBetween(1200, 2500) * (attempt + 1);
            crawlerLog.warning(`详情重试 ${id} (${attempt + 1}/${retries}) 失败: ${error.message}，${delay}ms 后重试`);
            await sleep(delay);
        }
    }
    return null;
}

async function collectDomesticSegments(page, baseSearch, logger) {
    const segments = [];
    const visited = new Set();

    async function split(searchValue, depth) {
        if (visited.has(searchValue)) return;
        visited.add(searchValue);

        await sleepRange(SEGMENT_DELAY_RANGE);
        const payload = await fetchListPage(page, { itemId: DOMESTIC_ITEM_ID, searchValue, pageNum: 1 });
        const { total, pageSize } = payload;
        if (!total) {
            logger.info(`${searchValue}: 无数据，跳过`);
            return;
        }

        const totalPages = Math.ceil(total / pageSize);
        if (total <= DOMESTIC_SEGMENT_LIMIT || depth >= DOMESTIC_MAX_SEGMENT_DEPTH) {
            segments.push({
                searchValue,
                total,
                pageSize,
                totalPages,
                firstPayload: payload,
            });
            logger.info(`${searchValue}: ${total} 条，使用当前检索段（共 ${totalPages} 页）`);
            return;
        }

        logger.info(`${searchValue}: ${total} 条，继续细分`);
        for (const digit of SEGMENT_DIGITS) {
            await split(`${searchValue}${digit}`, depth + 1);
        }
    }

    await split(baseSearch, 0);
    return segments;
}

async function crawlDomesticCategory(page, { baseSearch, outputName }, logger) {
    await fsExtra.ensureDir(OUTPUT_ROOT);
    const outputPath = path.join(OUTPUT_ROOT, outputName);
    const stream = fs.createWriteStream(outputPath, { flags: 'w', encoding: 'utf8' });
    let totalWritten = 0;

    try {
        const segments = await collectDomesticSegments(page, baseSearch, logger);
        for (const segment of segments) {
            let { searchValue, total, totalPages, firstPayload } = segment;
            logger.info(`${outputName}: [${searchValue}] 计划抓取 ${total} 条数据，共 ${totalPages} 页`);

            let pageNum = 1;
            let payload = firstPayload;
            let finished = false;

            while (!finished) {
                const records = payload.list || [];
                if (records.length === 0) break;

                const ids = records.map((item) => item.f4).filter(Boolean);
                await sleepRange(DETAIL_DELAY_RANGE);
                const batchDetails = await fetchDetailsBatch(page, DOMESTIC_ITEM_ID, ids);

                for (let index = 0; index < ids.length; index++) {
                    const id = ids[index];
                    let detailEntry = batchDetails[index];

                    if (!detailEntry || !detailEntry.success || !detailEntry.detail) {
                        try {
                            const fallback = await fetchDetailWithRetry(page, DOMESTIC_ITEM_ID, id);
                            if (!fallback) {
                                logger.warning(`${outputName}: 无法获取记录 ${id} 详情，已跳过`);
                                continue;
                            }
                            detailEntry = { detail: fallback, success: true };
                        } catch (error) {
                            logger.warning(`${outputName}: 重试记录 ${id} 详情失败: ${error.message}`);
                            continue;
                        }
                    }

                    const detail = detailEntry.detail;
                    if (!detail?.f0 || !detail.f0.startsWith('国药准字')) continue;

                    const record = {
                        code: detail.f0 || '',
                        zh: detail.f1 || '',
                        en: detail.f2 || '',
                    };

                    await writeJsonLine(stream, record);
                    totalWritten += 1;
                    await sleepRange(RECORD_DELAY_RANGE);
                }

                if (pageNum % 50 === 0 || pageNum === totalPages) {
                    logger.info(`${outputName}: [${searchValue}] 已完成第 ${pageNum}/${totalPages} 页，累计写入 ${totalWritten} 条`);
                }

                pageNum += 1;
                if (pageNum > totalPages) {
                    finished = true;
                } else {
                    await sleepRange(PAGE_DELAY_RANGE);
                    payload = await fetchListPage(page, { itemId: DOMESTIC_ITEM_ID, searchValue, pageNum });
                }
            }

            await sleepRange(SEGMENT_PAUSE_RANGE);
        }
    } finally {
        stream.end();
        await once(stream, 'finish');
        logger.info(`${outputName}: 写入完成，共 ${totalWritten} 条 => ${path.relative(process.cwd(), outputPath)}`);
    }
}

async function crawlImported(page, logger) {
    await fsExtra.ensureDir(OUTPUT_ROOT);
    const outputPathH = path.join(OUTPUT_ROOT, '进口H.jsonl');
    const outputPathS = path.join(OUTPUT_ROOT, '进口S.jsonl');
    const streamH = fs.createWriteStream(outputPathH, { flags: 'w', encoding: 'utf8' });
    const streamS = fs.createWriteStream(outputPathS, { flags: 'w', encoding: 'utf8' });

    let pageNum = 1;
    let totalPages = null;
    let writtenH = 0;
    let writtenS = 0;

    try {
        while (true) {
            const payload = await fetchListPage(page, { itemId: IMPORTED_ITEM_ID, searchValue: '国药准字', pageNum });
            if (!payload.list.length) {
                break;
            }

            if (totalPages === null) {
                totalPages = Math.ceil((payload.total || payload.list.length) / payload.pageSize);
                logger.info(`进口药品: 计划抓取 ${payload.total || 0} 条数据，共 ${totalPages} 页`);
            }

            const ids = payload.list.map((item) => item.f3).filter(Boolean);
            await sleepRange(DETAIL_DELAY_RANGE);
            const batchDetails = await fetchDetailsBatch(page, IMPORTED_ITEM_ID, ids, 2);

            for (let index = 0; index < ids.length; index++) {
                const id = ids[index];
                let detailEntry = batchDetails[index];

                if (!detailEntry || !detailEntry.success || !detailEntry.detail) {
                    try {
                        const fallback = await fetchDetailWithRetry(page, IMPORTED_ITEM_ID, id, DETAIL_RETRY_LIMIT + 1);
                        if (!fallback) {
                            logger.warning(`进口药品: 无法获取记录 ${id} 详情，已跳过`);
                            continue;
                        }
                        detailEntry = { detail: fallback, success: true };
                    } catch (error) {
                        logger.warning(`进口药品: 重试记录 ${id} 详情失败: ${error.message}`);
                        continue;
                    }
                }

                const detail = detailEntry.detail || {};
                const registration = detail.f1 || detail.f0 || '';
                if (!registration) continue;

                const baseRecord = {
                    code: registration,
                    product_zh: detail.f14 || detail.f1 || '',
                    product_en: detail.f15 || detail.f2 || '',
                    commodity_zh: detail.f16 || '',
                    commodity_en: detail.f17 || '',
                };

                if (registration.startsWith('H')) {
                    await writeJsonLine(streamH, baseRecord);
                    writtenH += 1;
                } else if (registration.startsWith('S')) {
                    await writeJsonLine(streamS, baseRecord);
                    writtenS += 1;
                }
                await sleepRange(RECORD_DELAY_RANGE);
            }

            if (pageNum % 50 === 0 || pageNum === totalPages) {
                logger.info(`进口药品: 已完成第 ${pageNum}/${totalPages} 页，累计 H=${writtenH}, S=${writtenS}`);
            }

            pageNum += 1;
            await sleepRange(PAGE_DELAY_RANGE);
            if (totalPages && pageNum > totalPages) break;
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
        await crawlDomesticCategory(page, { baseSearch: '国药准字H', outputName: '国内H.jsonl' }, logger);
    } else if (datasetKey === 'domestic-s') {
        await crawlDomesticCategory(page, { baseSearch: '国药准字S', outputName: '国内S.jsonl' }, logger);
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

    const envDatasets = process.env.NMPA_DATASETS
        ? process.env.NMPA_DATASETS.split(',').map((value) => value.trim()).filter(Boolean)
        : null;
    const datasetKeys = options.datasets ?? envDatasets ?? ['domestic-h', 'domestic-s', 'imported'];
    const proxy = resolveProxySettings();

    const crawler = new PlaywrightCrawler({
        headless: true,
        maxConcurrency: 1,
        requestHandlerTimeoutSecs: 7200,
        navigationTimeoutSecs: 120,
        maxRequestsPerCrawl: datasetKeys.length,
        launchContext: {
            launchOptions: {
                executablePath,
                args: ['--no-sandbox', '--disable-setuid-sandbox', '--headless=new'],
                proxy,
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
