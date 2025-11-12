// NMPA签名算法破解器 - JavaScript版本
// 基于 nmpa_crawler/ultimate_solution.py 和 sign_cracker.py 的逻辑
import CryptoJS from 'crypto-js';
import { v4 as uuidv4 } from 'uuid';

export class NMPASignatureCracker {
    constructor() {
        // 从Python版本迁移的密钥
        this.secretKeys = [
            "nmpa2024secretkey",
            "nmpa_data_search_key",
            "NMPA_WEB_ENCRYPT_KEY",
            "search_nmpa_encrypt"
        ];

        this.secretKey = this.secretKeys[0]; // 默认密钥
        this.deviceId = this.generateDeviceId();
        this.signCache = new Map(); // 签名缓存
    }

    /**
     * 生成设备ID
     */
    generateDeviceId() {
        const timestamp = Date.now().toString();
        const randomStr = Math.random().toString(36).substring(2, 10);
        return `${timestamp}_${randomStr}`;
    }

    /**
     * 生成随机nonce
     */
    generateNonce() {
        return Math.random().toString(36).substring(2, 18);
    }

    /**
     * 签名算法版本1 - 基础MD5签名
     * 对应Python的crack_sign_v1
     */
    crackSignV1(url, params) {
        const timestamp = Date.now().toString();
        params.timestamp = timestamp;

        // 参数排序
        const sortedParams = this.sortParams(params);

        // 构建签名字符串
        const paramStr = Object.entries(sortedParams)
            .map(([k, v]) => `${k}=${v}`)
            .join('&');
        const signStr = `${paramStr}&key=${this.secretKey}`;

        // 生成签名
        const sign = CryptoJS.MD5(signStr).toString();

        return {
            sign: sign,
            timestamp: timestamp,
            nonce: this.generateNonce(),
            algorithm: 'MD5-V1'
        };
    }

    /**
     * 签名算法版本2 - HMAC-SHA256签名
     * 对应Python的crack_sign_v2
     */
    crackSignV2(url, params) {
        const timestamp = Date.now().toString();
        params.timestamp = timestamp;
        params.deviceId = this.deviceId;

        // 参数排序和编码
        const sortedParams = this.sortParams(params);
        const paramStr = Object.entries(sortedParams)
            .map(([k, v]) => `${k}=${encodeURIComponent(v)}`)
            .join('&');

        // 使用HMAC-SHA256生成签名
        const urlPath = new URL(url).pathname;
        const signData = `GET\n${urlPath}\n${paramStr}`;
        const sign = CryptoJS.HmacSHA256(signData, this.secretKey).toString();

        return {
            sign: sign,
            timestamp: timestamp,
            deviceId: this.deviceId,
            nonce: this.generateNonce(),
            algorithm: 'HMAC-SHA256-V2'
        };
    }

    /**
     * 签名算法版本3 - AES加密签名
     * 对应Python的crack_sign_v3
     */
    crackSignV3(url, params) {
        const timestamp = Date.now().toString();
        const nonce = this.generateNonce();

        // 构建待加密数据
        const encryptData = {
            url: url,
            params: params,
            timestamp: timestamp,
            nonce: nonce,
            deviceId: this.deviceId
        };

        // 加密数据
        const encryptStr = JSON.stringify(encryptData, Object.keys(encryptData).sort());
        const encryptedData = this.aesEncrypt(encryptStr);

        // 生成签名
        const signData = `${encryptedData}${this.secretKey}${timestamp}`;
        const sign = CryptoJS.SHA256(signData).toString();

        return {
            sign: sign,
            timestamp: timestamp,
            nonce: nonce,
            deviceId: this.deviceId,
            encData: encryptedData,
            algorithm: 'AES-SHA256-V3'
        };
    }

    /**
     * 签名算法版本4 - 复合签名算法
     * 对应Python的crack_sign_v4，最高安全级别
     */
    crackSignV4(url, params) {
        const timestamp = Date.now().toString();
        const nonce = this.generateNonce();

        // 第一层：参数处理
        const processedParams = { ...params };
        processedParams.timestamp = timestamp;
        processedParams.nonce = nonce;
        processedParams.deviceId = this.deviceId;

        // 第二层：构建基础签名字符串
        const sortedParams = this.sortParams(processedParams);
        const baseStr = JSON.stringify(sortedParams, Object.keys(sortedParams).sort());

        // 第三层：多重哈希
        const hash1 = CryptoJS.MD5(baseStr + this.secretKey).toString();
        const hash2 = CryptoJS.SHA256(hash1 + timestamp).toString();
        const hash3 = CryptoJS.MD5(hash2 + nonce).toString();

        // 第四层：Base64编码
        const finalSign = CryptoJS.enc.Base64.stringify(CryptoJS.enc.Utf8.parse(hash3));

        return {
            sign: finalSign,
            timestamp: timestamp,
            nonce: nonce,
            deviceId: this.deviceId,
            hashCode: hash3.substring(0, 16), // 前16位作为校验码
            algorithm: 'COMPOSITE-V4'
        };
    }

