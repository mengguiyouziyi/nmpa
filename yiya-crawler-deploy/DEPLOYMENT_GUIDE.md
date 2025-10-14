# yiya-crawler 部署指南

## 📋 环境要求

### Docker环境（推荐）
- Docker Engine >= 20.0
- Docker Compose >= 2.0
- 内存 >= 2GB
- 磁盘空间 >= 5GB

### 本地环境（备选）
- Node.js >= 20.0.0
- npm >= 9.0.0
- Chromium浏览器（Puppeteer使用）
- MySQL 8.0+（可选）

## 🚀 快速部署

### 方式1: Docker Compose部署（推荐）

```bash
# 1. 克隆项目到部署目录
git clone <repository-url> yiya-crawler-deploy
cd yiya-crawler-deploy

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填写实际的配置

# 3. 启动服务
docker-compose up -d

# 4. 查看运行状态
docker-compose ps

# 5. 查看日志
docker-compose logs -f yiya-crawler
```

### 方式2: 直接构建Docker镜像

```bash
# 1. 构建镜像
docker build -t yiya-crawler:latest .

# 2. 运行容器
docker run -d \
  --name yiya-crawler \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/downloads:/app/downloads \
  --env-file .env \
  yiya-crawler:latest

# 3. 查看日志
docker logs -f yiya-crawler
```

### 方式3: 本地Node.js部署

```bash
# 1. 安装Node.js 20+
# 使用nvm安装
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 20
nvm use 20

# 2. 安装依赖
npm install

# 3. 安装Puppeteer浏览器
npx puppeteer install

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 5. 启动应用
npm start
```

## ⚙️ 配置说明

### 环境变量配置

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `YIYA_JOB_FREQUENCY` | 任务执行频率（分钟） | 60 | 否 |
| `DB_HOST` | 数据库主机 | localhost | 否 |
| `DB_PORT` | 数据库端口 | 3306 | 否 |
| `DB_NAME` | 数据库名称 | yiya_crawler | 否 |
| `DB_USER` | 数据库用户 | yiya | 否 |
| `DB_PASSWORD` | 数据库密码 | yiya123 | 否 |
| `LOG_LEVEL` | 日志级别 | info | 否 |
| `CRAWLER_HEADLESS` | 无头模式 | true | 否 |
| `CRAWLER_TIMEOUT` | 超时时间(ms) | 30000 | 否 |
| `CRAWLER_DELAY` | 延迟时间(ms) | 1000 | 否 |

### 阿里云OSS配置（可选）

如果需要上传文件到阿里云OSS，请配置以下变量：

```bash
OSS_REGION=oss-cn-hangzhou
OSS_ACCESS_KEY_ID=your_access_key_id
OSS_ACCESS_KEY_SECRET=your_access_key_secret
OSS_BUCKET=your_bucket_name
```

## 📁 目录结构

```
yiya-crawler-deploy/
├── 📜 配置文件
│   ├── .env                    # 环境变量配置
│   ├── .env.example           # 环境变量示例
│   ├── package.json           # 项目配置
│   ├── Dockerfile             # Docker镜像构建文件
│   └── docker-compose.yml     # Docker Compose配置
│
├── 🚀 源代码
│   ├── main.js                # 主入口文件
│   ├── src/                   # 源代码目录
│   │   ├── crawlers/          # 爬虫模块
│   │   ├── services/          # 服务模块
│   │   ├── utils/             # 工具模块
│   │   └── config/            # 配置模块
│   └── node_modules/          # 依赖包
│
├── 📁 数据目录
│   ├── outputs/               # 输出数据
│   ├── downloads/             # 临时下载
│   └── logs/                  # 日志文件
│
└── 📖 文档
    ├── DEPLOYMENT_GUIDE.md    # 部署指南
    └── README.md              # 项目说明
```

## 🔧 运维管理

### 查看运行状态

```bash
# Docker Compose方式
docker-compose ps

# Docker方式
docker ps | grep yiya-crawler

# 本地方式
ps aux | grep "node main.js"
```

### 查看日志

```bash
# Docker Compose方式
docker-compose logs -f yiya-crawler

# Docker方式
docker logs -f yiya-crawler

# 本地方式
tail -f logs/app.log
```

### 重启服务

```bash
# Docker Compose方式
docker-compose restart yiya-crawler

# Docker方式
docker restart yiya-crawler

# 本地方式
# 先停止进程，再重新启动
pkill -f "node main.js"
npm start
```

### 更新部署

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重新构建镜像
docker-compose build

# 3. 重启服务
docker-compose up -d
```

### 数据备份

```bash
# 备份输出数据
tar -czf outputs-$(date +%Y%m%d).tar.gz outputs/

# 备份数据库（如果使用）
docker-compose exec mysql mysqldump -u root -p yiya_crawler > mysql-backup-$(date +%Y%m%d).sql
```

## 🚨 故障排除

### 常见问题

#### 1. 容器启动失败
```bash
# 检查容器状态
docker-compose ps

# 查看错误日志
docker-compose logs yiya-crawler

# 检查配置文件
cat .env
```

#### 2. 内存不足
```bash
# 增加Docker内存限制
# 编辑 docker-compose.yml，添加：
services:
  yiya-crawler:
    deploy:
      resources:
        limits:
          memory: 4G
```

#### 3. 网络连接问题
```bash
# 检查网络连接
docker-compose exec yiya-crawler ping www.nmpa.gov.cn

# 重置网络
docker-compose down
docker-compose up -d
```

#### 4. 依赖安装失败
```bash
# 清理npm缓存
npm cache clean --force

# 重新安装依赖
rm -rf node_modules package-lock.json
npm install
```

### 性能优化

#### 1. 调整并发数
编辑 `src/config/constants.js`，调整爬虫并发参数。

#### 2. 优化数据库
```sql
-- 添加索引
CREATE INDEX idx_created_at ON crawler_results(created_at);
CREATE INDEX idx_source ON crawler_results(source);
```

#### 3. 增加缓存
使用Redis缓存频繁访问的数据。

## 📊 监控和报警

### 日志监控

```bash
# 监控错误日志
docker-compose logs -f yiya-crawler | grep ERROR

# 统计成功/失败次数
docker-compose logs yiya-crawler | grep -c "completed successfully"
```

### 资源监控

```bash
# 查看容器资源使用
docker stats yiya-crawler

# 查看磁盘使用
df -h
```

### 健康检查

在 `docker-compose.yml` 中添加健康检查：

```yaml
services:
  yiya-crawler:
    healthcheck:
      test: ["CMD", "pgrep", "-f", "node main.js"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## 🔐 安全配置

### 1. 环境变量安全
- 不要将 `.env` 文件提交到版本控制
- 使用强密码和安全的访问密钥
- 定期轮换密钥

### 2. 网络安全
- 使用防火墙限制访问
- 启用HTTPS（如果有Web界面）
- 定期更新系统和依赖

### 3. 数据安全
- 定期备份重要数据
- 加密敏感信息
- 设置适当的文件权限

## 📞 技术支持

### 日志位置
- 应用日志：`logs/app.log`
- 错误日志：`logs/error.log`
- Docker日志：`docker-compose logs yiya-crawler`

### 配置文件
- 主配置：`.env`
- 应用配置：`src/config/constants.js`
- 爬虫配置：`src/config/sites.js`

### 联系方式
- 项目Issues：提交GitHub Issues
- 技术文档：查看项目Wiki
- 更新日志：关注项目Releases

---

*部署指南最后更新: 2025年10月14日*