# 🚀 NMPA Python爬虫后台管理系统

> **版本**: v1.0.0
> **更新时间**: 2025-10-20
> **状态**: 生产就绪 ✅

---

## 📋 目录

- [🎯 功能概述](#-功能概述)
- [🚀 快速开始](#-快速开始)
- [📊 监控仪表板](#-监控仪表板)
- [🛠️ 管理命令详解](#️-管理命令详解)
- [📄 日志管理](#-日志管理)
- [⚙️ 配置说明](#️-配置说明)
- [🔧 故障排除](#-故障排除)
- [📈 性能优化](#-性能优化)

---

## 🎯 功能概述

### 🔄 后台运行管理
- ✅ **后台启动**: 使用nohup确保进程持续运行
- ✅ **PID管理**: 自动管理进程ID文件
- ✅ **优雅停止**: 支持TERM和KILL信号
- ✅ **自动重启**: 进程异常退出时自动恢复
- ✅ **健康检查**: 定期检查进程状态

### 📊 实时监控系统
- 📈 **仪表板**: 综合状态监控界面
- 🔍 **进程监控**: CPU、内存、运行时长
- 📄 **数据统计**: 文件数量、记录总数
- 💻 **系统资源**: 负载、内存、磁盘使用
- 🔄 **实时更新**: 自动刷新监控数据

### 📝 日志管理系统
- 📂 **分类存储**: 按日期自动分类日志
- 🔄 **日志轮转**: 防止日志文件过大
- 🔍 **智能搜索**: 支持模式匹配搜索
- 📊 **统计分析**: 错误、成功、重试统计
- 📦 **自动归档**: 压缩存储历史日志

---

## 🚀 快速开始

### 📦 环境准备

确保已经安装Python依赖：
```bash
cd /path/to/nmpa_crawler_python
pip install -r requirements.txt
```

### ⚡ 一键启动

**1. 启动爬虫（后台运行）**
```bash
./manage_crawler.sh start
```

**2. 查看运行状态**
```bash
./manage_crawler.sh status
```

**3. 打开监控仪表板**
```bash
./manage_crawler.sh dashboard
```

**4. 查看实时日志**
```bash
./manage_crawler.sh logs
```

### 🛑 停止爬虫

```bash
# 优雅停止
./manage_crawler.sh stop

# 或使用后台脚本
./run_background.sh stop
```

---

## 📊 监控仪表板

### 🎮 交互式界面

启动仪表板后，您将看到实时监控界面：

```
========================================
    NMPA Python爬虫监控仪表板
========================================
时间: 2025-10-20 15:30:45

🔄 进程状态
-----------
🟢 运行中
   PID: 12345
   CPU使用率: 12.5%
   内存使用: 8.3%
   运行时长: 02:15:30

📊 数据统计
-----------
输出文件数: 15
总记录数: 3,250

最新输出文件:
  📄 国药准字H10_001.jsonl (250 记录, 45K)
  📄 国药准字H108_001.jsonl (180 记录, 32K)
  📄 国药准字H109_001.jsonl (120 记录, 28K)

📄 日志状态
-----------
活跃日志文件: 3
日志总大小: 125M

最新日志:
  📄 crawler_20251020_152045.log
  📏 大小: 45M
  🕒 更新: 2025-10-20 15:30:42

💻 系统资源
-----------
系统负载: 0.15, 0.12, 0.08
内存使用: 2.1G/8.0G (26%)
磁盘使用: 45G/100G (45%)

========================================
按 Ctrl+C 退出，按 r 刷新，输入命令执行操作
可用命令: start, stop, restart, status, logs, clean, help
```

### ⌨️ 交互命令

在仪表板中可以直接输入命令：

| 命令 | 功能 | 说明 |
|------|------|------|
| `r` 或 `refresh` | 刷新仪表板 | 重新加载所有监控数据 |
| `start` | 启动爬虫 | 如果未运行则启动 |
| `stop` | 停止爬虫 | 优雅停止运行中的进程 |
| `restart` | 重启爬虫 | 停止后重新启动 |
| `status` | 查看状态 | 显示简要状态信息 |
| `logs` | 查看日志 | 打开实时日志查看器 |
| `clean` | 清理日志 | 调用日志清理工具 |
| `help` | 显示帮助 | 列出所有可用命令 |

---

## 🛠️ 管理命令详解

### 🚀 启动管理

#### `manage_crawler.sh start`
```bash
./manage_crawler.sh start
```
- **功能**: 在后台启动爬虫进程
- **特点**:
  - 使用nohup确保断开SSH后继续运行
  - 自动创建PID文件管理进程
  - 输出同时保存到日志文件和控制台
  - 自动创建必要的目录结构

#### `run_background.sh start` (高级)
```bash
./run_background.sh start
```
- **功能**: 高级后台启动，支持更多配置
- **配置参数** (在脚本开头可修改):
  - `MAX_LOG_FILES`: 最大保留日志文件数 (默认: 10)
  - `AUTO_RESTART`: 是否自动重启 (默认: true)
  - `RESTART_DELAY`: 重启延迟秒数 (默认: 30)
  - `CHECK_INTERVAL`: 监控检查间隔 (默认: 60)

### 🛑 停止管理

#### `manage_crawler.sh stop`
```bash
./manage_crawler.sh stop
```
- **功能**: 优雅停止爬虫进程
- **流程**:
  1. 发送TERM信号请求进程停止
  2. 等待最多30秒让进程清理资源
  3. 如果未响应，发送KILL信号强制停止
  4. 清理PID文件

### 🔄 重启管理

#### `manage_crawler.sh restart`
```bash
./manage_crawler.sh restart
```
- **功能**: 重启爬虫进程
- **流程**: 先停止 → 等待2秒 → 再启动

### 📊 状态查看

#### `manage_crawler.sh status`
```bash
./manage_crawler.sh status
```
显示快速状态摘要：
```
=== NMPA爬虫快速状态 ===
🟢 运行中
   PID: 12345
   CPU使用率: 12.5%
   内存使用: 8.3%
   运行时长: 02:15:30

📊 数据: 15 文件, 3,250 记录
📄 最新日志: [INFO] 成功处理段: 国药准字H10
```

#### `manage_crawler.sh health`
```bash
./manage_crawler.sh health
```
执行全面的健康检查：
- ✅ 进程状态检查
- ✅ 日志系统检查
- ✅ 数据输出检查
- ✅ 磁盘空间检查

---

## 📄 日志管理

### 🔍 日志查看

#### 实时跟踪日志
```bash
# 查看最新日志的实时更新
./manage_crawler.sh logs

# 或使用日志管理工具
./log_manager.sh follow
```

#### 查看历史日志
```bash
# 显示最新50行日志
./log_manager.sh latest

# 显示最新100行日志
./log_manager.sh latest 100

# 列出所有日志文件
./log_manager.sh list
```

### 🔎 日志搜索

```bash
# 搜索包含"error"的日志
./log_manager.sh search "error"

# 在指定日志文件中搜索
./log_manager.sh search "国药准字H10" logs/crawler_20251020_152045.log

# 搜索特定错误模式
./log_manager.sh search "失败\|异常\|error"
```

### 📊 日志分析

```bash
# 分析最近24小时的日志
./log_manager.sh analyze

# 分析最近48小时的日志
./log_manager.sh analyze 48

# 分析统计包括：
# - 总日志行数
# - 错误/警告/成功数量
# - 爬取统计（段处理、数据写入、重试次数）
# - 最近活动和错误摘要
```

### 🧹 日志清理

```bash
# 交互式清理7天前的日志
./log_manager.sh cleanup

# 强制清理30天前的日志
./log_manager.sh cleanup-force 30

# 清理时会显示将要删除的文件并请求确认
```

### 📦 日志导出

```bash
# 导出最近7天的日志
./log_manager.sh export

# 导出最近30天的日志到指定文件
./log_manager.sh export nmpa_logs_backup.tar.gz 30

# 导出文件包含：
# - 指定时间范围内的所有日志文件
# - README.txt文件（包含统计信息和文件列表）
```

---

## ⚙️ 配置说明

### 📁 目录结构

```
nmpa_crawler_python/
├── manage_crawler.sh      # 主管理脚本
├── run_background.sh      # 后台运行脚本
├── log_manager.sh         # 日志管理脚本
├── logrotate.conf         # 日志轮转配置
├── crawler.py             # 爬虫主程序
├── requirements.txt       # Python依赖
├── outputs/               # 数据输出目录
│   └── *.jsonl           # 爬取的数据文件
├── logs/                  # 日志目录
│   ├── crawler_*.log     # 活跃日志文件
│   └── archive/          # 归档日志目录
│       └── *.gz         # 压缩的历史日志
└── crawler.pid            # 进程ID文件
```

### 🔧 脚本配置

#### run_background.sh 配置
```bash
# 在脚本开头修改这些变量
MAX_LOG_FILES=10              # 最大保留日志文件数
AUTO_RESTART=true            # 是否自动重启
RESTART_DELAY=30             # 重启延迟(秒)
CHECK_INTERVAL=60            # 监控检查间隔(秒)
```

#### 日志轮转配置 (logrotate.conf)
```bash
# 使用系统logrotate
sudo logrotate -f logrotate.conf

# 或者手动轮转
logrotate -f logrotate.conf
```

### 🌍 环境变量

可以通过环境变量覆盖默认配置：

```bash
# 设置日志保留天数
export LOG_RETENTION_DAYS=30

# 设置最大日志文件大小
export MAX_LOG_SIZE_MB=100

# 设置监控检查间隔
export MONITOR_INTERVAL=30
```

---

## 🔧 故障排除

### ❌ 常见问题

#### 1. 爬虫无法启动
```bash
# 检查依赖
python3 --version
pip list | grep -E "(requests|beautifulsoup4|lxml)"

# 检查权限
ls -la *.sh
chmod +x *.sh

# 手动启动查看错误
python3 crawler.py --log-level DEBUG
```

#### 2. 进程意外停止
```bash
# 检查系统日志
journalctl -u your-service-name  # 如果使用systemd

# 检查内存不足
free -h
dmesg | grep -i "killed process"

# 启用自动重启
./manage_crawler.sh start
```

#### 3. 日志文件过大
```bash
# 立即清理日志
./log_manager.sh cleanup-force 7

# 设置日志轮转
crontab -e
# 添加: 0 2 * * * /path/to/logrotate -f /path/to/logrotate.conf
```

#### 4. 磁盘空间不足
```bash
# 检查磁盘使用
df -h

# 清理旧日志
./log_manager.sh cleanup-force 3

# 清理旧数据（谨慎操作）
find outputs/ -name "*.jsonl" -mtime +30 -delete
```

#### 5. 权限问题
```bash
# 修复权限
chmod +x *.sh
chown -R $USER:$USER logs/ outputs/

# 检查Python环境
which python3
python3 -c "import sys; print(sys.executable)"
```

### 🔍 调试模式

#### 启用详细日志
```bash
# 停止当前进程
./manage_crawler.sh stop

# 手动启动（前台运行）
python3 crawler.py --log-level DEBUG --concurrent 2

# 查看详细错误信息
tail -f logs/crawler_*.log
```

#### 检查网络连接
```bash
# 测试目标网站连接
curl -I https://www.nmpa.gov.cn/

# 检查代理设置（如果使用）
echo $http_proxy
echo $https_proxy
```

---

## 📈 性能优化

### ⚡ 并发优化

根据系统资源调整并发数：

```bash
# 查看CPU核心数
nproc

# 推荐并发数 = CPU核心数 × 2
python3 crawler.py --concurrent 8  # 4核CPU
```

### 💾 内存优化

```bash
# 监控内存使用
./manage_crawler.sh dashboard

# 如果内存使用过高，减少并发
python3 crawler.py --concurrent 4 --max-retries 3
```

### 📂 存储优化

```bash
# 定期清理旧数据
./log_manager.sh cleanup 30

# 压缩历史数据
find outputs/ -name "*.jsonl" -mtime +7 -exec gzip {} \;
```

### 🔄 定时维护

创建定时任务进行日常维护：

```bash
# 编辑crontab
crontab -e

# 添加以下内容：
# 每天凌晨2点清理日志
0 2 * * * /path/to/nmpa_crawler_python/log_manager.sh cleanup 7

# 每天凌晨3点健康检查
0 3 * * * /path/to/nmpa_crawler_python/manage_crawler.sh health

# 每周日凌晨4点重启爬虫
0 4 * * 0 /path/to/nmpa_crawler_python/manage_crawler.sh restart
```

---

## 🎯 最佳实践

### 📋 运行建议

1. **生产环境**:
   - 使用默认配置
   - 启用自动重启
   - 保留7-14天日志
   - 每日健康检查

2. **开发环境**:
   - 减少并发数
   - 启用调试日志
   - 频繁状态检查

3. **测试环境**:
   - 使用较小的数据集
   - 短时间运行测试
   - 详细日志记录

### 🔒 安全建议

1. **权限控制**:
   ```bash
   # 限制脚本执行权限
   chmod 750 *.sh

   # 设置文件权限
   chmod 640 outputs/*.jsonl
   chmod 640 logs/*.log
   ```

2. **网络安全**:
   ```bash
   # 如果使用代理，确保代理安全
   export http_proxy="http://secure-proxy:port"

   # 定期更新依赖
   pip install --upgrade -r requirements.txt
   ```

3. **数据备份**:
   ```bash
   # 定期备份数据
   tar -czf backup_$(date +%Y%m%d).tar.gz outputs/

   # 备份到远程位置
   scp backup_*.tar.gz user@backup-server:/backup/
   ```

---

## 📞 技术支持

### 📋 问题报告

遇到问题时，请提供以下信息：

1. **系统信息**:
   ```bash
   uname -a
   python3 --version
   cat /etc/os-release
   ```

2. **运行状态**:
   ```bash
   ./manage_crawler.sh status
   ./manage_crawler.sh health
   ```

3. **日志信息**:
   ```bash
   ./log_manager.sh latest 100
   ./log_manager.sh search "error\|exception"
   ```

4. **配置信息**:
   ```bash
   ps aux | grep python3
   df -h
   free -h
   ```

### 🎯 快速诊断

```bash
# 一键诊断脚本
./manage_crawler.sh health > diagnosis.txt 2>&1
./log_manager.sh analyze 24 >> diagnosis.txt
./manage_crawler.sh status >> diagnosis.txt

# 发送diagnosis.txt给技术支持
```

---

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

---

**🎉 感谢使用 NMPA Python爬虫后台管理系统！**

如有问题或建议，欢迎提交 Issue 或 Pull Request。