# NMPA Crawler 项目总览

本仓库用于采集国家药监局（NMPA）网站的药品数据，包含多个历史方案与脚本。其中最新可运行、已验证的采集逻辑集中在 `nmpa_crawler_nodejs/` 目录。

## 目录结构

```
nmpa/
├── nmpa_crawler_nodejs/        # Node.js 版真实接口采集方案（推荐）
│   ├── src/                    # 当前使用的核心代码（Playwright + Crawlee）
│   ├── super_main.js           # 推荐入口，会调用 runDatasetCrawler
│   ├── legacy/                 # 早期实验脚本（保留参考，不再维护）
│   ├── README.md               # Node 项目使用指南
│   ├── OPERATIONS.md           # 运行与排错手册
│   └── TECHNICAL_OVERVIEW.md   # 技术实现说明
├── nmpa_crawler/               # Python 等历史方案（未整理，可按需查阅）
├── nmpa_data/                  # 参考数据样例（国内/进口 JSONL）
├── .gitignore                  # 已忽略内部项目/临时输出
└── …                           # 其他历史文档/脚本（保持原样）
```

> 注意：`yiya-crawler-*`、`nmpa_crawler/output/` 等内部资料已列入 `.gitignore`，默认不会出现在 Git 提交历史里。

## 重点模块：nmpa_crawler_nodejs

这是当前维护的采集方案，利用 Playwright 模拟真实浏览器并调用页面内置的 `pajax.hasTokenGet` 接口获取带签名的数据。

### 环境准备

```bash
cd nmpa_crawler_nodejs
npm install
npx playwright install chromium
```

### 运行方式

```bash
node super_main.js       # 或 npm run dataset
```

脚本会自动拆分 国药准字H/S 前缀、控制每段最大页数，并在 `outputs/datasets/` 下生成 4 个 JSONL 文件（国内H、国内S、进口H、进口S）。

### 关键配置（环境变量）

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| NMPA_DATASETS | 指定数据集（domestic-h, domestic-s, imported） | domestic-h,domestic-s,imported |
| NMPA_PAGE_SIZE | 每页条数，可尝试 20/50/100 | 20 |
| NMPA_DOMESTIC_MAX_PAGES | 单段允许的最大页数 | 500 |
| NMPA_DOMESTIC_SEGMENT_LIMIT | 单段最大记录数，默认 PAGE_SIZE × MAX_PAGES | 10000 |
| NMPA_PROXY / HTTP(S)_PROXY | 代理地址 | — |
| NMPA_*_DELAY_MIN/MAX | 多个随机延时区间（拆分、翻页、详情、列表等） | 详见 README.md |
| NMPA_LIST_RETRY_LIMIT | 列表重试次数 | 3 |
| NMPA_DETAIL_RETRY_LIMIT | 详情重试次数 | 2 |

详尽说明参见 `nmpa_crawler_nodejs/README.md`、`OPERATIONS.md`、`TECHNICAL_OVERVIEW.md`。

## 推送后快速检查

1. 确认依赖已安装：`npm install + npx playwright install chromium`（只需一次）。
2. 可选测试：运行 `node super_main.js`，观察日志中"计划抓取""已完成第 x/…" 等信息，确认没有意外报错。
3. 核对输出：确认 `outputs/datasets/` 下 JSONL 文件随时间增大。
4. 仓库状态：`git status -sb` 为空代表没有遗留修改；如需忽略更多内部资料，可在 `.gitignore` 追加目录。

## 常见问题

- 403/412 或被封禁：增大延时参数、使用更稳定的代理出口、降低 `PAGE_SIZE` 或 `DOMESTIC_MAX_PAGES`。
- 推送失效：优先使用 HTTPS + PAT（需 repo 权限）或 SSH + 稳定网络。
- 历史文档/脚本：`nmpa_crawler/`、`yiya-crawler-*` 等目录保留参考，如需整理或上传，请在忽略名单之外单独提交。

---

如需进一步扩展其他数据集，可以在 `dataset_crawler.js` 的 `handleDatasetRequest` 中新增分支，或调整 `nmpa_crawler_nodejs` 块内的配置/逻辑。欢迎在提交前执行一次抓取验证，以确保输出格式与 `nmpa_data` 样例一致。