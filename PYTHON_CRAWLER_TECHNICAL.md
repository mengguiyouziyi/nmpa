# Python 版 NMPA 分段爬虫技术说明

> 适用目录：`~/projects/taya/nmpa/nmpa_crawler_python`  
> 脚本入口：`crawler.py`

## 1. 架构概览

- **语言 / 依赖**：Python 3 + `requests`，通过 `NMPAClient` 复用 Node 版的签名、时间戳、暖场策略。
- **入口脚本**：`crawler.py`，负责参数解析、日志初始化、分段递归、翻页抓取、详情落盘与节流控制。
- **输出目录结构**（与 Node 版保持一致）：
  ```
  outputs/
    datasets/        # 分段后的 JSONL 文件
      国药准字H109500/
        国药准字H109500_001.jsonl
        ...
    details/         # 每条记录对应的详情 JSON 缓存
      ffff62bbec9b6ea4172d3482a81f292a.json
      ...
  ```

## 2. 核心常量与调度策略

| 常量 | 说明 | 默认值 |
| ---- | ---- | ---- |
| `DOMESTIC_ITEM_ID` | “国药准字”列表接口的 itemId | `ff80808183cad75001840881f848179f` |
| `PAGE_SIZE` | 单页请求条数（由官网限制） | 20 |
| `SEGMENT_THRESHOLD` | 单段最大记录数阈值（超出需继续拆分） | 200 (20 x 10) |
| `SEGMENT_MAX_PAGES` | 单段最大允许页数 | 10 |
| `SEGMENT_MAX_DEPTH` | 最大拆分深度 | 8 |
| `SEGMENT_DIGITS` | 拆分追加字符集 | `"0123456789"` |
| `PAGE_DELAY_RANGE` | 翻页请求随机等待 | 1.8s ~ 3.2s |
| `DETAIL_DELAY_RANGE` | 单条详情请求随机等待 | 2.6s ~ 4.2s |
| `SEGMENT_DELAY_RANGE` | 完成一个分段后的冷却间隔 | 30s ~ 48s |
| `DETAIL_BACKOFF_RANGE` | 详情请求失败后的退避时间 | 18s ~ 30s |

所有延迟使用 `random.uniform(low, high)` 生成，以模拟真实访问节奏，显著降低 412/403 风险。

## 3. 主要模块说明

### 3.1 日志初始化 `configure_logging`
- 支持 `--log-level` 参数，默认 `INFO`。
- 打印格式：`时间 | 级别 | 消息`，所有关键步骤均以中文标签标注，方便 tail -f 观察。

### 3.2 目录准备 `_ensure_directories`
- 初始化 `outputs/` 根目录及子目录。
- 每个分段开始前调用 `_prepare_segment_output`，若已存在同名段目录会清空旧的 JSONL，确保数据一致。

### 3.3 分段递归 `segment_queries`
1. 调用 `fetch_first_page` 获取第一页，统计 `total`、`pageSize`、`totalPages`。
2. 如果 `total <= SEGMENT_THRESHOLD` 且 `totalPages <= SEGMENT_MAX_PAGES`，或已达到 `SEGMENT_MAX_DEPTH`，则直接返回该段。
3. 否则遍历 `SEGMENT_DIGITS`，将关键字拼接新后缀（如 `"国药准字H"` → `"国药准字H0"` ~ `"国药准字H9"`），递归继续拆分。
4. `visited` 集合用于去重，避免循环。

日志示例：
```
【拆分】国药准字H1095: 总记录=258, 页数=13, 实际页大小=20, 深度=0
【拆分】国药准字H1095: 需要继续细分 -> 总记录=258, 页数=13, 深度=0
```

### 3.4 分段处理 `process_segment`
1. 调用 `_prepare_segment_output` 清理旧文件。
2. 首先处理第一页列表数据：`fetch_details`→ `_write_dataset_records`。
3. 若还有后续页，调用 `fetch_remaining_pages` 循环请求。
4. 每个分段结束后打印统计并执行段级冷却。

日志示例：
```
【段开始】国药准字H109500: 总记录=72, 页数=4, 深度=2
【写入】国药准字H109500 第 002 页 -> 20 条记录
【段完成】国药准字H109500: 本段共写入 72 条
```

### 3.5 列表抓取 `fetch_remaining_pages`
- 逐页请求 `/data/nmpadata/search`。
- 每页执行 `fetch_details` 获取详情并写入 JSONL。
- 完成后返回本段累计写入条数。

