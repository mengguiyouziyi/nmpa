# NMPA 药品数据爬虫（Node.js 版）

该项目基于 Playwright + Crawlee，对国家药监局数据查询系统的 **真实接口** 进行自动化抓取，能够稳定拆分并获取 `国内/进口` 药品的“国药准字”数据集。

## ✨ 亮点能力

- **动态关键词拆分**：自动判断 `国药准字H / S` 的分段粒度，避免 1000 页限制。
- **详情补偿机制**：列表拉取失败或详情 403 时会自动退避重试，并单条补齐缺失数据。
- **代理支持**：通过环境变量即可注入中国大陆出口代理（HTTP/HTTPS/SOCKS）。
- **可插拔配置**：数据集清单、拆分阈值、节奏控制等均可通过环境变量细调。
- **标准化输出**：默认写入 `outputs/datasets` 目录的 4 个 JSONL 文件，与 `nmpa_data` 格式保持一致。

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
   ```
   或直接运行 npm 脚本：
   ```bash
   npm run dataset
   ```

运行过程中会自动拆分搜索前缀，逐段拉取列表与详情。任务完成后可在 `outputs/datasets/` 看到四个结果文件：

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
| `NMPA_DATASETS` | 指定要抓取的数据集，逗号分隔（可选值：`domestic-h`, `domestic-s`, `imported`） | `domestic-h,domestic-s,imported` |
| `NMPA_DOMESTIC_SEGMENT_LIMIT` | 单段最大记录数，超过自动继续拆分 | `9000` |
| `NMPA_DOMESTIC_SEGMENT_DEPTH` | 拆分最大深度 | `4` |
| `NMPA_PROXY` / `HTTP(S)_PROXY` | 代理地址（支持 `http://user:pass@host:port`） | 无 |
| `NMPA_PROXY_USERNAME` / `NMPA_PROXY_PASSWORD` | 当代理账号信息不能写进 URL 时使用 | 无 |
| `NMPA_SEGMENT_DELAY_MIN/MAX` | 拆分请求之间的等待区间（毫秒） | `1200 / 2800` |
| `NMPA_PAGE_DELAY_MIN/MAX` | 翻页之间的等待区间（毫秒） | `450 / 900` |
| `NMPA_DETAIL_DELAY_MIN/MAX` | 批量拉详情前的等待区间（毫秒） | `250 / 600` |
| `NMPA_SEGMENT_PAUSE_MIN/MAX` | 拆分段之间的休眠区间（毫秒） | `2000 / 5000` |
| `NMPA_LIST_DELAY_MIN/MAX` | 列表请求前的随机延时（毫秒） | `900 / 2000` |
| `NMPA_RECORD_DELAY_MIN/MAX` | 每条详情写入后的间隔（毫秒） | `80 / 180` |
| `NMPA_LIST_RETRY_LIMIT` | 列表请求重试次数 | `3` |
| `NMPA_DETAIL_RETRY_LIMIT` | 详情补偿重试次数 | `2` |

> **代理推荐**：如需长期高频抓取，建议选用中国出口的动态住宅/隧道代理（例如：芝麻 HTTP、亮数据 Bright Data、蚂蚁代理、阿布云等），并保证 IP 切换间隔与并发量符合服务商限制。

## 📄 数据格式示例

```jsonc
{"code":"国药准字H10950068","zh":"氧氟沙星葡萄糖注射液","en":"Ofloxacin and Glucose Injection"}
{"code":"国药准字S20063025","zh":"抗狂犬病血清","en":"Rabies Antiserum"}
{"code":"H20171268","product_zh":"琥珀酸普芦卡必利片","product_en":"Prucalopride Succinate Tablets","commodity_zh":"力洛","commodity_en":"Resolor"}
{"code":"S20160004","product_zh":"利拉鲁肽注射液","product_en":"Liraglutide Injection","commodity_zh":"诺和力","commodity_en":"Victoza"}
```

## 🗂 目录结构（核心部分）

```
nmpa_crawler_nodejs/
├── super_main.js              # 推荐入口，封装 runDatasetCrawler
├── package.json               # 项目入口 & npm scripts
├── src/
│   ├── dataset_crawler.js     # 数据集抓取主逻辑
│   └── utils/                 # 其他工具模块（保留）
├── outputs/                   # 默认输出目录（已在 .gitignore 中忽略）
├── storage/                   # Crawlee 临时缓存
├── legacy/                    # 历史脚本与实验代码（保留参考）
├── README.md                  # 当前文档
└── OPERATIONS.md              # 运行与排错手册
```

> 历史脚本历史原因暂保留在 `legacy/`，如需回溯旧方案可在该目录查阅。

## 🛠 运行技巧

- 建议 **后台持久运行**（如 `nohup` / `screen` / `tmux`），以免长时间任务被意外中断。
- 若出现 403，可等待 5-10 分钟或更换代理后重启；任务会自动从头开始并覆盖输出文件。
- 数据量较大时，建议按 Segment 模式运行（默认），避免一次请求触达 1000 页上限。
- `storage/` 目录里保留 Crawlee 的队列和统计，可用于排错，如不需要可定期清理。

## 📚 相关文档

- [OPERATIONS.md](OPERATIONS.md) — 运行流程、常见问题、代理建议
- [USAGE_GUIDE.md](USAGE_GUIDE.md) — 原始指南（保留）
- 其他 `FINAL_*.md` — 历史方案文档，按需查阅

## ⚠️ 注意

1. 请遵守目标网站的使用条款，合理安排请求频率。
2. 建议在夜间/低峰时段运行，减少被风控的风险。
3. 如需合规留证，建议保留日志与请求参数。

---

**维护者提示**：如需扩展新的数据源或接入任务调度，可在 `runDatasetCrawler` 的 `options.datasets` 或 `NMPA_DATASETS` 中追加自定义标识，并在 `handleDatasetRequest` 内实现对应逻辑。
