import { PlaywrightCrawler, log as crawlerLog } from 'crawlee';
import fs from 'fs';
import fsExtra from 'fs-extra';
import path from 'path';
import os from 'os';
import { once } from 'events';
import { fileURLToPath } from 'url';
import playwright from 'playwright';

const SEARCH_URL = 'https://www.nmpa.gov.cn/datasearch/search-result.html';
const OUTPUT_ROOT = path.resolve(process.env.NMPA_OUTPUT_ROOT ?? 'outputs/datasets');
const PLAYWRIGHT_ARGS = ['--no-sandbox', '--disable-setuid-sandbox', '--headless=new'];

const DOMESTIC_ITEM_ID = 'ff80808183cad75001840881f848179f';
const IMPORTED_ITEM_ID = 'ff80808183cad7500184088665711800';

const RAW_PAGE_SIZE = Math.max(1, parseInt(process.env.NMPA_PAGE_SIZE ?? '20', 10));
const REQUEST_PAGE_SIZE = Math.min(RAW_PAGE_SIZE, 20);
const DOMESTIC_MAX_PAGES = Math.min(
    50,
    Math.max(1, parseInt(process.env.NMPA_DOMESTIC_MAX_PAGES ?? '50', 10)),
);
const DEFAULT_SEGMENT_LIMIT = REQUEST_PAGE_SIZE * DOMESTIC_MAX_PAGES;
const DOMESTIC_SEGMENT_LIMIT = Math.min(
    DEFAULT_SEGMENT_LIMIT,
    Math.max(1, parseInt(process.env.NMPA_DOMESTIC_SEGMENT_LIMIT ?? `${DEFAULT_SEGMENT_LIMIT}`, 10)),
);
const DOMESTIC_MAX_SEGMENT_DEPTH = Math.max(1, parseInt(process.env.NMPA_DOMESTIC_SEGMENT_DEPTH ?? '20', 10));

const SEGMENT_DIGITS = (process.env.NMPA_SEGMENT_DIGITS || (() => {
    const digits = Array.from({ length: 10 }, (_, index) => String(index));
    const letters = Array.from({ length: 26 }, (_, index) => String.fromCharCode(65 + index));
    return digits.concat(letters).join(',');
})())
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean);

if (RAW_PAGE_SIZE !== REQUEST_PAGE_SIZE) {
    crawlerLog.warning(`指定的 NMPA_PAGE_SIZE=${RAW_PAGE_SIZE} 超出接口允许范围，已调整为 ${REQUEST_PAGE_SIZE}`);
}

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
const LIST_DELAY_RANGE = createRange(
    parseInt(process.env.NMPA_LIST_DELAY_MIN ?? '900', 10),
    parseInt(process.env.NMPA_LIST_DELAY_MAX ?? '2000', 10),
);
const RECORD_DELAY_RANGE = createRange(
    parseInt(process.env.NMPA_RECORD_DELAY_MIN ?? '80', 10),
    parseInt(process.env.NMPA_RECORD_DELAY_MAX ?? '180', 10),
);

