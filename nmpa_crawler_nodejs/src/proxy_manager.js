function normalizeProxyEntry(entry) {
    if (!entry) return null;
    if (entry === 'direct' || entry === 'DIRECT' || entry === 'local') {
        return { label: 'direct', url: null, type: 'direct' };
    }
    const trimmed = entry.trim();
    return { label: trimmed, url: trimmed, type: 'http' };
}

class ProxyManager {
    constructor(stateManager, options = {}) {
        this.stateManager = stateManager;
        const envList = process.env.NMPA_PROXY_LIST || process.env.NMPA_PROXY_POOL || '';
        const envSingle = process.env.NMPA_PROXY || '';
        const allowDirect = process.env.NMPA_PROXY_ALLOW_DIRECT === 'true' || options.allowDirect;

        const rawEntries = [];
        if (envList) rawEntries.push(...envList.split(',').map((value) => value.trim()).filter(Boolean));
        if (envSingle && !rawEntries.length) rawEntries.push(envSingle.trim());

        const proxyEntries = rawEntries.map(normalizeProxyEntry).filter(Boolean);
        if ((allowDirect || !proxyEntries.length) && !proxyEntries.some((item) => item?.type === 'direct')) {
            proxyEntries.push({ label: 'direct', url: null, type: 'direct' });
        }

        this.proxies = proxyEntries;
        this.currentIndex = stateManager?.getProxyIndex?.() ?? 0;
        if (this.proxies.length === 0) {
            this.proxies = [{ label: 'direct', url: null, type: 'direct' }];
        }
        this.maxRotations = Number(process.env.NMPA_PROXY_MAX_ROTATIONS || 20);
        this.rotateDelayMs = Number(process.env.NMPA_PROXY_ROTATE_DELAY_MS || 3000);
        this.rotationCount = 0;
    }

    getCurrent() {
        const index = Math.max(0, Math.min(this.currentIndex, this.proxies.length - 1));
        const proxy = this.proxies[index];
        return { ...proxy, index };
    }

    async rotate(reason = 'manual', context = {}) {
        if (this.proxies.length <= 1) {
            this.rotationCount += 1;
            return this.getCurrent();
        }
        this.rotationCount += 1;
        if (this.maxRotations && this.rotationCount > this.maxRotations) {
            throw new Error('代理轮换次数超过限制');
        }
        this.currentIndex = (this.currentIndex + 1) % this.proxies.length;
        const nextProxy = this.getCurrent();
        if (this.stateManager?.setProxyIndex) {
            this.stateManager.setProxyIndex(this.currentIndex, {
                ...nextProxy,
                reason,
                context,
                rotatedAt: new Date().toISOString(),
            });
            await this.stateManager.save();
        }
        if (this.rotateDelayMs > 0) {
            await new Promise((resolve) => setTimeout(resolve, this.rotateDelayMs));
        }
        return nextProxy;
    }

    shouldRotateForError(error) {
        if (!error) return false;
        const message = error.message || '';
        const blockedKeywords = [
            'Request failed with status code 400',
            'Request failed with status code 403',
            'Request failed with status code 412',
            'Timeout 30000ms exceeded',
            'Timeout 60000ms exceeded',
            'page.waitForFunction: Timeout',
            'Navigation timeout',
            '首页访问失败',
            '搜索页返回',
            'net::ERR_TIMED_OUT',
            'net::ERR_PROXY_CONNECTION_FAILED',
            'net::ERR_TUNNEL_CONNECTION_FAILED',
        ];
        if (blockedKeywords.some((keyword) => message.includes(keyword))) return true;
        const contextType = error?.context?.type;
        if (contextType && ['navigation', 'navigation-home', 'navigation-search'].includes(contextType)) return true;
        return false;
    }

    hasMultiple() {
        return this.proxies.length > 1;
    }

    getProxies() {
        return this.proxies;
    }
}

export { ProxyManager };
