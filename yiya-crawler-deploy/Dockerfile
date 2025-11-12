# 使用官方 Node.js 镜像（推荐 slim，体积小）
# FROM node:22-slim
FROM yiya-acr-registry.cn-hangzhou.cr.aliyuncs.com/yiya/yiya-crawler:v0.1

# RUN apt-get update && \
#     apt-get install -y xfonts-utils fontconfig locales zip unzip wget

# RUN locale-gen zh_CN.UTF-8 && \
#     locale-gen && \
#     wget https://yiya-dev.oss-cn-hangzhou.aliyuncs.com/drivers/fonts.zip && unzip fonts.zip && cp -r fonts/* /usr/share/fonts/ && \
#     cd /usr/share/fonts/ && mkfontscale && mkfontdir && fc-cache && fc-list :lang=zh

# ENV LANG=zh_CN.UTF-8
# ENV LANGUAGE=zh_CN:zh


# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY package*.json ./

# 安装项目依赖包
RUN npm install

# 复制项目代码
COPY . .

ENV NODE_ENV="production"
# Puppeteer 默认下载 Chromium，如果你不想重复下载可提前设置缓存
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=false
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

# 暴露端口（如果需要 Web UI）
EXPOSE 3000

# 默认命令（假设你的入口是 crawler.js）
CMD [ "node", "main.js" ]