    /**
     * 基于真实请求分析的签名算法
     * 根据你提供的真实curl请求分析
     */
    crackSignReal(url, params) {
        const timestamp = Date.now().toString();
        params.timestamp = timestamp;

        // 基于观察到的真实请求模式
        const itemId = params.itemId || 'ff80808183cad75001840881f848179f';

        // 策略1: 固定格式MD5（最可能）
        const fixedFormat = `itemId=${itemId}&isSenior=${params.isSenior || 'N'}&searchValue=${params.searchValue}&pageNum=${params.pageNum}&pageSize=${params.pageSize}&timestamp=${timestamp}`;
        const sign1 = CryptoJS.MD5(fixedFormat).toString();

        // 策略2: 参数排序 + 时间戳
        const sortedParams = this.sortParams(params);
        const sortedStr = Object.entries(sortedParams)
            .map(([k, v]) => `${k}=${v}`)
            .join('&');
        const sign2 = CryptoJS.MD5(sortedStr + timestamp).toString();

        // 策略3: 时间戳优先
        const sign3 = CryptoJS.MD5(timestamp + sortedStr).toString();

        // 策略4: 基于itemId的特殊处理
        const sign4 = CryptoJS.MD5(`${itemId}_${params.searchValue}_${timestamp}`).toString();

        // 返回最可能的签名（基于真实请求测试）
        return {
            sign: sign1, // 默认使用策略1
            alternatives: [sign2, sign3, sign4],
            timestamp: timestamp,
            algorithms: ['FIXED_FORMAT', 'SORTED_PARAMS', 'TIMESTAMP_FIRST', 'ITEMID_SPECIAL'],
            algorithm: 'REAL_ANALYSIS'
        };
    }

    /**
     * AES加密（简化版）
     */
    aesEncrypt(text) {
        // 简化的AES加密（实际使用中可能需要更复杂的实现）
        const key = this.secretKey.substring(0, 16).padEnd(16, '0');
        const encrypted = CryptoJS.AES.encrypt(text, CryptoJS.enc.Utf8.parse(key), {
            mode: CryptoJS.mode.ECB,
            padding: CryptoJS.pad.Pkcs7
        });
        return encrypted.toString();
    }

    /**
     * 参数排序
     */
    sortParams(params) {
        const sorted = {};
        Object.keys(params).sort().forEach(key => {
            sorted[key] = params[key];
        });
        return sorted;
    }

    /**
     * 自动检测并破解签名
     * 根据URL特征自动选择合适的签名算法
     */
    autoDetectAndCrack(url, params) {
        // 根据URL路径判断签名版本
        if (url.includes('/search')) {
            // 搜索接口使用基于真实请求分析的算法
            return this.crackSignReal(url, params);
        } else if (url.includes('/queryDetail')) {
            // 详情查询使用v3签名
            return this.crackSignV3(url, params);
        } else if (url.includes('/config/')) {
            // 配置接口使用v1签名
            return this.crackSignV1(url, params);
        } else {
            // 默认使用最安全的v4签名
            return this.crackSignV4(url, params);
        }
    }

    /**
     * 生成完整的请求头
     */
    generateHeaders(url, params) {
        const signData = this.autoDetectAndCrack(url, params);

        const headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.nmpa.gov.cn/datasearch/search-result.html',
            'Origin': 'https://www.nmpa.gov.cn',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"'
        };

        // 添加签名相关头部
        if (signData.timestamp) {
            headers['timestamp'] = signData.timestamp;
        }
        if (signData.sign) {
            headers['sign'] = signData.sign;
        }
        if (signData.deviceId) {
            headers['deviceId'] = signData.deviceId;
        }
        if (signData.nonce) {
            headers['nonce'] = signData.nonce;
        }
        if (signData.token !== undefined) {
            headers['token'] = signData.token || 'false';
        }

        return { headers, signData };
    }

    /**
     * 缓存签名信息
     */
    cacheSignature(cacheKey, signData) {
        this.signCache.set(cacheKey, {
            ...signData,
            cachedAt: Date.now()
        });
    }

    /**
     * 获取缓存的签名
     */
    getCachedSignature(cacheKey) {
        const cached = this.signCache.get(cacheKey);
        if (cached && Date.now() - cached.cachedAt < 300000) { // 5分钟有效期
            return cached;
        }
        return null;
    }

    /**
     * 测试所有签名算法
     */
    testAllAlgorithms(url, params) {
        console.log('🧪 测试所有签名算法...');
        console.log(`测试URL: ${url}`);
        console.log(`测试参数:`, params);
        console.log('');

        const algorithms = [
            { name: 'V1-MD5签名', func: () => this.crackSignV1(url, { ...params }) },
            { name: 'V2-HMAC-SHA256签名', func: () => this.crackSignV2(url, { ...params }) },
            { name: 'V3-AES加密签名', func: () => this.crackSignV3(url, { ...params }) },
            { name: 'V4-复合签名', func: () => this.crackSignV4(url, { ...params }) },
            { name: '真实请求分析', func: () => this.crackSignReal(url, { ...params }) }
        ];

        const results = [];
        for (const { name, func } of algorithms) {
            try {
                const result = func();
                results.push({ name, result });
                console.log(`${name}:`);
                console.log(`  算法: ${result.algorithm}`);
                console.log(`  签名: ${result.sign?.substring(0, 16)}...`);
                console.log(`  时间戳: ${result.timestamp}`);
                console.log('');
            } catch (error) {
                console.log(`${name}: 错误 - ${error.message}`);
                console.log('');
            }
        }

        return results;
    }
}

export default NMPASignatureCracker;