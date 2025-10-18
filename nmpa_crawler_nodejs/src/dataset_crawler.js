import { chromium } from 'playwright';
import { log as crawlerLog } from 'crawlee';
import fs from 'fs';
import fsExtra from 'fs-extra';
import path from 'path';
import os from 'os';
import { once } from 'events';
import { fileURLToPath } from 'url';

import { StateManager } from './state_manager.js';
import { ProxyManager } from './proxy_manager.js';
import { RequestBlockedError } from './errors.js';

const SEARCH_URL = 'https://www.nmpa.gov.cn/datasearch/search-result.html';

const DOMESTIC_ITEM_ID = 'ff80808183cad75001840881f848179f';
const IMPORTED_ITEM_ID = 'ff80808183cad7500184088665711800';

const PAGE_SIZE = Math.max(1, parseInt(process.env.NMPA_PAGE_SIZE ?? '20', 10));
const DOMESTIC_MAX_PAGES = Math.max(1, parseInt(process.env.NMPA_DOMESTIC_MAX_PAGES ?? '500', 10));
const DEFAULT_SEGMENT_DEPTH = 4;
const DEFAULT_SEGMENT_LIMIT = PAGE_SIZE * DOMESTIC_MAX_PAGES;
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

function parseProxyUrl(raw) {
    if (!raw) return undefined;
    try {
        const hasScheme = /:\/\//.test(raw);
        const parsed = new URL(hasScheme ? raw : `http://${raw}`);
        return {
            server: `${parsed.protocol}//${parsed.hostname}${parsed.port ? `:${parsed.port}` : ''}`,
            username: parsed.username ? decodeURIComponent(parsed.username) : undefined,
            password: parsed.password ? decodeURIComponent(parsed.password) : undefined,
        };
    } catch (error) {
        crawlerLog.warning(`代理地址解析失败: ${error.message}`);
        return undefined;
    }
}

async function writeJsonLine(stream, data) {
    const json = JSON.stringify(data, (_, value) => (value === null ? '' : value ?? ''));
    const line = `${json}\n`;
    if (!stream.write(line, 'utf8')) {
        await once(stream, 'drain');
    }
}

async function writeJsonLines(stream, records) {
    for (const record of records) {
        await writeJsonLine(stream, record);
        await sleepRange(RECORD_DELAY_RANGE);
    }
}

function createDatasetLogger(datasetKey) {
    const prefix = `[${datasetKey}]`;
    return {
        info: (message) => crawlerLog.info(`${prefix} ${message}`),
        warning: (message) => crawlerLog.warning(`${prefix} ${message}`),
        error: (message) => crawlerLog.error(`${prefix} ${message}`),
    };
}

function unwrapListPayload(raw) {
    const candidates = [raw?.data?.data, raw?.data, raw];
    for (const candidate of candidates) {
        if (candidate && typeof candidate === 'object' && Array.isArray(candidate.list)) {
            return candidate;
        }
    }
    return null;
}

function extractResponseMessage(raw) {
    return raw?.message || raw?.data?.message || raw?.data?.data?.message || '';
}

function isBlockedMessage(message) {
    if (!message) return false;
    const keywords = ['status code 400', 'status code 403', 'status code 412', '验证失败', '访问被拒绝'];
    return keywords.some((keyword) => message.includes(keyword));
}