### 3.6 详情缓存与抽取 `fetch_details`
1. 从列表记录中读取 `record_id = f4`（若无则尝试 `id`）。
2. 若 `outputs/details/<record_id>.json` 已存在，直接读取缓存。
3. 无缓存则调用 `_fetch_detail`，请求 `/data/nmpadata/queryDetail`，参数包含 `id`、`itemId`、`isSenior=N`。
4. 将原始响应 JSON 写入缓存，再解析 `data.detail` 或顶层 `detail`。
5. 仅保留 `f0`、`f1`、`f2` 字段作为最终记录（分别对应 `code`、`zh`、`en`）。
6. 通过 `seen_codes` 进行去重，避免同 code 多次写入。
7. 请求失败或解析失败时打印 warning，并执行退避等待。

### 3.7 CLI 参数
```
python3 crawler.py \
  --query "国药准字H" \
  --query "国药准字S" \
  --log-level INFO \
  --max-segments 5
```
- 不传 `--query` 时默认同时处理 `国药准字H` 与 `国药准字S`。
- `--max-segments` 用于调试或分批运行；不指定则全量跑完所有拆分段。

## 4. 运行流程总结

1. **启动**：解析参数 → 配置日志 → 初始化 `NMPAClient`（自动暖场、设置 cookies）。
2. **分段探索**：对每个基础关键词递归拆分，直到满足阈值或达到最大深度。
3. **分页抓取**：段内从第 1 页开始逐页请求，写入 JSONL，详情缓存到文件。
4. **节流控制**：分页之间执行 `PAGE_DELAY_RANGE`；详情请求后执行 `DETAIL_DELAY_RANGE`；段结束后执行 `SEGMENT_DELAY_RANGE`；异常重试执行 `DETAIL_BACKOFF_RANGE`。
5. **完成收尾**：记录累计段数与总写入条数，在日志中打印汇总信息。

## 5. 与 Node 版的对齐点

- 输出目录/文件命名完全复刻 Node 版本，便于后续数据汇总或比较。
- 按照同样的拆分策略：递归拆 0~9、最多 8 层、单段 ≤ 10 页。
- 详情字段对齐 Node 版本的 `code/zh/en` 三字段，额外详情信息保留在缓存 JSON 供后续扩展。
- 日志信息参照 Node 版风格，关键节点使用中文描述，方便运维快速确认状态。

## 6. 扩展建议

- **详情字段扩展**：若后续需要更多字段，可在 `_detail_to_entry` 中追加提取逻辑，并同步调整 JSONL 结构。
- **412 防护策略**：当前依赖客户端已有的时间戳刷新与 warmup，如果仍出现频繁防护，可考虑：
  - 增加更长的段间冷却；
  - 在 `fetch_details` 中引入指数退避重试；
  - 结合代理池或多出口 IP。
- **进度持久化**：可按 Node 版思路扩展 run_state.json，记录已完成段位，支持断点续跑。
- **并行优化**：当前脚本串行运行以最小化风险，如后续需要提速，可考虑按基础关键词多进程运行，但务必加大冷却。

## 7. 快速检查命令

```bash
# 查看最近生成的分段及文件
ls outputs/datasets | head
ls outputs/datasets/国药准字H109500

# 抽样查看 JSONL 与详情
head outputs/datasets/国药准字H109500/国药准字H109500_001.jsonl
head outputs/details/ffff62bbec9b6ea4172d3482a81f292a.json

# 监控日志
python3 crawler.py --log-level INFO --query "国药准字H1095" --max-segments 1
```

---

如需调整频率或拆分策略，可直接修改 `crawler.py` 顶部常量并重新运行。该文档亦可放入仓库内的 `docs/` 目录，便于团队协作时快速掌握 Python 版实现。

## 8. 请求签名与时间戳流程（`client.py`）

### 8.1 时间戳缓存
- `_cached_timestamp`：上次成功获取的服务器毫秒时间戳。
- `_timestamp_fetched_at`：本地时间，用于计算 TTL。
- `fetch_server_timestamp(force=False)`：
  1. 若缓存有效（未超出 `timestamp_ttl`），直接返回。
  2. 否则请求 `GET /config/DATE.json?date=<epoch_ms>`。
  3. 从响应头 `Date` 解析服务器时间，转换为 UTC 毫秒并缓存。

