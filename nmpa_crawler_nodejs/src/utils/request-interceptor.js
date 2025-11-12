// 请求拦截器 - 基于Python ultimate_solution.py的逻辑
import NMPASignatureCracker from './signature-cracker.js';

export class RequestInterceptor {
    constructor() {
        this.signatureCracker = new NMPASignatureCracker();
        this.capturedRequests = [];
        this.signCache = new Map();
        this.baseUrl = 'https://www.nmpa.gov.cn';
    }

    /**
     * 拦截请求（模拟Python版本的_capture_request）
     */
    captureRequest(request, response) {
        if (request.url().includes('/datasearch/data/nmpadata/search')) {
            const requestData = {
                url: request.url(),
                method: request.method(),
                headers: request.headers(),
                postData: request.postData(),
                timestamp: Date.now()
            };

            this.capturedRequests.push(requestData);

            // 解析URL参数
            const url = new URL(request.url());
            const params = {};
            url.searchParams.forEach((value, key) => {
                params[key] = value;
            });

            // 缓存签名信息
            const searchKey = params.searchValue || '';
            const pageNum = params.pageNum || '1';
            const cacheKey = `${searchKey}_${pageNum}`;

            if (params.sign) {
                this.signCache.set(cacheKey, {
                    sign: params.sign,
                    timestamp: params.timestamp || '',
                    fullParams: { ...params },
                    capturedAt: Date.now()
                });

                console.log(`🔐 捕获签名: ${cacheKey} -> ${params.sign.substring(0, 16)}...`);
                console.log(`   完整参数:`, params);
            }

            return requestData;
        }
        return null;
    }

    /**
     * 拦截响应（模拟Python版本的_capture_response）
     */
    captureResponse(request, response) {
        if (request.url().includes('/datasearch/data/nmpadata/search')) {
            try {
                const responseData = response.body();

                if (responseData) {
                    // 尝试解析JSON
                    let data;
                    try {
                        data = JSON.parse(responseData);
                    } catch (e) {
                        console.log('响应不是有效JSON:', responseData.substring(0, 100));
                        return null;
                    }

                    if (data.code === 200) {
                        const listCount = data.data?.list?.length || 0;
                        console.log(`✅ 成功响应: ${listCount} 条数据`);

                        return {
                            success: true,
                            data: data,
                            listCount: listCount,
                            totalRecords: data.data?.total || 0
                        };
                    }
                }
            } catch (error) {
                console.log('响应解析失败:', error.message);
            }
        }
        return null;
    }

    /**
     * 获取缓存的签名
     */
    getCachedSignature(searchValue, pageNum = '1') {
        const cacheKey = `${searchValue}_${pageNum}`;
        const cached = this.signCache.get(cacheKey);

        if (cached && Date.now() - cached.capturedAt < 300000) { // 5分钟有效期
            console.log(`✅ 使用缓存签名: ${cached.sign.substring(0, 16)}...`);
            return cached;
        }

        return null;
    }

    /**
     * 清理过期的缓存
     */
    cleanExpiredCache() {
        const now = Date.now();
        const expiredKeys = [];

        for (const [key, value] of this.signCache.entries()) {
            if (now - value.capturedAt > 300000) { // 5分钟过期
                expiredKeys.push(key);
            }
        }

        expiredKeys.forEach(key => {
            this.signCache.delete(key);
        });

        if (expiredKeys.length > 0) {
            console.log(`🧹 清理了 ${expiredKeys.length} 个过期签名缓存`);
        }
    }

    /**
     * 获取所有捕获的请求
     */
    getCapturedRequests() {
        return [...this.capturedRequests];
    }

    /**
     * 获取签名统计信息
     */
    getSignatureStats() {
        const stats = {
            totalCaptured: this.capturedRequests.length,
            cachedSignatures: this.signCache.size,
            uniqueSearchTerms: new Set(),
            algorithms: new Map()
        };

        // 统计唯一搜索词
        for (const [key, value] of this.signCache.entries()) {
            stats.uniqueSearchTerms.add(key.split('_')[0]);
        }

        // 统计算法使用情况
        for (const request of this.capturedRequests) {
            const url = new URL(request.url);
            const params = {};
            url.searchParams.forEach((value, key) => {
                params[key] = value;
            });

            if (params.sign) {
                // 尝试识别算法类型（简化版）
                if (params.sign.length === 32) {
                    stats.algorithms.set('MD5', (stats.algorithms.get('MD5') || 0) + 1);
                } else if (params.sign.length === 64) {
                    stats.algorithms.set('SHA256', (stats.algorithms.get('SHA256') || 0) + 1);
                } else if (params.sign.length > 64) {
                    stats.algorithms.set('BASE64', (stats.algorithms.get('BASE64') || 0) + 1);
                }
            }
        }

        return {
            ...stats,
            uniqueSearchTerms: stats.uniqueSearchTerms.size,
            algorithms: Object.fromEntries(stats.algorithms)
        };
    }

    /**
     * 导出捕获的数据
     */
    exportCapturedData() {
        return {
            requests: this.capturedRequests,
            signatures: Object.fromEntries(this.signCache),
            stats: this.getSignatureStats(),
            exportedAt: new Date().toISOString()
        };
    }

    /**
     * 重置所有数据
     */
    reset() {
        this.capturedRequests = [];
        this.signCache.clear();
        console.log('🔄 请求拦截器已重置');
    }
}

export default RequestInterceptor;