const LIST_RETRY_LIMIT = Math.max(1, parseInt(process.env.NMPA_LIST_RETRY_LIMIT ?? '3', 10));
const DETAIL_RETRY_LIMIT = Math.max(0, parseInt(process.env.NMPA_DETAIL_RETRY_LIMIT ?? '2', 10));
const DETAIL_CONCURRENCY = Math.max(1, parseInt(process.env.NMPA_DETAIL_CONCURRENCY ?? '4', 10));
const DETAIL_BATCH_DELAY_MS = Math.max(0, parseInt(process.env.NMPA_DETAIL_BATCH_DELAY_MS ?? '15000', 10));
const PAGE_LOG_INTERVAL = Math.max(1, parseInt(process.env.NMPA_PAGE_LOG_INTERVAL ?? '50', 10));
const DETAIL_SUCCESS_MIN_RATIO = Math.min(
    1,
    Math.max(0, parseFloat(process.env.NMPA_DETAIL_SUCCESS_MIN_RATIO ?? '0.2')),
);
const BLOCK_COOLDOWN_MS = Math.max(0, parseInt(process.env.NMPA_BLOCK_COOLDOWN_MS ?? '300000', 10));
const BLOCK_MAX_COOLDOWN_ATTEMPTS = Math.max(0, parseInt(process.env.NMPA_BLOCK_MAX_COOLDOWN_ATTEMPTS ?? '3', 10));
const BROWSER_SEQUENCE = (() => {
    const allowed = new Set(['chromium', 'firefox', 'webkit']);
    const raw = (process.env.NMPA_BROWSER_SEQUENCE ?? 'chromium')
        .split(',')
        .map((value) => value.trim().toLowerCase())
        .filter(Boolean);
    const normalized = raw.filter((value) => allowed.has(value));
    if (normalized.length === 0) {
        if (raw.length > 0) {
            crawlerLog.warning(`NMPA_BROWSER_SEQUENCE=${raw.join(',')} 不包含可用浏览器类型，已回退为 chromium`);
        }
        return ['chromium'];
    }
    return normalized;
})();
const BROWSER_PAGE_BATCH = Math.max(0, parseInt(process.env.NMPA_BROWSER_PAGE_BATCH ?? '0', 10));
const BROWSER_SWAP_DELAY_MS = Math.max(0, parseInt(process.env.NMPA_BROWSER_SWAP_DELAY_MS ?? '300000', 10));

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

function shouldRotateForListError(error) {
    if (!error) return false;
    if (error.shouldRotate) return true;
    const message = typeof error.message === 'string' ? error.message.toLowerCase() : '';
    return /status code 4\d\d|403|412|timeout|target page|context or browser has been closed/.test(message);
}

async function closeQuietly(resource) {
    if (!resource || typeof resource.close !== 'function') return;
    try {
        await resource.close();
    } catch (error) {
        // ignore
    }
}

class BrowserController {
    constructor({ initialPage, logger, proxy, browserArgs, swapDelayMs, sequence }) {
        this.logger = logger;
        this.proxy = proxy;
        this.browserArgs = browserArgs;
        this.swapDelayMs = swapDelayMs;
        this.sequence = sequence.length > 0 ? sequence : ['chromium'];

        this.currentPage = initialPage ?? null;
        this.currentContext = this.currentPage?.context?.() ?? null;
        this.currentBrowser = this.currentContext?.browser?.() ?? null;
        this.ownsCurrentBrowser = false;
        this.disabledTypes = new Set();

        const detectedType = this.detectType(this.currentBrowser);
        this.currentBrowserType = detectedType ?? this.sequence[0];
        const detectedIndex = detectedType ? this.sequence.indexOf(detectedType) : -1;
        this.rotationIndex = detectedIndex >= 0 ? detectedIndex + 1 : 0;
    }

    detectType(browser) {
        try {
            const type = browser?.browserType?.()?.name?.();
            return typeof type === 'string' ? type.toLowerCase() : null;
        } catch {
            return null;
        }
    }

    async initialize() {
        if (this.currentPage) {
            await this.preparePage(this.currentPage);
            return;
        }
        await this.launchNextBrowser();
    }

    async preparePage(page) {
        if (!page) return;
        await page.addInitScript(() => {
            window.getUrl = window.getUrl || (() => '');
        });
        await navigateToSearch(page);
    }

    async getPage() {
        if (!this.currentPage) {
            await this.launchNextBrowser();
        }
        return this.currentPage;
    }

