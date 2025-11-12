# 运行与排错手册

> 本文档记录 `nmpa_crawler_nodejs` 项目的常用操作、参数说明以及排错建议，可与 `README.md` 配合使用。

## 1. 环境准备

1. Node.js ≥ 18（已在服务器安装）
2. 安装依赖
   ```bash
   npm install
   ```
3. 安装 Playwright 浏览器（首次执行）
   ```bash
   npx playwright install chromium
   ```
4. 如需持久化日志，建议使用 `screen` / `tmux` / `nohup` 等工具在后台运行。

## 2. 基本使用

### 2.1 运行完整数据集
```bash
node super_main.js
# 或 npm run dataset
```
- 程序会依次完成 `国内H → 国内S → 进口药品` 三个数据集。
- 数据输出到 `outputs/datasets/*.jsonl`，重复运行会覆盖旧文件。

### 2.2 指定数据集
通过环境变量限制抓取范围：
```bash
NMPA_DATASETS=domestic-h,imported node super_main.js
```
可选值：
- `domestic-h`：国内国药准字 H 系列
- `domestic-s`：国内国药准字 S 系列
- `imported`：进口注册证（自动区分 H / S 并写入两个文件）

## 3. 关键参数

| 变量 | 说明 |
| --- | --- |
| `NMPA_PAGE_SIZE` | 每页请求的记录数（默认 `20`，可尝试 `100`） |
| `NMPA_DOMESTIC_MAX_PAGES` | 单段允许的最大页数（默认 `500`） |
| `NMPA_DOMESTIC_SEGMENT_LIMIT` | 单次搜索允许的最大记录数（默认 `10000`，即 `PAGE_SIZE × MAX_PAGES`） |
| `NMPA_DOMESTIC_SEGMENT_DEPTH` | 拆分深度（默认 `4`，即 `H → H0 → H20 → H200` 最多 4 层） |
| `NMPA_SEGMENT_DIGITS` | 拆分时使用的后缀字符，默认 `0-9` |
| `NMPA_SEGMENT_DELAY_MIN/MAX` | 拆分请求之间的休眠区间（毫秒，默认 `1200 / 2800`） |
| `NMPA_PAGE_DELAY_MIN/MAX` | 每页之间的休眠区间（毫秒，默认 `450 / 900`） |
| `NMPA_DETAIL_DELAY_MIN/MAX` | 批量拉详情前的休眠区间（毫秒，默认 `250 / 600`） |
| `NMPA_SEGMENT_PAUSE_MIN/MAX` | 拆分段之间的额外暂停（毫秒，默认 `2000 / 5000`） |
| `NMPA_LIST_DELAY_MIN/MAX` | 每次列表请求前的随机延时（毫秒，默认 `900 / 2000`） |
| `NMPA_RECORD_DELAY_MIN/MAX` | 每条详情写入后的间隔（毫秒，默认 `80 / 180`） |
| `NMPA_LIST_RETRY_LIMIT` | 列表接口重试次数 |
| `NMPA_DETAIL_RETRY_LIMIT` | 详情接口补偿次数 |

> 拆分策略：程序会先请求 `国药准字H` 获取总数，若超出 `SEGMENT_LIMIT`，则自动派生 `国药准字H0~H9`，继续检测是否需要下钻 `H20`、`H200`……直到每个分段小于阈值或达到最大深度。

## 3.1 调整分页与拆分策略

- 若要尝试“少翻页但单页更多数据”，可以把 `NMPA_PAGE_SIZE` 调高（如 50 / 100），并根据需要调小 `NMPA_DOMESTIC_MAX_PAGES`；程序会自动以 `PAGE_SIZE × MAX_PAGES` 作为单段阈值。
- 如果总记录较多仍触发拆分，可以继续加深拆分深度或调低 `DOMESTIC_MAX_PAGES`，保证每段页数不超过配置值。
- 当频繁出现 403 / 412 时，建议降低 `PAGE_SIZE`，或保持 `PAGE_SIZE` 不变但增加延时参数，让请求节奏更慢。
- 调整完毕后观察日志中的“计划抓取 … 页”“已完成第 … 页”等字段，确认段内页数符合预期。

## 4. 代理配置

### 4.1 环境变量
```bash
export NMPA_PROXY="http://user:pass@host:port"
# 或使用以下变量
export HTTP_PROXY=http://...
export HTTPS_PROXY=http://...
export NMPA_PROXY_USERNAME=xxx
export NMPA_PROXY_PASSWORD=yyy
```
- 支持 HTTP / HTTPS / SOCKS 协议。
- 如果账号密码不方便直接写在 URL，可单独设置 `NMPA_PROXY_USERNAME` / `NMPA_PROXY_PASSWORD`。

### 4.2 代理选择建议
- 尽量使用 **中国大陆出口** 的 IP，命中率更高。
- 动态住宅或隧道代理（如：芝麻 HTTP、亮数据 Bright Data、蚂蚁代理、阿布云）可有效降低封禁概率。
- 建议控制请求速度，避免短时间内持续命中同一出口 IP。

## 5. 常见问题

### 5.1 403 / 412 禁止访问
- 先等待 5-10 分钟，IP 限制通常会自动解除。
- 更换代理出口或降低拆分阈值（让单段请求量更小）。
- 检查是否同时启动了多个实例，避免并发命中。

### 5.2 详情缺失或日志出现 “已跳过”
- 程序会自动重试 2 次；若仍失败则跳过，并在日志中打印记录 ID。
- 可手动补采：调整 `NMPA_DATASETS` 并缩小拆分前缀（例如 `国药准字H340`），只抓取失败段。

### 5.3 任务中断
- 输出文件会按覆盖策略写入，如需断点续跑请提前备份已完成的 JSONL。
- `storage/` 目录保存了 Crawlee 的请求队列和统计，可根据需要清空：
  ```bash
  rm -rf storage/*
  ```

### 5.4 输出目录为空
- 确保命令运行足够长时间（初次抓取会持续数小时）。
- 查看日志是否出现大量 403，如有需要降低阈值或更换代理。

## 6. 目录说明

- `src/dataset_crawler.js`：核心逻辑（拆分、抓取、写文件、代理配置）。
- `legacy/`：历史实验脚本，仅保留参考，不再维护。
- `outputs/`：抓取结果与日志输出目录，已在 `.gitignore` 中忽略。
- `storage/`：Playwright/Crawlee 的临时缓存，可按需清理。

## 7. 建议的运行流程

1. 配置好代理（如需要）。
2. 运行 `node super_main.js` 并观察首批输出是否正常。
3. 对长任务，使用 `nohup node super_main.js > crawler.log 2>&1 &` 挂后台。
4. 定期检查 `outputs/datasets/*.jsonl` 的记录数是否持续增加。
5. 如需定时重复抓取，可将命令写入 crontab，但应预留足够的运行时间。

---

如遇未覆盖的问题，可记录日志时间点、关键提示以及对应的拆分前缀，方便进一步排查。