async function fetchListPage(page, { itemId, searchValue, pageNum }, attempt = 0, options = {}) {
    const pageSize = options.pageSize ?? PAGE_SIZE;
    const canFallback = options.canFallback ?? (pageSize !== 20);
    await sleepRange(LIST_DELAY_RANGE);
    const result = await page.evaluate(async (params) => {
        try {
            window.getUrl = window.getUrl || (() => '');
            const raw = await window.pajax.hasTokenGet(window.api.queryList, {
                itemId: params.itemId,
                isSenior: 'N',
                searchValue: params.searchValue,
                pageNum: params.pageNum,
                pageSize: params.pageSize,
            });
            return { ok: true, payload: raw };
        } catch (error) {
            return { ok: false, message: error?.message || String(error) };
        }
    }, { itemId, searchValue, pageNum, pageSize });

    if (!result.ok) {
        const message = result.message || '无法获取列表数据';
        if (isBlockedMessage(message)) {
            throw new RequestBlockedError(message, { type: 'list', searchValue, pageNum });
        }
        if (attempt + 1 >= LIST_RETRY_LIMIT) {
            throw new Error(message);
        }
        const delay = randomBetween(1500, 3000) * (attempt + 1);
        crawlerLog.warning(`列表请求失败(${attempt + 1}/${LIST_RETRY_LIMIT})，${message}，${delay}ms 后重试`);
        await sleep(delay);
        return fetchListPage(page, { itemId, searchValue, pageNum }, attempt + 1, { pageSize, canFallback });
    }

    const payload = unwrapListPayload(result.payload);
    if (!payload) {
        const message = extractResponseMessage(result.payload) || '返回数据缺失 list 字段';
        if (isBlockedMessage(message)) {
            throw new RequestBlockedError(message, { type: 'list', searchValue, pageNum });
        }
        throw new Error(`无法获取列表数据: ${message}`);
    }

    const records = Array.isArray(payload.list) ? payload.list : [];
    const total = Number(payload.total) || 0;
    const effectivePageSize = Number(payload.pageSize) || pageSize;

    if (total > 0 && records.length === 0 && canFallback && pageSize > 20) {
        crawlerLog.warning(`列表返回为空，尝试使用 pageSize=20 重新请求: ${searchValue} 第 ${pageNum} 页`);
        return fetchListPage(page, { itemId, searchValue, pageNum }, attempt, { pageSize: 20, canFallback: false });
    }

    return {
        searchValue,
        pageNum,
        pageSize: effectivePageSize,
        total,
        list: records,
    };
}