    async launchNextBrowser() {
        if (this.sequence.length === 0) throw new Error('Browser sequence is empty.');

        const total = this.sequence.length;
        let attempts = 0;
        let lastError = null;
        const attemptedTypes = new Set();

        while (attempts < total * 2) {
            if (this.disabledTypes.size >= total) {
                this.logger.warning('所有浏览器已被标记为不可用，清空禁用列表后重试');
                this.disabledTypes.clear();
            }

            const index = this.rotationIndex % this.sequence.length;
            const browserTypeName = this.sequence[index] || 'chromium';
            this.rotationIndex += 1;
            attempts += 1;
            attemptedTypes.add(browserTypeName);

            if (this.disabledTypes.has(browserTypeName)) {
                continue;
            }

            const launcher = playwright[browserTypeName];
            if (!launcher) {
                this.logger.warning(`Playwright 不支持浏览器类型 ${browserTypeName}`);
                continue;
            }

            const launchOptions = {
                headless: true,
                args: this.browserArgs,
            };
            if (this.proxy) {
                launchOptions.proxy = { ...this.proxy };
            }

            let browser = null;
            let context = null;
            let page = null;
            try {
                browser = await launcher.launch(launchOptions);
                context = await browser.newContext();
                page = await context.newPage();

                await this.preparePage(page);

                this.currentBrowser = browser;
                this.currentContext = context;
                this.currentPage = page;
                this.currentBrowserType = browserTypeName;
                this.ownsCurrentBrowser = true;

                this.logger.info(`已切换至 ${browserTypeName} 浏览器实例`);
                return;
            } catch (error) {
                lastError = error;
                this.logger.warning(`${browserTypeName} 浏览器启动失败: ${error.message}`);
                await closeQuietly(page);
                await closeQuietly(context);
                await closeQuietly(browser);
            }
        }

        throw new Error(`无法启动任何浏览器 (${Array.from(attemptedTypes).join(', ')})：${lastError?.message ?? 'unknown error'}`);
    }

    async rotateBrowser(reason) {
        if (this.swapDelayMs > 0) {
            this.logger.info(`${reason}，准备轮换浏览器，暂停 ${this.swapDelayMs}ms`);
            await sleep(this.swapDelayMs);
        }
        await this.disposeCurrent();
        await this.launchNextBrowser();
    }

    async disposeCurrent() {
        await closeQuietly(this.currentPage);
        await closeQuietly(this.currentContext);
        if (this.ownsCurrentBrowser) {
            await closeQuietly(this.currentBrowser);
        }
        this.currentPage = null;
        this.currentContext = null;
        this.currentBrowser = null;
        this.ownsCurrentBrowser = false;
    }

    async dispose() {
        await this.disposeCurrent();
    }

