# nmpa_js (实验性)

> **说明**：仅当你明确掌握 `https://www.nmpa.gov.cn/datasearch/data/nmpadata/*` 接口的 `sign`/`timestamp`/`token`/参数加密算法时，才需要使用本目录中的 NodeJS 脚本；默认推荐使用 **browser** 引擎（`undetected-chromedriver + axios` 由前端自动完成签名，无需逆向）。

## 参考线索
- 站点通过前端 JS（常见 `jsjiami.com.v6` 混淆）在 `axios` 拦截器里生成签名与可能的参数加密；
- 公开案例显示：`/datasearch/data/nmpadata/search` 与 `/datasearch/data/nmpadata/queryDetail` 需要 `timestamp` 与 `sign` 等请求头/参数；
- 你可以复用浏览器里扣下的 `env.js + md5.js + ajax.js` 等核心函数，将其以 `module.exports` 形式导出，这里仅给出一个形参入口。

## 入参 & 出参
本目录建议的 `main.js` 应支持：
```bash
node main.js '{"url": "...", "params": {...}}'
```
输出：
```json
{"sign": "xxxxx", "timestamp": 1749092062000}
```
