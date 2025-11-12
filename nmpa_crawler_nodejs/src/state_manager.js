import fs from 'fs';
import fsExtra from 'fs-extra';
import path from 'path';

const OUTPUT_ROOT = path.resolve('outputs');
const RUNS_ROOT = path.join(OUTPUT_ROOT, 'runs');
const STATE_DIR = path.join(OUTPUT_ROOT, 'state');
const CURRENT_RUN_FILE = path.join(STATE_DIR, 'current_run.json');

function formatTimestamp(date = new Date()) {
    const pad = (value) => `${value}`.padStart(2, '0');
    const year = date.getFullYear();
    const month = pad(date.getMonth() + 1);
    const day = pad(date.getDate());
    const hour = pad(date.getHours());
    const minute = pad(date.getMinutes());
    const second = pad(date.getSeconds());
    return `${year}${month}${day}_${hour}${minute}${second}`;
}

function defaultDatasetInfo(datasetKey, runDir) {
    const datasetsDir = path.join(runDir, 'datasets');
    const outputFileMap = {
        'domestic-h': 'domestic-h.jsonl',
        'domestic-s': 'domestic-s.jsonl',
        'imported-h': 'imported-h.jsonl',
        'imported-s': 'imported-s.jsonl',
        imported: 'imported.jsonl',
    };
    const mapped = outputFileMap[datasetKey] || `${datasetKey}.jsonl`;
    return {
        datasetKey,
        outputPath: path.join(datasetsDir, mapped),
        segments: {},
        written: 0,
        status: 'pending',
        lastUpdated: null,
        notes: [],
    };
}

function ensureDirectory(targetPath) {
    fsExtra.ensureDirSync(targetPath);
}

class StateManager {
    static async createInitial(config) {
        ensureDirectory(RUNS_ROOT);
        ensureDirectory(STATE_DIR);
        const runId = config.runId || formatTimestamp();
        const runDir = path.join(RUNS_ROOT, runId);
        const datasetsDir = path.join(runDir, 'datasets');
        ensureDirectory(runDir);
        ensureDirectory(datasetsDir);

        const initialState = {
            runId,
            status: 'running',
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            config: {
                datasets: config.datasets || [],
                pageSize: config.pageSize,
                maxPages: config.maxPages,
                concurrency: config.concurrency,
                useProxy: config.useProxy,
                proxyList: config.proxyList,
                additional: config.additional || {},
            },
            paths: {
                runDir,
                datasetsDir,
                stateFile: path.join(runDir, 'run_state.json'),
                summaryFile: path.join(runDir, 'run_summary.json'),
            },
            datasets: {},
            proxy: {
                currentIndex: 0,
                history: [],
            },
            errors: [],
            notes: [],
        };

        const manager = new StateManager(initialState);
        await manager.save();
        await fsExtra.ensureDir(STATE_DIR);
        await fsExtra.writeJson(CURRENT_RUN_FILE, { runId }, { spaces: 2 });
        return manager;
    }

    static async load(runId) {
        const stateFile = path.join(RUNS_ROOT, runId, 'run_state.json');
        if (!await fsExtra.pathExists(stateFile)) {
            throw new Error(`未找到运行状态文件: ${stateFile}`);
        }
        const state = await fsExtra.readJson(stateFile);
        return new StateManager(state);
    }

    constructor(state) {
        this.state = state;
    }

    get runId() {
        return this.state.runId;
    }

    get runDir() {
        return this.state.paths.runDir;
    }

    get datasetsDir() {
        return this.state.paths.datasetsDir;
    }

    get config() {
        return this.state.config;
    }

    get status() {
        return this.state.status;
    }

    set status(value) {
        this.state.status = value;
        this.touch();
    }

    touch() {
        this.state.updatedAt = new Date().toISOString();
    }

    async save() {
        this.touch();
        await fsExtra.ensureDir(this.runDir);
        await fsExtra.writeJson(this.state.paths.stateFile, this.state, { spaces: 2 });
    }

    getDataset(datasetKey) {
        if (!this.state.datasets[datasetKey]) {
            this.state.datasets[datasetKey] = defaultDatasetInfo(datasetKey, this.runDir);
        }
        return this.state.datasets[datasetKey];
    }

    setDatasetStatus(datasetKey, status, note) {
        const dataset = this.getDataset(datasetKey);
        dataset.status = status;
        dataset.lastUpdated = new Date().toISOString();
        if (note) dataset.notes.push({ timestamp: dataset.lastUpdated, note });
    }