### 8.2 签名生成
1. `_prepare_signature` 收集所有非空参数，并追加 `timestamp`。
2. `_sorted_query_string` 对参数按 key 排序，拼接 `key=value`。
3. `_json_md5_to_str`：
   - 将拼接字符串与 `APP_SECRET` 相连（空字符串则仅用 secret）。
   - 进行 URL 编码（符合 NMPA 前端代码的 encode 逻辑）。
   - 对编码结果取 MD5 生成 32 位十六进制签名。
4. 返回 `SignedRequest`，包含 `sign`、`timestamp`、`raw`。
5. `_build_headers` 将 `sign`、`timestamp` 放入请求头，同时保留 User-Agent、Referer、Origin 等伪装字段。

### 8.3 重试与 412 处理
- `_request` 中最多执行 `retries + 1` 次（默认 3 次）。
- 如果返回 412：
  - 调用 `_invalidate_timestamp()` 清理缓存。
  - 随机 `sleep(1.2~3.0)` 后重试。
- 其它异常遵循相同的退避逻辑，最终抛出捕获到的最后一次异常。

### 8.4 暖场流程
`warmup()` 模拟浏览器访问顺序：
1. `https://www.nmpa.gov.cn/`
2. `https://www.nmpa.gov.cn/yaopin/`
3. `https://www.nmpa.gov.cn/datasearch/search-result.html`

若遭遇 412，会检查 cookies 是否已包含 `acw_tc`，否则继续重试。每个阶段之间会执行 `warmup_delay` 的等待（默认 1.5s）。

## 9. API 端点与参数规范

| 接口 | 方法 | 参数 | 描述 |
| ---- | ---- | ---- | ---- |
| `/data/nmpadata/search` | GET | `itemId`, `searchValue`, `pageNum`, `pageSize`, `isSenior` | 列表页接口，返回 `data.list`, `data.total`, `data.pageSize` |
| `/data/nmpadata/queryDetail` | GET | `id`, `itemId`, `isSenior` | 详情接口，返回 `data.detail` 或顶层 `detail` |
| `/config/DATE.json` | GET | `date` | 服务端时间戳，用于签名 |

**列表响应示例**：
```json
{
  "code": 200,
  "data": {
    "total": 72,
    "pageSize": 20,
    "list": [
      {"f0": "国药准字H10950068", "f1": "氧氟沙星葡萄糖注射液", "f2": "黑龙江博宇制药有限公司", "f4": "ffff62bbec9b6ea4172d3482a81f292a"}
    ]
  },
  "message": null
}
```

**详情响应示例**：
```json
{
  "code": 200,
  "data": {
    "isMark": false,
    "detail": {
      "f0": "国药准字H10950068",
      "f1": "氧氟沙星葡萄糖注射液",
      "f2": "Ofloxacin and Glucose Injection",
      "f3": "普光",
      "f4": "注射剂",
      "f5": "200ml:氧氟沙星0.2g与葡萄糖11.0g",
      "f8": "黑龙江博宇制药有限公司",
      "f9": "2020-10-18",
      "f10": "黑龙江省庆安县东城区",
      "f15": "ffff62bbec9b6ea4172d3482a81f292a"
    }
  },
  "message": null
}
```

## 10. 拆分状态机

```
┌───────────────┐
│ base keyword │  （如 国药准字H）
└──────┬────────┘
       │ segment_queries(depth=0)
       ▼
┌──────────────────────────┐
│ fetch_first_page(base,0) │ → 无数据 => 终止
└──────┬────────┬──────────┘
       │        │total<=阈值/页<=10
       │        ▼
       │   返回 SegmentResult
       │
       │ total>阈值 或 页>10
       ▼
for digit in "0123456789":
    segment_queries(base+digit, depth+1)
```

- 使用 DFS 深度优先遍历，确保更细的段位先完成。
- `visited` 集合避免重复处理同一关键字（如同层拆分后再次访问）。
- 深度达到 `SEGMENT_MAX_DEPTH` 仍然超阈值时，会直接使用当前段并输出 warning。

## 11. 详情抓取细节

1. 记录 ID 选取顺序：`record.get("f4")` → `record.get("id")`。
2. 详情缓存：如 `outputs/details/<id>.json` 已存在，直接 `json.load`；失败时打印 warning 并重新请求。
3. `_extract_detail` 兼容两种结构：
   - `payload["detail"]`（部分响应直接返回）。
   - `payload["data"]["detail"]`（多数响应）。