    markCurrentBrowserUnhealthy(reason) {
        const type = this.currentBrowserType;
        if (!type) return false;
        if (this.sequence.length <= 1) return false;
        if (this.disabledTypes.has(type)) return false;
        this.logger.warning(`${type} 浏览器已标记为不可用：${reason}`);
        this.disabledTypes.add(type);
        return true;
    }
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
        const server = `${parsed.protocol}//${parsed.hostname}${parsed.port ? `:${parsed.port}` : ''}`;
        const username = parsed.username ? decodeURIComponent(parsed.username) : undefined;
        const password = parsed.password ? decodeURIComponent(parsed.password) : undefined;
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

async function fetchListPage(page, { itemId, searchValue, pageNum, pageSize = REQUEST_PAGE_SIZE }, attempt = 0, recoveryAttempts = 0) {
    await sleepRange(LIST_DELAY_RANGE);
    try {
        const response = await page.evaluate(async (params) => {
            window.getUrl = window.getUrl || (() => '');
            const raw = await window.pajax.hasTokenGet(window.api.queryList, {
                itemId: params.itemId,
                isSenior: 'N',
                searchValue: params.searchValue,
                pageNum: params.pageNum,
                pageSize: params.pageSize,
            });
            return raw;
        }, { itemId, searchValue, pageNum, pageSize: REQUEST_PAGE_SIZE });

        const payload = response?.data?.data;
        if (!payload || !Array.isArray(payload.list)) {
            const message = response?.message || response?.data?.message || 'unknown response';
            throw new Error(message);
        }
        return payload;
    } catch (error) {
        const message = (error?.message || '').toLowerCase();
        const looksBlocked = message.includes('status code 4') || message.includes('status code 5') || message.includes('timeout') || message.includes('getcookie');
        const shouldRotate = shouldRotateForListError(error);

        if (attempt + 1 >= LIST_RETRY_LIMIT) {
            if (looksBlocked && BLOCK_COOLDOWN_MS > 0 && recoveryAttempts < BLOCK_MAX_COOLDOWN_ATTEMPTS) {
                crawlerLog.warning(`列表请求连续失败，可能触发封禁，等待 ${BLOCK_COOLDOWN_MS}ms 后重试（已冷却 ${recoveryAttempts}/${BLOCK_MAX_COOLDOWN_ATTEMPTS} 次）`);
                await sleep(BLOCK_COOLDOWN_MS);
                return fetchListPage(page, { itemId, searchValue, pageNum, pageSize }, 0, recoveryAttempts + 1);
            }

            if (error && typeof error === 'object') {
                error.shouldRotate = error.shouldRotate ?? shouldRotate;
                error.shouldCooldown = error.shouldCooldown ?? looksBlocked;
            }
            throw error;
        }

        const delay = randomBetween(1500, 3000) * (attempt + 1);
        crawlerLog.warning(`列表请求失败(${attempt + 1}/${LIST_RETRY_LIMIT})，${error.message || error}，${delay}ms 后重试`);
        await sleep(delay);
        return fetchListPage(page, { itemId, searchValue, pageNum, pageSize }, attempt + 1, recoveryAttempts);
    }
}

async function processDomesticSegments(controller, baseSearch, logger, onSegment) {
    const visited = new Set();
    let segmentIndex = 0;

    async function split(searchValue, depth) {
        if (visited.has(searchValue)) return;
        visited.add(searchValue);

        const page = await controller.getPage();
        await sleepRange(SEGMENT_DELAY_RANGE);
        const payload = await fetchListPage(page, { itemId: DOMESTIC_ITEM_ID, searchValue, pageNum: 1, pageSize: REQUEST_PAGE_SIZE });
        const total = payload.total || 0;
        if (!total) {
            logger.info(`${searchValue}: 无数据，跳过`);
            return;
        }

        const effectivePageSize = payload.pageSize || REQUEST_PAGE_SIZE;
        const totalPages = Math.ceil(total / Math.max(1, effectivePageSize));
        if ((total <= DOMESTIC_SEGMENT_LIMIT) && (totalPages <= DOMESTIC_MAX_PAGES)) {
            const segment = {
                searchValue,
                total,
                totalPages,
                firstPayload: { ...payload, pageSize: effectivePageSize },
                order: segmentIndex,
            };
            segmentIndex += 1;
            logger.info(`${searchValue}: ${total} 条，使用当前检索段（共 ${totalPages} 页）`);
            if (onSegment) {
                await onSegment(segment);
            }
            return;
        }

        if (depth + 1 > DOMESTIC_MAX_SEGMENT_DEPTH) {
            throw new Error(`${searchValue}: 拆分深度已达 ${DOMESTIC_MAX_SEGMENT_DEPTH} 仍超过 ${DOMESTIC_MAX_PAGES} 页，请调整 NMPA_SEGMENT_DIGITS 或提高 NMPA_DOMESTIC_MAX_SEGMENT_DEPTH`);
        }

        logger.info(`${searchValue}: ${total} 条，继续细分`);
        const nextDepth = depth + 1;
        let hasChild = false;
        for (const digit of SEGMENT_DIGITS) {
            hasChild = true;
            await split(`${searchValue}${digit}`, nextDepth);
        }
        if (!hasChild) {
            throw new Error(`${searchValue}: SEGMENT_DIGITS 为空无法继续拆分，请调整 NMPA_SEGMENT_DIGITS`);
        }
    }

    await split(baseSearch, 0);
    return segmentIndex;
}

async function fetchDetailsBatch(page, itemId, recordIds, concurrency = DETAIL_CONCURRENCY) {
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
                    window.getUrl = window.getUrl || (() => '');
                    const raw = await window.pajax.hasTokenGet(window.api.queryDetail, {
                        id,
                        itemId,
                        isSenior: 'N',
                    });
                    const detail = raw?.data?.data?.detail ?? raw?.data?.detail ?? raw?.detail ?? null;
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
}

async function fetchDetailWithRetry(page, itemId, id, retries = DETAIL_RETRY_LIMIT) {
    for (let attempt = 0; attempt <= retries; attempt++) {
        try {
            const result = await page.evaluate(async (params) => {
                window.getUrl = window.getUrl || (() => '');
                const raw = await window.pajax.hasTokenGet(window.api.queryDetail, {
                    id: params.id,
                    itemId: params.itemId,
                    isSenior: 'N',
                });
                return raw?.data?.data?.detail ?? raw?.data?.detail ?? raw?.detail ?? null;
            }, { itemId, id });

            if (result) {
                return result;
            }
        } catch (error) {
            if (attempt === retries) {
                throw error;
            }
        }
        await sleep(800 * (attempt + 1));
    }
    return null;
}

async function crawlDomesticSegment(controller, segment, { prefix, logger }) {
    const segmentDir = path.join(OUTPUT_ROOT, segment.searchValue);
    await fsExtra.ensureDir(segmentDir);
    await fsExtra.emptyDir(segmentDir);

    let pageNum = 1;
    let payload = segment.firstPayload;
    let totalWritten = 0;
    let batchIndex = 0;
    let pagesInBatch = 0;
    let stream = null;
    let rotationRecoveries = 0;
    let consecutiveDetailFailures = 0;
    const seenCodes = new Set();

    const openBatch = async () => {
        batchIndex += 1;
        pagesInBatch = 0;
        const filename = `${segment.searchValue}_${String(batchIndex).padStart(3, '0')}.jsonl`;
        const filePath = path.join(segmentDir, filename);
        stream = fs.createWriteStream(filePath, { flags: 'w', encoding: 'utf8' });
        logger.info(`${segment.searchValue}: 开始批次 #${batchIndex}，输出 ${path.relative(process.cwd(), filePath)}`);
    };

    const closeBatch = async () => {
        if (!stream) return;
        stream.end();
        await once(stream, 'finish');
        logger.info(`${segment.searchValue}: 批次 #${batchIndex} 写入完成，当前累计 ${totalWritten} 条`);
        stream = null;
    };

    try {
        while (pageNum <= segment.totalPages) {
            const page = await controller.getPage();

            if (!payload) {
                await sleepRange(PAGE_DELAY_RANGE);
                try {
                    payload = await fetchListPage(page, { itemId: DOMESTIC_ITEM_ID, searchValue: segment.searchValue, pageNum, pageSize: REQUEST_PAGE_SIZE });
                    rotationRecoveries = 0;
                } catch (error) {
                    const canRotate = controller.sequence.length > 1
                        && shouldRotateForListError(error)
                        && rotationRecoveries < controller.sequence.length * 3;
                    if (canRotate) {
                        rotationRecoveries += 1;
                        logger.warning(`${segment.searchValue}: 第 ${pageNum} 页列表请求异常(${error.message || error})，尝试切换浏览器重试`);
                        await controller.rotateBrowser(`${segment.searchValue}: 列表请求异常，尝试新浏览器`);
                        payload = null;
                        continue;
                    }
                    throw error;
                }
            }

            const records = payload.list || [];
            if (!records.length) break;

            if (!stream) await openBatch();

            const ids = records.map((item) => item.f4).filter(Boolean);
            if (DETAIL_BATCH_DELAY_MS > 0) await sleep(DETAIL_BATCH_DELAY_MS);
            const batchDetails = await fetchDetailsBatch(page, DOMESTIC_ITEM_ID, ids);
            let pageSuccessCount = 0;

            for (let index = 0; index < ids.length; index++) {
                const id = ids[index];
                let detailEntry = batchDetails[index];
                if (!detailEntry || !detailEntry.success || !detailEntry.detail) {
                    try {
                        const recovered = await fetchDetailWithRetry(page, DOMESTIC_ITEM_ID, id);
                        if (!recovered) {
                            logger.warning(`${segment.searchValue}: 无法获取记录 ${id} 详情，已跳过`);
                            continue;
                        }
                        detailEntry = { detail: recovered, success: true };
                    } catch (error) {
                        logger.warning(`${segment.searchValue}: 重试记录 ${id} 详情失败: ${error.message}`);
                        continue;
                    }
                }

                const detail = detailEntry.detail;
                if (!detail?.f0 || !detail.f0.startsWith(prefix)) continue;

                const record = {
                    code: detail.f0 || '',
                    zh: detail.f1 || '',
                    en: detail.f2 || '',
                };

                if (seenCodes.has(record.code)) continue;
                seenCodes.add(record.code);

                await writeJsonLine(stream, record);
                totalWritten += 1;
                pageSuccessCount += 1;
                await sleepRange(RECORD_DELAY_RANGE);
            }

            const successRatio = pageSuccessCount / Math.max(1, ids.length);

            if (successRatio < DETAIL_SUCCESS_MIN_RATIO) {
                consecutiveDetailFailures += 1;
                logger.warning(`${segment.searchValue}: 第 ${pageNum} 页详情成功率 ${(successRatio * 100).toFixed(1)}%，尝试切换浏览器重试（连续 ${consecutiveDetailFailures} 页低于阈值）`);
                const marked = controller.markCurrentBrowserUnhealthy('连续详情抓取失败');
                if (marked || controller.sequence.length > 1) {
                    await controller.rotateBrowser(`${segment.searchValue}: 连续详情失败`);
                } else {
                    await sleep(15000);
                }
                payload = null;
                continue;
            } else {
                consecutiveDetailFailures = 0;
            }

            if (pageNum % PAGE_LOG_INTERVAL === 0 || pageNum === segment.totalPages) {
                logger.info(`${segment.searchValue}: 已完成第 ${pageNum}/${segment.totalPages} 页，段累计写入 ${totalWritten} 条`);
            }

            pageNum += 1;
            payload = null;
            pagesInBatch += 1;

            if (BROWSER_PAGE_BATCH > 0 && pagesInBatch >= BROWSER_PAGE_BATCH && pageNum <= segment.totalPages) {
                await closeBatch();
                await controller.rotateBrowser(`${segment.searchValue}: 已抓取 ${pageNum - 1} 页`);
                pagesInBatch = 0;
            }
        }
    } finally {
        await closeBatch();
    }

    logger.info(`${segment.searchValue}: 段抓取完成，总写入 ${totalWritten} 条，批次数 ${batchIndex}`);
}

async function crawlDomesticCategory(controller, { baseSearch, prefix, label }, logger) {
    await fsExtra.ensureDir(OUTPUT_ROOT);
    let processed = 0;

    await processDomesticSegments(controller, baseSearch, logger, async (segment) => {
        if (controller.sequence.length > 1) {
            await controller.rotateBrowser(`${segment.searchValue}: 使用当前检索段，准备切换浏览器`);
        }
        await crawlDomesticSegment(controller, segment, { prefix, logger });
        processed += 1;
        await sleepRange(SEGMENT_PAUSE_RANGE);
    });

    if (processed === 0) {
        logger.info(`${label ?? baseSearch}: 未找到可抓取的段`);
    } else {
        logger.info(`${label ?? baseSearch}: 共处理 ${processed} 个检索段`);
    }
}

async function crawlImported(page, logger) {
    await fsExtra.ensureDir(OUTPUT_ROOT);
    const outputPathH = path.join(OUTPUT_ROOT, '进口H.jsonl');
    const outputPathS = path.join(OUTPUT_ROOT, '进口S.jsonl');
    const streamH = fs.createWriteStream(outputPathH, { flags: 'w', encoding: 'utf8' });
    const streamS = fs.createWriteStream(outputPathS, { flags: 'w', encoding: 'utf8' });

    let totalPages = null;
    let pageNum = 1;
    let writtenH = 0;
    let writtenS = 0;

    try {
        while (true) {
            if (pageNum > 1) await sleepRange(PAGE_DELAY_RANGE);
            const payload = await fetchListPage(page, { itemId: IMPORTED_ITEM_ID, searchValue: '国药准字', pageNum, pageSize: REQUEST_PAGE_SIZE });
            const records = payload.list || [];
            if (!records.length) break;

            if (totalPages === null) {
                const effectivePageSize = payload.pageSize || REQUEST_PAGE_SIZE;
                totalPages = Math.ceil((payload.total || records.length) / Math.max(1, effectivePageSize));
                logger.info(`进口药品: 计划抓取 ${payload.total || records.length} 条数据，共 ${totalPages} 页`);
            }

            const ids = records.map((item) => item.f3).filter(Boolean);
            if (DETAIL_BATCH_DELAY_MS > 0) await sleep(DETAIL_BATCH_DELAY_MS);
            const batchDetails = await fetchDetailsBatch(page, IMPORTED_ITEM_ID, ids, 2);

            for (let index = 0; index < ids.length; index++) {
                const id = ids[index];
                let detailEntry = batchDetails[index];
                if (!detailEntry || !detailEntry.success || !detailEntry.detail) {
                    try {
                        const recovered = await fetchDetailWithRetry(page, IMPORTED_ITEM_ID, id, DETAIL_RETRY_LIMIT + 1);
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

            if (pageNum % PAGE_LOG_INTERVAL === 0 || pageNum === totalPages) {
                logger.info(`进口药品: 已完成第 ${pageNum}/${totalPages ?? '?'} 页，累计 H=${writtenH}, S=${writtenS}`);
            }

            pageNum += 1;
        }
    } finally {
        streamH.end();
        streamS.end();
        await Promise.all([once(streamH, 'finish'), once(streamS, 'finish')]);
        logger.info(`进口药品: 写入完成，H=${writtenH} (${path.relative(process.cwd(), outputPathH)}), S=${writtenS} (${path.relative(process.cwd(), outputPathS)})`);
    }
}

async function navigateToSearch(page) {
    await page.goto(SEARCH_URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForFunction(() => window.api && window.pajax && window.itemFileUrl, { timeout: 60000 });
}

async function handleDatasetRequest(page, datasetKey, logger = crawlerLog, context = {}) {
    if (datasetKey === 'domestic-h' || datasetKey === 'domestic-s') {
        const baseSearch = datasetKey === 'domestic-h' ? '国药准字H' : '国药准字S';
        const controller = new BrowserController({
            initialPage: page,
            logger,
            proxy: context.proxy,
            browserArgs: PLAYWRIGHT_ARGS,
            swapDelayMs: BROWSER_SWAP_DELAY_MS,
            sequence: BROWSER_SEQUENCE,
        });
        await controller.initialize();
        try {
            await crawlDomesticCategory(controller, { baseSearch, prefix: baseSearch, label: context.label }, logger);
        } finally {
            await controller.dispose();
        }
    } else if (datasetKey === 'imported') {
        await navigateToSearch(page);
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

    const rawProxy = process.env.NMPA_PROXY || process.env.HTTPS_PROXY || process.env.HTTP_PROXY || process.env.ALL_PROXY;
    const proxy = parseProxyUrl(rawProxy);

    const crawler = new PlaywrightCrawler({
        headless: true,
        maxConcurrency: 1,
        requestHandlerTimeoutSecs: 7200,
        navigationTimeoutSecs: 120,
        maxRequestsPerCrawl: datasetKeys.length,
        launchContext: {
            launchOptions: {
                executablePath,
                args: PLAYWRIGHT_ARGS,
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
            await handleDatasetRequest(page, datasetKey, logger, { proxy, label: request.userData.label });
        },
    });

    const requests = datasetKeys.map((datasetKey) => ({
        url: SEARCH_URL,
        userData: {
            datasetKey,
            label: datasetKey === 'domestic-h'
                ? '国内H'
                : datasetKey === 'domestic-s'
                    ? '国内S'
                    : datasetKey === 'imported'
                        ? '进口药品'
                        : datasetKey,
        },
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
