# 🚀 Proxy Off + Python爬虫后台运行指南

> **替代命令**: `proxy_off & python3 crawler.py --log-level DEBUG`
> **功能**: 自动关闭代理并以DEBUG模式后台运行爬虫，完整记录日志

---

## 🎯 功能特性

### ✨ 核心功能
- 🛑 **自动关闭代理**: 停止V2Ray + 清除环境变量
- 🔍 **DEBUG模式**: 详细的调试日志输出
- 🚀 **后台运行**: 使用nohup确保持续运行
- 📄 **完整日志**: 记录代理关闭和爬虫运行全过程
- 🎛️ **进程管理**: 简单的启动、停止、状态查看

### 📋 执行流程
```
1. 检查当前代理状态
2. 执行proxy_off（或内置关闭逻辑）
3. 验证代理已关闭
4. 启动DEBUG模式爬虫
5. 所有输出记录到日志文件
```

---

## 🚀 快速使用

### 📦 方法1: 一键启动（推荐）

```bash
cd ~/projects/taya/nmpa/nmpa_crawler_python
./proxy_off_crawler.sh
```

**输出示例**:
```
[15:31:03] 🚀 启动NMPA爬虫 (DEBUG模式 + 代理关闭)
[15:31:03] 📄 日志文件: logs/crawler_debug_20251020_153103.log
[15:31:05] ✅ 已在后台启动! PID: 4082590

🔍 管理命令:
  查看状态: ps -p 4082590
  查看日志: tail -f logs/crawler_debug_20251020_153103.log
  停止进程: kill 4082590
  删除PID: rm -f crawler_proxy_off.pid
[15:31:08] 🎉 进程运行正常
```

### 📋 方法2: 直接命令（简单）

如果您更喜欢直接命令，可以使用：

```bash
# 创建日志目录
mkdir -p logs

# 一行命令后台运行
nohup bash -c '
    echo "[$(date)] 开始运行"
    proxy_off 2>/dev/null || { pkill -f v2ray; unset http_proxy https_proxy all_proxy; }
    sleep 2
    echo "[$(date)] 启动爬虫..."
    python3 crawler.py --log-level DEBUG
' > logs/crawler_debug_$(date +%Y%m%d_%H%M%S).log 2>&1 &
```

### 🛠️ 方法3: 管理脚本（功能完整）

```bash
# 启动
./final_proxy_off_runner.sh start

# 查看状态
./final_proxy_off_runner.sh status

# 查看日志
./final_proxy_off_runner.sh logs

# 停止
./final_proxy_off_runner.sh stop
```

---

## 📊 日志管理

### 📄 日志文件位置

- **文件格式**: `logs/crawler_debug_YYYYMMDD_HHMMSS.log`
- **内容包含**:
  - 代理状态变化
  - V2Ray停止过程
  - 环境变量清除
  - DEBUG级别爬虫日志
  - 详细的HTTP请求/响应信息

### 🔍 查看日志

```bash
# 查看最新日志
tail -f logs/crawler_debug_*.log

# 查看特定日志
tail -f logs/crawler_debug_20251020_153103.log

# 查看日志开头（检查代理关闭过程）
head -20 logs/crawler_debug_20251020_153103.log

# 搜索特定内容
grep "代理" logs/crawler_debug_*.log
grep "DEBUG" logs/crawler_debug_*.log
grep "ERROR" logs/crawler_debug_*.log
```

### 📋 日志示例

```log
[2025-10-20 15:31:03] ========== 开始运行 ==========
[2025-10-20 15:31:03] 当前代理状态:
  http_proxy: 'http://127.0.0.1:7890'
  https_proxy: 'http://127.0.0.1:7890'
  all_proxy: '未设置'
[2025-10-20 15:31:03] 执行proxy_off...
[2025-10-20 15:31:03] V2Ray已停止
[2025-10-20 15:31:03] 代理环境变量已清除
[2025-10-20 15:31:06] 代理关闭后状态:
  http_proxy: '未设置'
  https_proxy: '未设置'
  all_proxy: '未设置'
[2025-10-20 15:31:06] 启动DEBUG模式爬虫...
2025-10-20 15:31:06 | DEBUG | 日志级别已设置为 DEBUG
2025-10-20 15:31:06 | INFO | 【启动】NMPA 爬虫启动，基础关键词=['国药准字H', '国药准字S']
2025-10-20 15:31:06 | DEBUG | Starting new HTTPS connection (1): www.nmpa.gov.cn:443
```

---

## 🎛️ 进程管理

### 📈 查看运行状态

```bash
# 方法1: 使用PID文件
if [ -f crawler_proxy_off.pid ]; then
    ps -p $(cat crawler_proxy_off.pid)
fi

# 方法2: 查找进程
ps aux | grep python3.*crawler | grep -v grep

# 方法3: 使用管理脚本
./final_proxy_off_runner.sh status
```

### 🛑 停止进程

```bash
# 方法1: 使用PID文件
if [ -f crawler_proxy_off.pid ]; then
    kill $(cat crawler_proxy_off.pid)
    rm -f crawler_proxy_off.pid
fi

# 方法2: 查找并停止
pkill -f "python3.*crawler.*--log-level DEBUG"

# 方法3: 使用管理脚本
./final_proxy_off_runner.sh stop
```

