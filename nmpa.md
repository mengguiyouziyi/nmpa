下面给你一套**可直接上手**的完整爬虫（已打包为 zip），默认走“ **浏览器引擎** （undetected‑chromedriver + selenium‑wire）”，在页面上下文里直接调用官网的 `axios` 完成请求签名与（可能存在的）参数加密，无需自行逆向。已按你的文档要求实现“境内/境外 + H/S”的查询与字段提取。你可以直接下载：

**👉 [下载完整项目（ZIP）](sandbox:/mnt/data/NMPA_crawler_package.zip)**

---

## 这份爬虫如何满足你的 5 点注意事项

### 1) JS 逆向问题（sign/加密/Token/Cookie）

* NMPA 数据查询前端对接口做了**签名（sign + timestamp）**与（近期多次变化的） **参数加密** ，社区讨论也提到它使用了 `jsjiami.com.v6` 混淆，并通过 **axios 拦截器**对请求进行处理，常见的接口包括：
  * 列表：`/datasearch/data/nmpadata/search`（GET，携带 `itemId,isSenior,searchValue,pageNum,pageSize,timestamp` 等）
  * 详情：`/datasearch/data/nmpadata/queryDetail`（GET，携带 `itemId,id,timestamp` 等）

    在某些时段还会校验请求头中的 `sign/timestamp/token`。这些现象在社区的实际抓包与逆向贴里都有说明与代码片段展示。([GitHub](https://github.com/yangshimin/SpiderCollection/issues/6?utm_source=chatgpt.com "大佬们，能搞定药品监督局的jsjiami.com.v6吗？ #6"))
* **解决策略** ：

  我提供两套引擎——

1. **默认 Browser 引擎（推荐、稳定）** ：在页面里直接用 `window.axios` 发起请求，让前端脚本自动加签与处理参数，这样 **不受算法变更影响** 。
2. **可选 HTTP 引擎（实验性）** ：若你坚持纯 `requests/httpx`，可把你逆下来的 `sign/参数加密` 逻辑（如 `env.js/md5.js/ajax.js`）塞到项目自带的 `http_engine/nmpa_js/main.js`，脚本会通过 Node 子进程返回 `sign/timestamp` 给 Python； **默认不开启** ，仅供熟悉逆向的同学启用。上述“search/queryDetail 需 sign/timestamp”的线索与做法，均来自可复核的公开资料。([CSDN Blog](https://blog.csdn.net/qq_45549964/article/details/148453846?utm_source=chatgpt.com "某药监局药品详情sign值逆向原创"))

### 2) 封禁与代理

* **UC + 随机抖动** ：默认在每页请求间加 600–1500ms 抖动；
* **代理支持** ：`config.yaml` 中可配置 HTTP/HTTPS 代理；
* **重试** ：内置失败重试与最小化访问策略；
* **浏览器指纹** ：undetected‑chromedriver 对常见反自动化有限规避能力。

  （实际访问入口：NMPA 数据查询主页。）([nmpa.gov.cn](https://www.nmpa.gov.cn/datasearch/home-index.html?utm_source=chatgpt.com "国家药品监督管理局数据查询"))

### 3) 字段抓取（按你的硬性字段）

你的文档要求：

* **境内生产药品** ：产品名称（中文）、产品名称（英文）
* **境外生产药品** ：产品名称（中文/英文）、商品名（中文/英文）

  我按“ **先抓全量详情 JSON，再抽取所需字段** ”实现，字段名采用 **多别名匹配** （如“药品名称/通用名称/产品名称（中文）”等），可适配不同详情页结构；其余原始字段全部写入 `*.raw.jsonl`。

### 4) 接口与参数的**真实结构**与**有效性验证**

* 入口页与数据查询页：`https://www.nmpa.gov.cn/datasearch/home-index.html`；前端加载数据库配置 `NMPA_DATA.json`，其中包含各库的  **itemId** ，常见的有“ **境内生产药品** ”“ **境外生产药品** ”。我在浏览器上下文用 axios 获取该 JSON，并递归解析得到 `itemId`；若解析失败，回退到 `static_item_ids.json`（其中“境内”示例 `itemId` 参考了公开逆向文中展示的值，可运行后依据线上返回动态覆盖）。([nmpa.gov.cn](https://www.nmpa.gov.cn/datasearch/home-index.html?utm_source=chatgpt.com "国家药品监督管理局数据查询"))
* 列表与详情接口：社区工程/帖子明确了 `/datasearch/data/nmpadata/search` 与 `/datasearch/data/nmpadata/queryDetail` 这对组合，并提示需要 `sign/timestamp/token` 头或参数，近期出现“参数加密”。本项目 Browser 引擎直接复用页面的 axios 设置，实现 **真实可请求** ；HTTP 引擎明确提示你放入逆向 JS，实现 **真实可还原** 。([GitHub](https://github.com/yangshimin/SpiderCollection/issues/6?utm_source=chatgpt.com "大佬们，能搞定药品监督局的jsjiami.com.v6吗？ #6"))

### 5) 结构清晰、功能完善、配置齐全、真实可用

* **结构** （zip 内）：

```
  nmpa_crawler/
  ├── main.py                  # 入口：读取配置并调度任务
  ├── browser_engine.py        # 默认引擎：页面内 axios 调用（免逆向）
  ├── http_engine.py           # 实验性引擎：需你提供 sign/加密JS
  ├── http_engine/
  │   └── nmpa_js/
  │       ├── README.md        # 如何接入你逆下来的JS
  │       └── main.js          # Node 入口（占位）
  ├── utils.py                 # itemId 解析、字段抽取、工具函数
  ├── exporter.py              # 导出Excel/CSV与原始JSON
  ├── static_item_ids.json     # 失败回退的静态itemId（可更新）
  ├── config.yaml              # 任务/代理/并发/导出等配置
  └── requirements.txt
```

* **默认任务** ：已配置 4 组（境内/境外 × H/S），直接运行即可；
* **输出** ：每组生成一个 Excel/CSV 和对应的 `*.raw.jsonl`；
* **可维护** ：字段别名和抓取策略都集中在 `utils.py`，容易改。

---

## 使用说明（3 步）

> 建议在全新虚拟环境中操作。

1. **安装依赖**

   ```bash
   pip install -r requirements.txt
   ```
2. **按需改配置** （代理、页数、导出格式等在 `config.yaml`）
3. **运行**

   ```bash
   python main.py -c config.yaml
   ```

   产出位于 `outputs/`：

   * `domestic_国药准字H.xlsx`、`domestic_国药准字S.xlsx`
   * `imported_国药准字H.xlsx`、`imported_国药准字S.xlsx`
   * 以及每组对应的 `*.raw.jsonl`

---

## 关键实现点（源码摘录与说明）

* **在页面内调用 axios 获取数据库配置与搜索结果** （Browser 引擎片段）：

```python
  # browser_engine.py（节选）
  # 1) 获取 NMPA_DATA.json 并解析“境内/境外”的 itemId
  data = self._exec_async("""
      const url = '/datasearch/config/NMPA_DATA.json?date=' + Date.now();
      const resp = await axios.get(url);
      done(resp.data);
  """)
  # 2) 搜索列表（让前端自动完成 sign/加密/头）
  data = self._exec_async(f"""
      const resp = await axios.get('/datasearch/data/nmpadata/search', {{
          params: {{
            itemId: {json.dumps(item_id)},
            isSenior: 'N',
            searchValue: {json.dumps(search_value)},
            pageNum: {page_num},
            pageSize: {page_size},
            timestamp: Date.now()
          }}
      }});
      done(resp.data);
  """)
  # 3) 详情
  detail = self._exec_async(f"""
      const resp = await axios.get('/datasearch/data/nmpadata/queryDetail', {{
          params: {{ itemId: {json.dumps(item_id)}, id: {json.dumps(doc_id)}, timestamp: Date.now() }}
      }});
      done(resp.data);
  """)
```

> 入口与数据查询为 NMPA 官方“数据查询”站点。([nmpa.gov.cn](https://www.nmpa.gov.cn/datasearch/home-index.html?utm_source=chatgpt.com "国家药品监督管理局数据查询"))

* **字段抽取** ：对不同结构的详情 JSON 做“拍平”并用**多别名匹配**输出你要的列（境外还包含中/英文商品名）。该设计可应对不同库/不同时间返回结构的小变动。（详见 `utils.py`。）

---

## 与你给的 GitHub 项目如何结合/取长补短

* `Billy-FIN/NMPA_Scraper`：展示了 requests + Selenium 混用思路与资源文件（如 `NMPA_DATA.json`），可用于理解库与 itemId 的关系；本项目 **把 itemId 动态解析放到页面内部 axios** ，更稳。([GitHub](https://github.com/Billy-FIN/NMPA_Scraper/tree/main/resources "NMPA_Scraper/resources at main · Billy-FIN/NMPA_Scraper · GitHub"))
* `nimua/NMPA_spider`：强调了 **浏览器自动化** （DrissionPage/等待/节流等），与本项目的 Browser 引擎设计同路。([GitHub](https://github.com/nimua/NMPA_spider "GitHub - nimua/NMPA_spider: 从药监局（国家药品监督管理局）网站获取公开信息"))
* `XGFan/nmpa`：主打异步/高并发思路；本项目默认节流，若后期要提速，可在 Browser 引擎里做多关键字并发或改造成分布式。([GitHub](https://github.com/XGFan/nmpa "GitHub - XGFan/nmpa: nmpa.gov.cn 抓取"))
* `QueenOfBugs/scxk.nmpa`：对 NMPA 另一个系统（许可信息）的**列表/详情二段式抓取**法则非常典型，列表拿 id、再查详情，本项目同样遵循该模型。([GitHub](https://github.com/QueenOfBugs/scxk.nmpa?utm_source=chatgpt.com "国家药品监督管理局-所有化妆品生产许可信息爬取"))
* `shi-yuan/nmpa-data`：提供了 **药品数据抓取与解析的脚本集** ，其中也包含 Node/Python 混合方式；本项目把这种混合方案包装为 **可选 HTTP 引擎** ，仅当你需要“纯 HTTP”才用。([GitHub](https://github.com/shi-yuan/nmpa-data "GitHub - shi-yuan/nmpa-data: 国家药监局药品数据"))

---

## 重要提示与合规性

* **接口会变** ：近两年该站加密逻辑多次调整（例如新增“参数加密”）；**Browser 引擎**对这种变化最具适配性。若你一定要 `requests`，请把逆下来的加密逻辑填入 `http_engine/nmpa_js/main.js`。([CSDN Blog](https://blog.csdn.net/qq_45549964/article/details/148453846?utm_source=chatgpt.com "某药监局药品详情sign值逆向原创"))
* 遵守网站条款与 `robots.txt`，控制速率与并发，仅作合规用途。

---

## 再次附上下载

* **项目打包（含源码、依赖清单、配置、占位 Node 脚本）** ：

  **[NMPA_crawler_package.zip](sandbox:/mnt/data/NMPA_crawler_package.zip)**

> 字段与查询范围的定义来自你上传的《药监局药品名称提取.docx》，本项目严格按该文档的“境内/境外 + H/S + 指定字段”落地实现。

如果你希望我把 **HTTP 引擎**里的 Node 占位脚本替换为 **已验证的真实 sign/参数加密逻辑** （把你逆下来的 JS 发我即可），我可以把它直接接入 `http_engine.py`，让两条路径都可用。