async function fetchDetailsBatch(page, itemId, recordIds, concurrency = 3) {
    if (recordIds.length === 0) return [];

    const results = await page.evaluate(async (params) => {
        const { itemId, recordIds, concurrency } = params;
        const output = new Array(recordIds.length);
        let index = 0;

        const pickDetail = (raw) => raw?.data?.data?.detail ?? raw?.data?.detail ?? raw?.detail ?? null;

        async function worker() {
            while (index < recordIds.length) {
                const current = index++;
                const id = recordIds[current];
                try {
                    window.getUrl = window.getUrl || (() => '');
                    const raw = await window.pajax.hasTokenGet(window.api.queryDetail, {
                        id,
                        itemId,
                        isSenior: 'N',
                    });
                    const detail = pickDetail(raw);
                    const message = raw?.message || raw?.data?.message || '';
                    output[current] = { id, success: !!detail, detail, message };
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

    return results;
}

async function fetchDetailWithRetry(page, itemId, id, retries = DETAIL_RETRY_LIMIT) {
    for (let attempt = 0; attempt <= retries; attempt++) {
        try {
            await sleepRange(DETAIL_DELAY_RANGE);
            const payload = await page.evaluate(async (params) => {
                try {
                    window.getUrl = window.getUrl || (() => '');
                    const raw = await window.pajax.hasTokenGet(window.api.queryDetail, {
                        id: params.id,
                        itemId: params.itemId,
                        isSenior: 'N',
                    });
                    const detail = raw?.data?.data?.detail ?? raw?.data?.detail ?? raw?.detail ?? null;
                    const message = raw?.message || raw?.data?.message || '';
                    return { ok: !!detail, detail, message };
                } catch (error) {
                    return { ok: false, message: error?.message || String(error) };
                }
            }, { itemId, id });

            if (payload.ok && payload.detail) {
                return payload.detail;
            }

            if (payload.message && isBlockedMessage(payload.message)) {
                throw new RequestBlockedError(payload.message, { type: 'detail', id });
            }

            throw new Error(payload.message || '未知错误');
        } catch (error) {
            if (error instanceof RequestBlockedError) throw error;
            if (attempt === retries) throw error;
            const delay = randomBetween(1200, 2500) * (attempt + 1);
            crawlerLog.warning(`详情重试 ${id} (${attempt + 1}/${retries}) 失败: ${error.message}，${delay}ms 后重试`);
            await sleep(delay);
        }
    }
    return null;
}

async function collectDomesticSegments({ page, baseSearch, datasetKey, stateManager, logger }) {
    const segments = [];
    const visited = new Set();

    async function split(searchValue, depth) {
        if (visited.has(searchValue)) return;
        visited.add(searchValue);

        await sleepRange(SEGMENT_DELAY_RANGE);
        const payload = await fetchListPage(page, { itemId: DOMESTIC_ITEM_ID, searchValue, pageNum: 1 });
        const total = payload.total;
        if (!total) {
            logger.info(`${searchValue}: 无数据，跳过`);
            return;
        }

        const effectivePageSize = payload.pageSize || PAGE_SIZE;
        const totalPages = Math.ceil(total / Math.max(1, effectivePageSize));
        if (((total <= DOMESTIC_SEGMENT_LIMIT) && (totalPages <= DOMESTIC_MAX_PAGES)) || depth >= DOMESTIC_MAX_SEGMENT_DEPTH) {
            segments.push({
                searchValue,
                total,
                pageSize: effectivePageSize,
                totalPages,
                firstPayload: { ...payload, pageSize: effectivePageSize },
            });
            stateManager.initSegment(datasetKey, { segmentKey: searchValue, total, totalPages });
            logger.info(`${searchValue}: ${total} 条，使用当前检索段（共 ${totalPages} 页）`);
            return;
        }

        logger.info(`${searchValue}: ${total} 条，继续细分`);
        for (const digit of SEGMENT_DIGITS) {
            await split(`${searchValue}${digit}`, depth + 1);
        }
    }

    await split(baseSearch, 0);
    await stateManager.save();
    return segments;
}

function createRuntime(stateManager) {
    const streams = new Map();

    return {
        stateManager,
        getStream(datasetKey) {
            if (!streams.has(datasetKey)) {
                const dataset = stateManager.getDataset(datasetKey);
                fsExtra.ensureDirSync(path.dirname(dataset.outputPath));
                const flags = fs.existsSync(dataset.outputPath) ? 'a' : 'w';
                const stream = fs.createWriteStream(dataset.outputPath, { flags, encoding: 'utf8' });
                streams.set(datasetKey, stream);
            }
            return streams.get(datasetKey);
        },
        async closeStreams() {
            const closeTasks = Array.from(streams.values()).map((stream) => new Promise((resolve) => {
                stream.end(resolve);
                stream.on('error', resolve);
            }));
            await Promise.all(closeTasks);
            streams.clear();
        },
    };
}

async function navigateToSearch(page) {
    try {
        await page.goto(SEARCH_URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
        await page.waitForFunction(() => window.api && window.pajax && window.itemFileUrl, { timeout: 60000 });
    } catch (error) {
        const message = error?.message || '导航阶段失败';
        if (message.includes('Timeout') || message.includes('net::') || message.includes('ERR')) {
            throw new RequestBlockedError(message, { type: 'navigation' });
        }
        throw error;
    }
}

async function processDomesticSegment(page, { datasetKey, segment, runtime, logger }) {
    const { stateManager } = runtime;
    const segmentKey = segment.searchValue;
    const segmentState = stateManager.getSegment(datasetKey, segmentKey);
    const stream = runtime.getStream(datasetKey);

    let pageNum = segmentState.nextPage || 1;
    let payload = null;
    if (pageNum === 1 && segment.firstPayload && !(segmentState.processedPages || []).includes(1)) {
        payload = segment.firstPayload;
    }

    try {
        while (true) {
            stateManager.markSegmentInProgress(datasetKey, segmentKey, pageNum);
            await stateManager.save();

            if (!payload) {
                payload = await fetchListPage(page, { itemId: DOMESTIC_ITEM_ID, searchValue: segmentKey, pageNum });
            }

            const records = payload.list || [];
            if (!records.length) break;

            const ids = records.map((item) => item.f4).filter(Boolean);
            await sleepRange(DETAIL_DELAY_RANGE);
            const batchDetails = await fetchDetailsBatch(page, DOMESTIC_ITEM_ID, ids);

            const pageRecords = [];
            for (let index = 0; index < ids.length; index++) {
                const id = ids[index];
                let detailEntry = batchDetails[index];

                if (!detailEntry || !detailEntry.success || !detailEntry.detail) {
                    try {
                        const fallback = await fetchDetailWithRetry(page, DOMESTIC_ITEM_ID, id);
                        if (!fallback) {
                            logger.warning(`${datasetKey}: 无法获取记录 ${id} 详情，已跳过`);
                            continue;
                        }
                        detailEntry = { detail: fallback, success: true };
                    } catch (error) {
                        if (error instanceof RequestBlockedError) throw error;
                        logger.warning(`${datasetKey}: 重试记录 ${id} 详情失败: ${error.message}`);
                        continue;
                    }
                }

                const detail = detailEntry.detail;
                if (!detail?.f0 || !detail.f0.startsWith('国药准字')) continue;

                pageRecords.push({
                    code: detail.f0 || '',
                    zh: detail.f1 || '',
                    en: detail.f2 || '',
                });
            }

            if (pageRecords.length > 0) {
                await writeJsonLines(stream, pageRecords);
            }

            stateManager.recordPageResult(datasetKey, segmentKey, pageNum, pageRecords.length);
            await stateManager.save();

            if (pageNum % 10 === 0 || pageNum === segment.totalPages) {
                const progress = stateManager.getSegment(datasetKey, segmentKey);
                logger.info(`${datasetKey}: [${segmentKey}] 已完成第 ${pageNum}/${segment.totalPages} 页，段累计 ${progress.written} 条`);
            }

            pageNum += 1;
            if (segment.totalPages && pageNum > segment.totalPages) break;

            await sleepRange(PAGE_DELAY_RANGE);
            payload = await fetchListPage(page, { itemId: DOMESTIC_ITEM_ID, searchValue: segmentKey, pageNum });
        }

        stateManager.markSegmentCompleted(datasetKey, segmentKey);
        await stateManager.save();
        await sleepRange(SEGMENT_PAUSE_RANGE);
    } catch (error) {
        stateManager.markSegmentFailed(datasetKey, segmentKey, error.message);
        await stateManager.save();
        throw error;
    }
}

async function crawlDomesticCategory(page, { datasetKey, baseSearch }, runtime) {
    const { stateManager } = runtime;
    const logger = createDatasetLogger(datasetKey);

    stateManager.setDatasetStatus(datasetKey, 'running');
    stateManager.setDatasetStatus('imported-h', 'running');
    stateManager.setDatasetStatus('imported-s', 'running');
    await stateManager.save();

    const segments = await collectDomesticSegments({
        page,
        baseSearch,
        datasetKey,
        stateManager,
        logger,
    });

    const orderedSegmentKeys = segments.map((segment) => segment.searchValue);
    const pendingKeys = stateManager.getPendingSegments(datasetKey, orderedSegmentKeys);
    if (!pendingKeys.length) {
        logger.info(`${datasetKey}: 所有细分段均已完成，跳过`);
        return;
    }

    for (const segment of segments) {
        if (!pendingKeys.includes(segment.searchValue)) continue;
        await processDomesticSegment(page, { datasetKey, segment, runtime, logger });
    }
}

async function crawlImported(page, runtime) {
    const { stateManager } = runtime;
    const datasetKey = 'imported';
    const segmentKey = 'imported';
    const logger = createDatasetLogger(datasetKey);

    stateManager.setDatasetStatus(datasetKey, 'running');
    stateManager.setDatasetStatus('imported-h', 'running');
    stateManager.setDatasetStatus('imported-s', 'running');
    await stateManager.save();

    const segmentState = stateManager.getSegment(datasetKey, segmentKey);
    const streamH = runtime.getStream('imported-h');
    const streamS = runtime.getStream('imported-s');

    let pageNum = segmentState.nextPage || 1;
    let totalPages = segmentState.totalPages || null;

    try {
        while (true) {
            stateManager.markSegmentInProgress(datasetKey, segmentKey, pageNum);
            await stateManager.save();

            const payload = await fetchListPage(page, { itemId: IMPORTED_ITEM_ID, searchValue: '国药准字', pageNum });
            if (!payload.list.length) break;

            if (!totalPages) {
                const effectivePageSize = payload.pageSize || PAGE_SIZE;
                totalPages = Math.ceil((payload.total || payload.list.length) / Math.max(1, effectivePageSize));
                stateManager.initSegment(datasetKey, {
                    segmentKey,
                    total: payload.total || payload.list.length,
                    totalPages,
                });
                await stateManager.save();
                logger.info(`进口药品: 计划抓取 ${payload.total || 0} 条数据，共 ${totalPages} 页`);
            }

            const ids = payload.list.map((item) => item.f3).filter(Boolean);
            await sleepRange(DETAIL_DELAY_RANGE);
            const batchDetails = await fetchDetailsBatch(page, IMPORTED_ITEM_ID, ids, 2);

            const pageRecordsH = [];
            const pageRecordsS = [];

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
                        if (error instanceof RequestBlockedError) throw error;
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
                    pageRecordsH.push(baseRecord);
                } else if (registration.startsWith('S')) {
                    pageRecordsS.push(baseRecord);
                }
            }

            if (pageRecordsH.length) {
                await writeJsonLines(streamH, pageRecordsH);
                const datasetH = stateManager.getDataset('imported-h');
                datasetH.written += pageRecordsH.length;
                datasetH.lastUpdated = new Date().toISOString();
            }

            if (pageRecordsS.length) {
                await writeJsonLines(streamS, pageRecordsS);
                const datasetS = stateManager.getDataset('imported-s');
                datasetS.written += pageRecordsS.length;
                datasetS.lastUpdated = new Date().toISOString();
            }

            stateManager.recordPageResult(datasetKey, segmentKey, pageNum, pageRecordsH.length + pageRecordsS.length);
            await stateManager.save();

            if (pageNum % 10 === 0 || (totalPages && pageNum === totalPages)) {
                logger.info(`进口药品: 已完成第 ${pageNum}/${totalPages || '?'} 页，累计 H=${stateManager.getDataset('imported-h').written}, S=${stateManager.getDataset('imported-s').written}`);
            }

            pageNum += 1;
            if (totalPages && pageNum > totalPages) break;
            await sleepRange(PAGE_DELAY_RANGE);
        }

        stateManager.markSegmentCompleted(datasetKey, segmentKey);
        stateManager.markDatasetCompleted(datasetKey);
        stateManager.setDatasetStatus('imported-h', 'completed');
        stateManager.setDatasetStatus('imported-s', 'completed');
        await stateManager.save();
    } catch (error) {
        stateManager.markSegmentFailed(datasetKey, segmentKey, error.message);
        await stateManager.save();
        throw error;
    }
}

async function processDataset(page, datasetKey, runtime) {
    const stateManager = runtime.stateManager;
    const logger = createDatasetLogger(datasetKey);

    await navigateToSearch(page);

    try {
        if (datasetKey === 'domestic-h') {
            await crawlDomesticCategory(page, { datasetKey, baseSearch: '国药准字H' }, runtime);
        } else if (datasetKey === 'domestic-s') {
            await crawlDomesticCategory(page, { datasetKey, baseSearch: '国药准字S' }, runtime);
        } else if (datasetKey === 'imported') {
            await crawlImported(page, runtime);
        } else {
            throw new Error(`未知的数据集标识: ${datasetKey}`);
        }

        stateManager.markDatasetCompleted(datasetKey);
        await stateManager.save();
        logger.info(`${datasetKey}: 数据集处理完成`);
    } catch (error) {
        stateManager.recordError(error, { datasetKey });
        await stateManager.save();
        throw error;
    }
}

async function launchBrowser(proxyInfo) {
    const executablePath = resolveChromiumExecutable();
    if (!executablePath) {
        crawlerLog.warning('未找到 Playwright Chromium 缓存，使用默认浏览器配置。');
    } else {
        crawlerLog.info(`使用 Chromium 可执行文件: ${executablePath}`);
    }

    const launchOptions = {
        headless: process.env.NMPA_SHOW_BROWSER !== 'true',
        executablePath,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
    };

    if (proxyInfo?.url) {
        launchOptions.proxy = parseProxyUrl(proxyInfo.url);
    }

    const browser = await chromium.launch(launchOptions);
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.addInitScript(() => {
        window.getUrl = window.getUrl || (() => '');
    });
    return { browser, context, page };
}

async function runDatasetCrawler(options = {}) {
    const envDatasets = process.env.NMPA_DATASETS
        ? process.env.NMPA_DATASETS.split(',').map((value) => value.trim()).filter(Boolean)
        : null;

    const resumeRunId = process.env.NMPA_RESUME_RUN_ID || null;
    const presetRunId = process.env.NMPA_RUN_ID || null;

    let datasetKeys = options.datasets ?? envDatasets ?? null;

    let stateManager;
    if (resumeRunId) {
        stateManager = await StateManager.load(resumeRunId);
        datasetKeys = datasetKeys ?? stateManager.config.datasets;
        crawlerLog.info(`恢复运行: ${resumeRunId}`);
    } else {
        const initialConfig = {
            runId: presetRunId || undefined,
            datasets: datasetKeys ?? ['domestic-h', 'domestic-s', 'imported'],
            pageSize: PAGE_SIZE,
            maxPages: DOMESTIC_MAX_PAGES,
            concurrency: parseInt(process.env.NMPA_MAX_CONCURRENCY ?? '1', 10),
            useProxy: Boolean(process.env.NMPA_PROXY || process.env.NMPA_PROXY_LIST || process.env.NMPA_PROXY_POOL),
            proxyList: [],
            additional: {},
        };
        stateManager = await StateManager.createInitial(initialConfig);
        datasetKeys = initialConfig.datasets;
    }

    datasetKeys = datasetKeys ?? stateManager.config.datasets;
    datasetKeys.forEach((datasetKey) => stateManager.getDataset(datasetKey));
    await stateManager.save();

    const runtime = createRuntime(stateManager);
    const proxyManager = new ProxyManager(stateManager, { allowDirect: true });

    if (!stateManager.config.proxyList || !stateManager.config.proxyList.length) {
        stateManager.config.proxyList = proxyManager.getProxies().map((proxy) => proxy.label);
        await stateManager.save();
    }

    const maxAttempts = Number(process.env.NMPA_MAX_ATTEMPTS || '50');
    let attempt = 0;

    while (!stateManager.areAllDatasetsCompleted()) {
        attempt += 1;
        const proxyInfo = proxyManager.getCurrent();
        crawlerLog.info(`尝试第 ${attempt} 轮抓取，使用代理: ${proxyInfo.label || 'direct'}`);

        let browser;
        try {
            const launched = await launchBrowser(proxyInfo);
            browser = launched.browser;
            const { page } = launched;

            for (const datasetKey of datasetKeys) {
                const dataset = stateManager.getDataset(datasetKey);
                if (dataset.status === 'completed') {
                    continue;
                }
                await processDataset(page, datasetKey, runtime);
            }

            await browser.close();
            browser = null;
        } catch (error) {
            if (browser) {
                await browser.close().catch(() => {});
            }
            stateManager.recordError(error, { attempt, proxy: proxyInfo });
            await stateManager.save();

            if (proxyManager.shouldRotateForError(error)) {
                crawlerLog.warning(`检测到代理 ${proxyInfo.label || 'direct'} 可能失效: ${error.message}`);
                await proxyManager.rotate(error.name || 'blocked', { message: error.message });
                if (attempt >= maxAttempts) {
                    throw error;
                }
                continue;
            }

            throw error;
        }
    }

    await runtime.closeStreams();
    stateManager.status = 'completed';
    await stateManager.save();
    crawlerLog.info('全部数据集抓取完成。');
    return {
        runId: stateManager.runId,
        runDir: stateManager.runDir,
        datasetsDir: stateManager.datasetsDir,
    };
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