### 🔄 重启进程

```bash
# 停止当前进程
./proxy_off_crawler.sh stop 2>/dev/null || true

# 等待完全停止
sleep 2

# 重新启动
./proxy_off_crawler.sh
```

---

## 🔧 故障排除

### ❌ 常见问题

#### 1. 进程启动失败

**现象**: 提示"进程启动失败"

**解决方案**:
```bash
# 查看详细错误日志
tail -20 logs/crawler_debug_*.log

# 检查Python环境
python3 --version
which python3

# 检查爬虫文件
ls -la crawler.py
python3 crawler.py --help
```

#### 2. 代理未完全关闭

**现象**: 日志显示代理仍然开启

**解决方案**:
```bash
# 手动关闭代理
proxy_off

# 或者强制关闭
pkill -f v2ray
unset http_proxy https_proxy all_proxy

# 验证代理状态
echo "http_proxy: ${http_proxy:-未设置}"
echo "https_proxy: ${https_proxy:-未设置}"
```

#### 3. 日志文件权限问题

**现象**: 无法写入日志文件

**解决方案**:
```bash
# 检查目录权限
ls -la logs/

# 修复权限
chmod 755 logs/
chmod 644 logs/*.log

# 重新创建目录
rm -rf logs/
mkdir -p logs
```

#### 4. 进程意外退出

**现象**: 进程启动后很快退出

**解决方案**:
```bash
# 查看退出原因
tail -50 logs/crawler_debug_*.log

# 检查系统资源
df -h
free -h

# 前台运行测试
python3 crawler.py --log-level DEBUG
```

### 🔍 调试技巧

#### 启用详细调试
```bash
# 前台运行查看详细输出
bash -x ./proxy_off_crawler.sh

# 手动执行每个步骤
proxy_off
python3 crawler.py --log-level DEBUG
```

#### 检查系统状态
```bash
# 查看系统负载
uptime
htop

# 查看网络连接
netstat -tuln | grep :7890

# 查看进程树
pstree -p | grep python
```

---

## 💡 最佳实践

### 🎯 推荐使用流程

1. **首次使用**:
   ```bash
   # 测试proxy_off功能
   proxy_off
   echo "代理状态: http_proxy=${http_proxy:-未设置}"

   # 测试爬虫启动
   python3 crawler.py --log-level DEBUG --help

   # 使用脚本启动
   ./proxy_off_crawler.sh
   ```

2. **日常使用**:
   ```bash
   # 一键启动
   ./proxy_off_crawler.sh

   # 查看状态
   ps -p $(cat crawler_proxy_off.pid 2>/dev/null)

   # 查看日志
   tail -f logs/crawler_debug_*.log
   ```

3. **监控管理**:
   ```bash
   # 设置定时检查
   echo "*/10 * * * * /path/to/check_crawler.sh" | crontab -

   # 定期清理日志
   find logs/ -name "*.log" -mtime +7 -delete
   ```

### 📋 自动化脚本

创建监控脚本 `check_crawler.sh`:
```bash
#!/bin/bash
PID_FILE="crawler_proxy_off.pid"

if [ -f "$PID_FILE" ]; then
    pid=$(cat "$PID_FILE")
    if ps -p "$pid" > /dev/null; then
        echo "✅ 爬虫运行正常 (PID: $pid)"
    else
        echo "❌ 爬虫已停止，重新启动..."
        ./proxy_off_crawler.sh
    fi
else
    echo "⚠️ PID文件不存在，启动爬虫..."
    ./proxy_off_crawler.sh
fi
```

### 🔒 安全建议

1. **权限控制**:
   ```bash
   chmod 700 proxy_off_crawler.sh
   chmod 700 logs/
   ```

2. **日志轮转**:
   ```bash
   # 每天清理旧日志
   find logs/ -name "*.log" -mtime +3 -delete
   ```

3. **进程监控**:
   ```bash
   # 设置systemd服务（推荐生产环境）
   sudo cp nmpa-crawler.service /etc/systemd/system/
   sudo systemctl enable nmpa-crawler
   sudo systemctl start nmpa-crawler
   ```

---

## 📞 快速参考

### 🚀 常用命令

```bash
# 启动
./proxy_off_crawler.sh

# 查看状态
ps -p $(cat crawler_proxy_off.pid 2>/dev/null)

# 查看日志
tail -f logs/crawler_debug_*.log

# 停止
kill $(cat crawler_proxy_off.pid 2>/dev/null); rm -f crawler_proxy_off.pid

# 重启
./proxy_off_crawler.sh stop 2>/dev/null; sleep 2; ./proxy_off_crawler.sh
```

### 📁 文件位置

- **主脚本**: `./proxy_off_crawler.sh`
- **PID文件**: `./crawler_proxy_off.pid`
- **日志目录**: `./logs/`
- **日志格式**: `./logs/crawler_debug_YYYYMMDD_HHMMSS.log`

---

**🎉 现在您可以使用 `./proxy_off_crawler.sh` 来替代 `proxy_off & python3 crawler.py --log-level DEBUG`，享受完整的后台运行和日志管理功能！**