4. `_detail_to_entry` 仅提取 `f0/f1/f2`，转化为 `code/zh/en` 并去除首尾空白。
5. `seen_codes` 记录已写入的药品编码，防止重复（区别于记录 ID）。
6. 请求失败后执行 `DETAIL_BACKOFF_RANGE` 等待再继续本页其他记录。

## 12. 日志分类表

| 标签 | 说明 | 触发位置 |
| ---- | ---- | ---- |
| `【启动】` | CLI 参数、初始关键词 | `main()` |
| `【入口】` | 基础关键词开始处理 | `crawl()` |
| `【拆分】` | 拆分判断、递归状态 | `fetch_first_page` / `segment_queries` |
| `【队列】` | 分段进入处理队列 | `crawl()` |
| `【段开始】/【段完成】` | 段级统计 | `process_segment()` |
| `【分页】` | 翻页请求进度 | `fetch_remaining_pages()` |
| `【详情】` | 详情新增数量 | `fetch_details()` |
| `【写入】` | JSONL 文件写入概况 | `_write_dataset_records()` |
| `【终止】/【完成】` | 运行结束或提前终止 | `crawl()` |
| `WARNING` | 记载异常/重试信息 | 详情/缓存/拆分异常路径 |

## 13. 数据结构字典

### 13.1 JSONL
- 文件路径：`outputs/datasets/<segment>/<segment>_<page>.jsonl`
- 字段定义：
  - `code`: 国药准字编号（如 `国药准字H10950068`）
  - `zh`: 中文药品名称
  - `en`: 英文名称
- 每个文件对应一页（最多 200 条），便于与 Node 版对齐。

### 13.2 详情缓存
- 文件路径：`outputs/details/<record_id>.json`
- 内容：原始接口 JSON，全量保留以支持后续字段扩展。
- `record_id` 等同于列表返回字段 `f4`，与 `code` 不完全相同（后者包含字母 + 数字的药品批准文号）。

## 14. 性能与节流预估

| 项目 | 数值 (默认配置) | 说明 |
| ---- | ---- | ---- |
| 单页耗时 | ~5-7s | 含列表请求、20 条详情、分页延迟 |
| 单段耗时 (4 页) | ~90-120s | 包含段级冷却 30-48s |
| 单条详情耗时 | 2.6-4.2s | 请求 + 写入缓存 |
| 412 冷却 | 1.2-3.0s | `_request` 内部实现 |

**估算**：`国药准字H` 全量约 10 万条 → 预计分段数 ~500-600（细节取决于分布）。按默认参数，持续运行可能持续 12-18 小时，建议使用长时间运行工具如 `tmux`/`screen`。

## 15. 故障排查清单

1. **频繁 412**  
   - 检查是否有系统代理、VPN 等影响。  
   - 增大 `SEGMENT_DELAY_RANGE`、`PAGE_DELAY_RANGE`。  
   - 查看日志是否出现 `【详情】...请求失败`，必要时扩大 `DETAIL_BACKOFF_RANGE` 或增加 `retries`。
2. **无详情文件生成**  
   - 确认 `outputs/details` 是否有写权限。  
  - 检查日志中是否出现 `【详情】...无 detail 字段`，可能接口返回结构变更。  
3. **JSONL 空文件**  
   - 日志中会有 `【写入】...无有效详情`。检查详情接口是否异常或缓存文件被破坏。  
4. **长时间无输出**  
   - tail 日志关注 `【拆分】` 与 `【段开始】` 是否还在增长。  
   - 若停留在 `【拆分】`，可能 `SEGMENT_DIGITS` 为空或网络请求失败。  

## 16. 扩展开发建议

- **多源抓取**：如需同时抓取境外药品，可新增不同的 `itemId` 与基础关键字，再在 CLI 中指定。  
- **任务断点**：可以在 `process_segment` 成功后写一份运行状态（如 JSON），记录已完成段，重启时跳过已有段。  
- **异常指标**：结合 Prometheus/日志监控，将 `【详情】...请求失败`/412 计数上报，便于长期运行的稳定性监控。  
- **并发优化**：若未来需要并行，可考虑：
  - 每个基础关键字开一个子进程（注意共享 `outputs/details`）。  
  - 在 `fetch_details` 内部批量请求时使用 `ThreadPoolExecutor` / 异步请求，但需更严格节流。  

---

## 17. 加密参数破解细节

