# NMPA 药品数据爬虫（Node.js 版）

本项目基于 **Playwright + Crawlee** 对国家药监局数据查询系统（https://www.nmpa.gov.cn/datasearch/search-result.html）进行自动化抓取，能够稳定拆分并获取国内 / 进口“国药准字”药品数据。脚本会模拟真实浏览器，直接调用页面内置的 `pajax.hasTokenGet` 接口获取带签名的响应数据，因此无需额外逆向签名算法。

## ✨ 亮点能力

- **动态关键词拆分**：自动判断 `国药准字H / S` 的分段粒度，控制在最多 500 页以内，规避 1000 页限制。
- **详情补偿机制**：列表或详情请求失败会退避重试，必要时单条补采，最大化保全数据。
- **节奏可控**：内置多维随机延时（拆分、翻页、列表、详情、记录写入），默认配置即较为保守，可按需通过环境变量进一步调慢。
- **代理支持**：支持 HTTP / HTTPS / SOCKS 代理以及账号密码注入，便于结合国内出口代理或隧道服务使用。
- **可插拔配置**：数据集清单、分页大小、拆分阈值、延时区间等均可通过环境变量自定义。
- **标准化输出**：默认生成 `outputs/datasets/{国内H, 国内S, 进口H, 进口S}.jsonl`，字段格式与 `nmpa_data` 示例保持一致。

## 🚀 快速上手

1. 安装依赖
   ```bash
   npm install
   ```
2. 安装 Playwright 浏览器（首次执行即可）
   ```bash
   npx playwright install chromium
   ```
3. 运行“超级增强版”抓取任务
   ```bash
   node super_main.js
   # 或 npm run dataset
   ```

运行过程中脚本会自动拆分搜索前缀、分页拉取列表并补采详情。任务完成后可在 `outputs/datasets/` 查看四个 JSONL 文件，随时间增长即表示抓取在推进。

```
outputs/datasets/
├── 国内H.jsonl
├── 国内S.jsonl
├── 进口H.jsonl
└── 进口S.jsonl
```

## ⚙️ 核心环境变量

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `NMPA_DATASETS` | 指定要抓取的数据集（`domestic-h`, `domestic-s`, `imported`） | `domestic-h,domestic-s,imported` |
| `NMPA_PAGE_SIZE` | 每页请求的记录数（建议 20 起步，可尝试 100） | `20` |
| `NMPA_DOMESTIC_MAX_PAGES` | 单段允许的最大页数 | `500` |
| `NMPA_DOMESTIC_SEGMENT_LIMIT` | 单段最大记录数（默认 `PAGE_SIZE × MAX_PAGES`） | `10000` |
| `NMPA_DOMESTIC_SEGMENT_DEPTH` | 拆分最大深度 | `4` |
| `NMPA_PROXY` / `HTTP(S)_PROXY` | 代理地址（支持 `http://user:pass@host:port`） | — |
| `NMPA_PROXY_USERNAME` / `NMPA_PROXY_PASSWORD` | 当账号信息不便写入 URL 时使用 | — |
| `NMPA_SEGMENT_DELAY_MIN/MAX` | 拆分请求之间的等待区间（毫秒） | `1200 / 2800` |
| `NMPA_SEGMENT_PAUSE_MIN/MAX` | 两个拆分段之间的额外暂停（毫秒） | `2000 / 5000` |
| `NMPA_PAGE_DELAY_MIN/MAX` | 翻页之间的等待区间（毫秒） | `450 / 900` |
| `NMPA_DETAIL_DELAY_MIN/MAX` | 批量拉详情前的等待区间（毫秒） | `250 / 600` |
| `NMPA_LIST_DELAY_MIN/MAX` | 每次列表请求前的随机延时（毫秒） | `900 / 2000` |
| `NMPA_RECORD_DELAY_MIN/MAX` | 每条详情写入后的间隔（毫秒） | `80 / 180` |
| `NMPA_LIST_RETRY_LIMIT` | 列表请求重试次数 | `3` |
| `NMPA_DETAIL_RETRY_LIMIT` | 详情请求重试次数 | `2` |

> 如果需要进一步降低请求频率，可增大以上延时参数，或调小 `PAGE_SIZE` / `DOMESTIC_MAX_PAGES`。

## 🛠 运行技巧与建议

- **后台运行**：建议结合 `nohup` / `screen` / `tmux` 等工具运行长任务，避免意外退出。示例：`nohup node super_main.js > crawler.log 2>&1 &`
- **代理选型**：推荐使用中国大陆出口的住宅或隧道代理（芝麻 HTTP、亮数据 Bright Data、蚂蚁代理、阿布云等），根据供应商要求设置并发与 IP 切换间隔。
- **节奏控制**：若日志中频繁出现 403，可增大延时参数或临时下调 `PAGE_SIZE`/`DOMESTIC_MAX_PAGES`，让每段数据量更小。
- **断点补采**：可通过 `NMPA_DATASETS` 指示仅抓取部分数据集，也可以把 `NMPA_PAGE_SIZE`、前缀拆分范围调得更细，只补未完成的段。
- **缓存清理**：`storage/` 目录保存了 Crawlee 队列信息，若要重新开始，可删除 `storage/*` 后再运行；`outputs/` 会覆盖写入，建议提前备份已完成的数据。

## 🔍 技术原理概述

脚本使用 Playwright 启动 Chromium，进入官方页面后在浏览器上下文内调用 `pajax.hasTokenGet`，由网站原始脚本完成签名与校验。通过 `dataset_crawler.js` 中的拆分逻辑，先检测 `国药准字` 总量、再逐级细分关键字，确保每个检索段的页数不超过配置阈值。请求节奏由多维随机延时控制，详情失败会退避重试；最终以 JSONL 流式写入输出文件。

更详细的架构与原理说明可阅读 **[TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md)**。

## 📚 文档索引

- `README.md`（本文）— 项目简介与使用说明
- [`OPERATIONS.md`](OPERATIONS.md) — 运行流程、参数调优、常见问题
- [`TECHNICAL_OVERVIEW.md`](TECHNICAL_OVERVIEW.md) — 技术实现与关键细节
- `USAGE_GUIDE.md` — 原始历史指南（保留参考）
- `FINAL_*.md` — 过往方案 / 研究文档，可按需查阅

## ⚠️ 注意事项

1. 请遵循目标网站使用条款，合理安排抓取频率。
2. 建议在夜间或低峰时段运行，降低风控风险。
3. 若用于正式生产场景，务必保留运行日志、请求参数和代理记录。

---

**维护者提示**：如需扩展新的数据源或加入调度，可以在 `runDatasetCrawler` 的 `options.datasets` 或 `NMPA_DATASETS` 中追加自定义标识，并在 `handleDatasetRequest` 分支内实现对应逻辑。
