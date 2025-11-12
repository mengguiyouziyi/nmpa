# NMPA 药品信息爬虫（境内/境外，化药H/生物S）

> 目标：从 **国家药监局数据查询**（https://www.nmpa.gov.cn/datasearch/home-index.html） 自动抓取：  
> - **境内生产药品**：产品名称（中文、英文）  
> - **境外生产药品**：产品名称（中文、英文）、商品名（中文、英文）  
> - 其余字段会同时保存到 `*.raw.jsonl` 便于后续扩展

## ✅ 方案要点（默认 Browser 引擎—真实可用）
- 通过 `undetected-chromedriver + selenium-wire` 打开 `nmpa.gov.cn`；
- **不需要自行逆向 sign/params 加密**：在页面上下文内直接调用 `window.axios` 发起 `/datasearch/data/nmpadata/search` 与 `/datasearch/data/nmpadata/queryDetail`，由前端自动完成 `sign`、`timestamp`、`token` 及参数处理；
- 自动从 `/datasearch/config/NMPA_DATA.json` 解析 **境内/境外** `itemId`，若失败则回退 `static_item_ids.json`；
- 支持代理、速率控制、失败重试、导出 Excel/CSV；

> 如需 Requests 直连（HTTP 引擎），请自行加入 **站点 sign/参数加密算法**，详见 `http_engine/nmpa_js/README.md`（实验性）。

## 安装
```bash
# 1) 创建虚拟环境（可选）
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) 安装依赖
pip install -r requirements.txt
```

> `undetected-chromedriver` 会自动下载匹配版本的 Chromium/Chrome；国内环境建议配置代理，详见 `config.yaml`。

## 使用
编辑 `config.yaml`，默认已包含四个任务：
- 境内 + 国药准字H
- 境内 + 国药准字S
- 境外 + 国药准字H
- 境外 + 国药准字S

运行：
```bash
python main.py -c config.yaml
```

输出在 `outputs/`：
- `domestic_国药准字H.xlsx / .csv`
- `domestic_国药准字S.xlsx / .csv`
- `imported_国药准字H.xlsx / .csv`
- `imported_国药准字S.xlsx / .csv`
- 对应 `*.raw.jsonl` 保存每条记录完整 JSON。

## 字段抽取说明
为适配不同详情结构，本项目采取“**先全量抓取，再从详情 JSON 抽取**”策略：
- 境内：`产品名称（中文）`、`产品名称（英文）`
- 境外：`产品名称（中文）`、`产品名称（英文）`、`商品名（中文）`、`商品名（英文）`
- 字段匹配使用多组别名（如“药品名称”/“通用名称”等），详见 `utils.py` 的 `ALIASES`。

## 反爬与稳定性
- **JS 逆向**：站点采用 `jsjiami` 混淆 + `axios` 拦截器生成签名与（可能的）参数加密；Browser 引擎在页面内调用 `axios`，**无需逆向**。
- **封禁规避**：
  - `config.yaml` 可调 `delay_min_ms`/`delay_max_ms` 做抖动；
  - 支持 HTTP/HTTPS 代理；
  - 失败自动重试（浏览器请求层面由前端处理，HTTP 引擎由 `tenacity` 负责）。

## HTTP 引擎（实验性，可选）
若你必须用 `requests/httpx`：
1. 在浏览器中调试并扣取 `env.js / md5.js / ajax.js` 的 `sign` 生成逻辑；
2. 将其封装到 `http_engine/nmpa_js/main.js` 的导出接口中；
3. 在 `config.yaml` 中设置：
   ```yaml
   mode: http
   http_engine:
     node_path: "node"
     sign_js: "http_engine/nmpa_js/main.js"
   ```

> 逆向思路可参考社区文章（示例展示了 `/datasearch/data/nmpadata/search` 与 `queryDetail` 需 `timestamp/sign`；并提示近期可能新增“参数加密”）：**请以站点最新逻辑为准**。

## 法律与合规
- 本项目仅用于技术研究与学习，请遵守目标网站的 Robots 协议与服务条款，不要对目标站点造成压力；
- 采集数据仅限个人合规用途，不得用于商业传播；

## 目录结构
```
nmpa_crawler/
├── main.py
├── browser_engine.py
├── http_engine.py
├── utils.py
├── exporter.py
├── static_item_ids.json
├── config.yaml
├── requirements.txt
└── http_engine/
    └── nmpa_js/
        ├── README.md
        └── main.js
```

---

如需自定义字段或并发策略，我已在代码中留出扩展点，欢迎直接修改 `utils.py` 与 `browser_engine.py`。