本节详细说明签名与时间戳的逆向过程、Python 复现方式，以及 Node 版原始尝试，方便在其他项目中复用。

### 17.1 前置取证

1. **浏览器抓包**  
   - 打开 `https://www.nmpa.gov.cn/datasearch/search-result.html`，执行一次搜索。  
   - 记录 `network` 面板中 `XHR` 请求的 QueryString（`itemId、searchValue、pageNum、pageSize、isSenior` 等），以及请求头中的 `timestamp`、`sign`。  
   - 记下响应头 `Date`，用于校准服务器时间。
2. **源码定位**  
   - 在 DevTools `Sources` 中搜索 `sign` / `timestamp`。  
   - 官网混淆脚本中存在 `MD5` 计算逻辑，对参数排序后追加一个常量密钥（经排查为 `nmpasecret2020`）。  
3. **时间戳接口**  
   - 通过抓包可见页面会在发起搜索前请求 `GET /config/DATE.json?date=<client_ms>`。  
   - 响应正文不重要，关键在 `Date` 头部，可转换为 UTC 毫秒时间戳。

### 17.2 Python 版实现（`client.py`）

核心常量与函数：

```python
APP_SECRET = "nmpasecret2020"

def _sorted_query_string(pairs):
    items = []
    for key, value in pairs.items():
        if value is None or value == "":
            continue
        items.append(f"{key}={value}")
    return "&".join(sorted(items))

def _json_md5_to_str(sorted_query: str) -> str:
    payload = f"{sorted_query}&{APP_SECRET}" if sorted_query else APP_SECRET
    encoded = urllib.parse.quote(payload, safe="-_.!~*'()")
    encoded = (
        encoded.replace("!", "%21")
        .replace("(", "%28")
        .replace(")", "%29")
        .replace("~", "%7E")
    )
    return hashlib.md5(encoded.encode("utf-8")).hexdigest()
```

生成签名的完整流程：

```python
def _prepare_signature(self, params):
    timestamp = self.fetch_server_timestamp()
    sign_payload = {k: v for k, v in params.items() if v not in ("", None)}
    sign_payload["timestamp"] = timestamp
    sorted_query = _sorted_query_string(sign_payload)
    sign = _json_md5_to_str(sorted_query)
    return SignedRequest(sign=sign, timestamp=timestamp, raw=sorted_query)
```

关键点：
- **时间戳同步**：`fetch_server_timestamp()` 会请求 `/config/DATE.json`，解析响应头 `Date`。设置 `timestamp_ttl=60`，60s 内复用缓存，避免频繁请求。  
- **参数排序**：按 ASCII 顺序排序，排除空值，保证签名与官方一致。  
- **secret 拼接**：`APP_SECRET` 追加到 query 字符串后再 URL 编码，保持与原站 `encodeURIComponent` 一致（注意 `!()~` 的额外替换）。  
- **重试策略**：遇到 412 会调用 `_invalidate_timestamp()`，重新获取时间戳 + 再签名。  

### 17.3 详情接口签名

- 详情接口路径 `/data/nmpadata/queryDetail` 使用同一套签名算法，只是参数包含 `id`。  
- Python 调用示例：

```python
resp = client.get(
    "/data/nmpadata/queryDetail",
    params={"id": record_id, "itemId": DOMESTIC_ITEM_ID, "isSenior": "N"},
    timeout=15.0,
    retries=3,
)
```

- `_prepare_signature` 会自动将 `id` 纳入排序字符串，生成合法 `sign`。

### 17.4 Node 版参考（源码片段）

`nmpa_crawler_nodejs/src/utils/signature-cracker.js` 中保留了不同猜测版本，真实逻辑位于 `crackSignReal`：

```javascript
crackSignReal(url, params) {
    const timestamp = Date.now().toString();
    params.timestamp = timestamp;
    const itemId = params.itemId || 'ff80808183cad75001840881f848179f';
    const fixedFormat =
        `itemId=${itemId}&isSenior=${params.isSenior || 'N'}` +
        `&searchValue=${params.searchValue}&pageNum=${params.pageNum}` +
        `&pageSize=${params.pageSize}&timestamp=${timestamp}`;
    const sign1 = CryptoJS.MD5(fixedFormat).toString();
    return { sign: sign1, timestamp, algorithm: 'REAL_ANALYSIS' };
}
```