    getSegment(datasetKey, segmentKey) {
        const dataset = this.getDataset(datasetKey);
        if (!dataset.segments[segmentKey]) {
            dataset.segments[segmentKey] = {
                segmentKey,
                status: 'pending',
                total: null,
                totalPages: null,
                nextPage: 1,
                processedPages: [],
                written: 0,
                lastUpdated: null,
                notes: [],
            };
        }
        return dataset.segments[segmentKey];
    }

    initSegment(datasetKey, segmentInfo) {
        const segment = this.getSegment(datasetKey, segmentInfo.segmentKey);
        segment.total = segmentInfo.total;
        segment.totalPages = segmentInfo.totalPages;
        segment.status = segment.status === 'completed' ? 'completed' : 'pending';
        if (!segment.firstSeenAt) segment.firstSeenAt = new Date().toISOString();
        segment.lastUpdated = new Date().toISOString();
        this.setDatasetStatus(datasetKey, 'running');
    }

    markSegmentInProgress(datasetKey, segmentKey, pageNum) {
        const segment = this.getSegment(datasetKey, segmentKey);
        segment.status = 'in-progress';
        segment.currentPage = pageNum;
        segment.lastUpdated = new Date().toISOString();
    }

    recordPageResult(datasetKey, segmentKey, pageNum, writtenCount) {
        const dataset = this.getDataset(datasetKey);
        const segment = this.getSegment(datasetKey, segmentKey);
        if (!segment.processedPages.includes(pageNum)) {
            segment.processedPages.push(pageNum);
        }
        segment.nextPage = pageNum + 1;
        segment.written += writtenCount;
        segment.lastUpdated = new Date().toISOString();
        dataset.written += writtenCount;
        dataset.lastUpdated = new Date().toISOString();
    }

    markSegmentFailed(datasetKey, segmentKey, reason) {
        const segment = this.getSegment(datasetKey, segmentKey);
        segment.status = 'failed';
        segment.lastUpdated = new Date().toISOString();
        if (reason) segment.notes.push({ timestamp: segment.lastUpdated, note: reason });
        this.touch();
    }

    markSegmentCompleted(datasetKey, segmentKey) {
        const segment = this.getSegment(datasetKey, segmentKey);
        segment.status = 'completed';
        segment.lastUpdated = new Date().toISOString();
        this.touch();
    }

    getPendingDatasets() {
        const keys = Object.keys(this.state.datasets);
        if (keys.length === 0) {
            return this.state.config.datasets || [];
        }
        return keys.filter((key) => this.state.datasets[key].status !== 'completed');
    }

    getPendingSegments(datasetKey, segmentKeys) {
        return segmentKeys.filter((segmentKey) => {
            const segment = this.getSegment(datasetKey, segmentKey);
            return segment.status !== 'completed';
        });
    }

    markDatasetCompleted(datasetKey) {
        this.setDatasetStatus(datasetKey, 'completed');
    }

    areAllDatasetsCompleted() {
        const datasetKeys = Object.keys(this.state.datasets);
        if (datasetKeys.length === 0) return false;
        return datasetKeys.every((key) => this.state.datasets[key].status === 'completed');
    }

    recordError(error, context = {}) {
        const entry = {
            timestamp: new Date().toISOString(),
            message: error?.message || String(error),
            name: error?.name || 'Error',
            context,
        };
        this.state.errors.push(entry);
    }

    recordNote(note, context = {}) {
        this.state.notes.push({
            timestamp: new Date().toISOString(),
            note,
            context,
        });
    }

    setProxyIndex(index, proxyInfo) {
        this.state.proxy.currentIndex = index;
        this.state.proxy.history.push({
            timestamp: new Date().toISOString(),
            index,
            proxy: proxyInfo,
        });
    }

    getProxyIndex() {
        return this.state.proxy.currentIndex || 0;
    }

    getProxyHistory() {
        return this.state.proxy.history || [];
    }

    summarize() {
        const datasets = Object.values(this.state.datasets).map((dataset) => ({
            datasetKey: dataset.datasetKey,
            status: dataset.status,
            written: dataset.written,
            segments: Object.values(dataset.segments).map((segment) => ({
                segmentKey: segment.segmentKey,
                status: segment.status,
                written: segment.written,
                nextPage: segment.nextPage,
                total: segment.total,
                totalPages: segment.totalPages,
            })),
        }));
        return {
            runId: this.runId,
            status: this.state.status,
            updatedAt: this.state.updatedAt,
            datasets,
            errors: this.state.errors,
            proxyHistory: this.getProxyHistory(),
        };
    }
}

export { StateManager, formatTimestamp, RUNS_ROOT, CURRENT_RUN_FILE };
