# NMPA 有头自动化点击脚本

本目录提供一个使用 **DrissionPage** 驱动 Chrome 浏览器的交互脚本，模拟人工在国家药监局数据检索页面上的基本操作（搜索、翻页、查看详情）。配合主 `requests` 爬虫一起运行，可定期向官网发送“有人在浏览”的信号，降低连续 API 请求的可疑性。

## 主要特性

- **有头浏览器**：DrissionPage 直接调用本地 Chrome，便于实时观察。
- **随机动作节奏**：输入、滚动、点击之间穿插自然的随机延时。
- **自动详情与翻页**：每轮尝试点击列表首条详情，并在成功后翻页一次。
- **10 分钟节奏**：默认每 600 秒执行一次完整流程，可通过参数调整。
- **异常自愈**：元素不存在或点击失败时自动降级处理，不影响下一轮。

## 快速开始

1. 准备 Python 环境，安装依赖：
   ```bash
   pip install -r requirements.txt
   python -m DrissionPage down-driver  # 首次运行下载匹配驱动
   ```

2. 启动自动化脚本：
   ```bash
   python automation.py \
     --interval 1800 \
     --keyword "国药准字H" \
     --keyword "国药准字S" \
     --headless \
     --log-file automation.log
   ```

   参数说明：
- `--interval`：两轮之间的目标间隔（秒），默认 1800（30 分钟）。
   - `--keyword`：添加一个搜索关键词，可多次指定；若不指定，默认轮换 `国药准字H/S/Z`。
- `--once`：仅运行一轮后退出。
- `--headless`：在服务器环境下建议开启，自动添加 `--headless=new`、`--no-sandbox` 等参数。
- `--log-file`：可选，将日志写入文件，便于与主爬虫日志分离。

3. 与 requests 爬虫协同：
   - 建议使用 `tmux`/`screen` 等守护工具分别运行自动化脚本与主爬虫。
   - 自动化脚本只负责浏览器模拟，不会写出任何数据文件，可与爬虫共用同一台机器。
   - 若 Chrome 版本更新，请重新执行 `pip install -r requirements.txt` 以自动下载新的驱动。

## 目录结构

```
nmpa_drission/
  automation.py      # 主程序
  requirements.txt   # 依赖清单（DrissionPage）
  README.md          # 使用说明
```

## 常见问题

1. **弹出窗口过多**：脚本默认关闭详情页新标签；如遇官网弹窗，需要手动关闭或扩展脚本处理逻辑。
2. **浏览器无法启动**：确保已安装 Chrome 并执行 `python -m DrissionPage down-driver` 下载驱动；无图形环境可通过远程桌面/虚拟显示器运行。
3. **元素定位失败**：官网前端若更新，可调整 `automation.py` 中 `_click_detail`、`_click_next_page` 的选择器。

如需进一步伪装（代理切换、手势模拟等），可基于当前脚本继续扩展。提交 Issues 或 PR 以共享更稳健的方案。***

## 定期更新脚本

为了便于日常增量更新，仓库新增了三个轻量化入口，可在项目根目录按需执行：

```bash
# 境内品种（默认一次更新 20 个分段，可通过 --max-segments 调整）
python crawler_update.py --log-level INFO --max-segments 20

# 境外品种（默认抓取国药准字H/S，可叠加 --query 指定前缀）
python crawler_jingwai_update.py --log-level INFO

# 原料药（默认仅抓取前 5 页，可通过 --max-pages 控制）
python crawler_yuanliaoyao_update.py --log-level INFO --max-pages 5
```

完整抓取仍可直接运行 `crawler.py`、`crawler_jingwai.py`、`crawler_yuanliaoyao.py`。原料药数据会输出到 `outputs_yuanliaoyao/原料药.jsonl`，并可通过 `python yly_to_excel.py` 生成对应的 `原料药.xlsx`。