- Node 实现来源于对官网脚本的反混淆，与 Python 版的最终逻辑一致。  
- Python 版将 secret 提炼为常量 `APP_SECRET` 并补齐正式的 URL 编码规则，使得签名与官网完全匹配。

### 17.5 逆向要点回顾

1. **抓包锁定请求字段**：寻找 `timestamp`, `sign`，分析 QueryString。  
2. **解析时间戳来源**：观察 `/config/DATE.json` 调用，解析响应头 `Date`。  
3. **确认 secret**：搜索官网脚本中的字符串常量或对 `sign` 逆向，最终定位 `nmpasecret2020`。  
4. **校验**：将 Python 生成的 `sign` 与官网请求对比（可使用线上测试）。若一致，则证明算法正确。  
5. **异常处理**：脚本遇到 412 会自动刷新 timestamp + sign，必要时执行冷却。

### 17.6 迁移到其他项目

复用时仅需实现以下步骤：
- 用目标站点的 `secret`、`参数排序规则`、`编码方式` 替换 `APP_SECRET` 及 `_json_md5_to_str`。  
- 若有额外字段（如 `nonce`、`deviceId`），将其加入排序后参与签名。  
- 将 `fetch_server_timestamp` 替换为目标站点的时间同步逻辑。  
- 复用 `NMPAClient` 架构即可快速搭建新的签名客户端。

---

该附录补充了签名算法、接口字段、状态机、日志、节流与排查等细粒度细节，可作为团队成员调试、扩展或迁移 Python 版爬虫的参考蓝本。

## 18. 断点续爬与风控冷却机制

### 18.1 `run_state.json` 结构

- 路径：`outputs/run_state.json`
- 生成时机：每进入/完成一个分段都会刷新。
- 结构示例：
  ```json
  {
    "segments": {
      "国药准字H110204": {
        "status": "in_progress",
        "next_page": 3,
        "total_pages": 4,
        "depth": 2,
        "updated": 1760952276.123
      }
    }
  }
  ```
- 字段含义：
  - `status`: `in_progress` / `completed`
  - `next_page`: 下一次应抓取的页码（已完成第一页时为 2）
  - `total_pages`: 该段总页数，用于恢复日志提示
  - `depth`: 拆分深度，辅助排查
  - `updated`: Unix 时间戳，便于判断最新写入时刻
- 恢复策略：
  1. 脚本启动时加载 `run_state.json`；
  2. 若 `status=completed`，直接跳过该段；
  3. 若 `status=in_progress`，根据 `next_page` 定位续跑页码；
  4. 自动读取已写入 JSONL，重建 `seen_codes`，避免重复写入；
  5. 成功写完所有页后 `status` 置为 `completed`。

### 18.2 风控冷却流程

- **触发条件**：列表、详情、时间戳任一请求出现 `403` 或 `412`。
- **等待策略**：
  - `412`：短冷却 0.8s，并刷新时间戳。
  - `403`：长冷却 `random.uniform(300, 600)` 秒（5~10 分钟），最多重试 `BLOCK_RETRY_LIMIT = 5` 次。
- **日志示例**：
  ```
  【详情】7003...: 请求失败(403 ...)，执行退避
  【风控】详情 7003... 返回 403（1/5），冷却 428.3 秒后重试
  ```
- **状态记录**：冷却时会调用 `RunStateManager.record_block_event`，在 `run_state.json` 中留下 `last_block` 记录，便于复盘。

### 18.3 客户端层面的防护

- `client.py` 的 `_request` 和 `fetch_server_timestamp` 均内置 403 处理逻辑：
  - 每次 403 会调用 `logger.warning` 输出冷却时间；
  - 冷却结束后自动重试同一请求，直到成功或超过重试上限；
  - 期间会清空签名时间戳缓存，避免因为陈旧 timestamp 导致重复封禁。

### 18.4 与运行流程的配合

- 每处理完一页即写回 `next_page`，即使进程被杀，也能准确从下一页继续；
- 详情抓取失败时不会导致段级退出，而是等待后继续处理当前记录；
- 分段之间仍执行 `SEGMENT_DELAY_RANGE (30~48s)`，与长冷却叠加保障整体节奏；
- 如需人为暂停，可直接 `Ctrl+C`，稍后重新执行同一命令，脚本会读取状态并继续。

通过以上机制，脚本在遇到风控时不会立即中断，而是自动冷却并续跑，同时保证磁盘状态与日志可观测性，大大提高长时间批量任务的稳定性。
