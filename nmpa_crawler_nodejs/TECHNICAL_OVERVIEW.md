# 技术实现说明

本文档概述 `nmpa_crawler_nodejs` 的核心实现方式，帮助理解代码结构、数据流程与反爬策略。代码主体位于 `src/dataset_crawler.js`，运行入口为 `super_main.js`（调用 `runDatasetCrawler`）。

## 1. 总体流程

1. **启动 Playwright**：
   - 采用 Chromium headless 模式（可通过 `PLAYWRIGHT_CHROMIUM_EXEC` 指定缓存二进制）。
   - 支持通过 `NMPA_PROXY` / `HTTP(S)_PROXY` 等环境变量注入代理，底层传给 Playwright 的 `launchOptions.proxy`。
2. **加载页面并注入脚本**：
   - 访问 `https://www.nmpa.gov.cn/datasearch/search-result.html`。
   - 在 `preNavigationHooks` 中执行 `page.addInitScript`，保证页面初始化时就有 `window.getUrl` 以避免 `pajax.hasTokenGet` 依赖的函数缺失。
3. **利用页面自带接口**：
   - 在浏览器上下文 (`page.evaluate`) 内调用 `window.pajax.hasTokenGet`。
   - 由官方脚本负责生成 `sign`、`timestamp`、`token`，无需逆向算法或伪造请求头。
   - 通过 `fetchListPage` 封装列表请求，`fetchDetailsBatch` / `fetchDetailWithRetry` 封装详情请求。
4. **拆分关键词并分页遍历**：
   - `collectDomesticSegments`：针对 `国药准字H` 或 `S`，从 1 级前缀开始（例如 `国药准字H` → `H0` → `H20`）递归拆分。
   - 当 “本段总量 ≤ `DOMESTIC_SEGMENT_LIMIT` 且页数 ≤ `DOMESTIC_MAX_PAGES`” 时认为拆分到位。
   - 首个 payload 会缓存下来，避免重复请求第一页。
5. **写入结果**：
   - 以 JSONL 流式写入 `outputs/datasets/国内H.jsonl` 等文件，每条记录按照 `nmpa_data` 中的字段结构清洗。
   - 如果详情缺失或连续失败，会记录日志并跳过，避免阻塞。

## 2. 请求签名与反爬绕过

- **签名获取**：不自行破解，直接复用前端脚本。
  ```javascript
  const raw = await window.pajax.hasTokenGet(window.api.queryList, {...});
  ```
  这样可以确保 `sign` 与 `timestamp` 与官网一致，避免出现 412/403。

- **节奏控制**：
  - 多级随机延时：拆分请求、翻页、详情批量、列表调用、记录写入等均有独立的随机等待区间。
  - 重试退避：列表和详情失败会按重试次数成倍增加等待时间。
  - 配置化：所有延时区间、页大小、拆分阈值都可通过环境变量覆盖。

- **代理支持**：
  - 支持 `http(s)://user:pass@host:port` 或在 URL 之外通过 `NMPA_PROXY_USERNAME/PASSWORD` 注入认证信息。
  - 若不设置代理，会使用本机出口。

## 3. 拆分策略细节

- 默认 `PAGE_SIZE = 20`、`DOMESTIC_MAX_PAGES = 500`，因此单段最大条数约 10 000。
- 拆分深度默认为 4 层：
  - 层 0：`国药准字H`
  - 层 1：`国药准字H0` ~ `H9`
  - 层 2：`国药准字H20` ~ `H29`
  - 层 3：`国药准字H200` ~ `H209`
- 对于每一个段：
  1. 请求第一页得到 `total` 与 `pageSize`。
  2. 如果 `total <= SEGMENT_LIMIT` 且 `totalPages <= DOMESTIC_MAX_PAGES`，直接分页遍历，否则继续细分。
  3. 分段之间会额外等待 `SEGMENT_PAUSE_RANGE`，降低访问频率。

## 4. 数据写入与容错

- **列表**：`fetchListPage` 在每次执行前调用 `sleepRange(LIST_DELAY_RANGE)`，并把 `pageSize` 统一设为 `PAGE_SIZE`。
- **详情**：批量调用 `fetchDetailsBatch`，若单条失败则 `fetchDetailWithRetry` 退避重试。
- **记录输出**：成功写入后调用 `sleepRange(RECORD_DELAY_RANGE)`，避免连续写入对应大量请求。
- **错误处理**：连续失败会在日志打印 `id`，便于后续人工补采。

## 5. 目录结构

- `super_main.js`：项目入口，调用 `runDatasetCrawler()`。
- `src/dataset_crawler.js`：核心实现，包含所有拆分、请求、代理、输出逻辑。
- `legacy/`：保留早期实验脚本，现有流程不再依赖。
- `outputs/`：抓取输出目录，已在 `.gitignore` 中忽略。
- `storage/`：Crawlee 的队列缓存，可按需清空。

## 6. 可配置项速览

| 分类 | 环境变量 | 默认值 | 说明 |
| --- | --- | --- | --- |
| 数据集 | `NMPA_DATASETS` | `domestic-h,domestic-s,imported` | 控制本次抓取范围 |
| 分页 | `NMPA_PAGE_SIZE` | `20` | 每页条目，可调大到 50/100 |
| 阈值 | `NMPA_DOMESTIC_MAX_PAGES` | `500` | 单段最大页数 |
| 阈值 | `NMPA_DOMESTIC_SEGMENT_LIMIT` | `PAGE_SIZE × MAX_PAGES` | 单段最大条数 |
| 拆分 | `NMPA_DOMESTIC_SEGMENT_DEPTH` | `4` | 递归拆分最大深度 |
| 代理 | `NMPA_PROXY` / `HTTP(S)_PROXY` | — | 代理地址 |
| 代理 | `NMPA_PROXY_USERNAME/PASSWORD` | — | 代理认证 |
| 延时 | `NMPA_*_DELAY_MIN/MAX` | 参见 README 表格 | 控制随机等待区间 |
| 重试 | `NMPA_LIST_RETRY_LIMIT` / `NMPA_DETAIL_RETRY_LIMIT` | `3` / `2` | 列表/详情最大重试次数 |

## 7. 常见问题

- **如何加快或减慢爬取？** 调节 `NMPA_PAGE_SIZE`、`DOMESTIC_MAX_PAGES` 与各类 `*_DELAY_*` 即可。
- **如何补抓失败段？** 缩小拆分前缀（例如 `NMPA_SEGMENT_DIGITS='0,1'`，只跑 `H0`/`H1`），或直接修改 `collectDomesticSegments` 的环境变量让拆分更细。
- **为什么没有自己构造签名？** 直接复用前端脚本可以自动适配网站的签名算法更新；Playwright 负责模拟真实浏览器，`pajax` 负责签名，维护成本低。

如需进一步查看具体实现，可参考 `dataset_crawler.js` 中带注释的函数，以及 `README.md / OPERATIONS.md` 的运行说明。
