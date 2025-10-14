#!/bin/bash

# yiya-crawler 自动部署脚本
# 作者: Claude Code
# 版本: 1.0.0

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi

    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi

    log_success "系统依赖检查通过"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."

    mkdir -p outputs downloads logs

    log_success "目录创建完成"
}

# 配置环境变量
setup_environment() {
    log_info "配置环境变量..."

    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            log_warning "已从 .env.example 创建 .env 文件，请根据需要修改配置"
        else
            log_error "缺少 .env.example 文件"
            exit 1
        fi
    else
        log_info ".env 文件已存在，跳过创建"
    fi

    log_success "环境变量配置完成"
}

# 构建Docker镜像
build_image() {
    log_info "构建Docker镜像..."

    if docker-compose build; then
        log_success "Docker镜像构建成功"
    else
        log_error "Docker镜像构建失败"
        exit 1
    fi
}

# 启动服务
start_services() {
    log_info "启动服务..."

    if docker-compose up -d; then
        log_success "服务启动成功"
    else
        log_error "服务启动失败"
        exit 1
    fi
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务就绪..."

    # 等待容器启动
    sleep 10

    # 检查容器状态
    if docker-compose ps | grep -q "Up"; then
        log_success "服务已就绪"
    else
        log_error "服务启动异常"
        docker-compose ps
        exit 1
    fi
}

# 显示状态
show_status() {
    log_info "服务状态："
    docker-compose ps

    echo ""
    log_info "最近的日志："
    docker-compose logs --tail=20 yiya-crawler
}

# 清理函数
cleanup() {
    if [ $? -ne 0 ]; then
        log_error "部署失败，正在清理..."
        docker-compose down 2>/dev/null || true
    fi
}

# 主函数
main() {
    log_info "开始部署 yiya-crawler..."
    echo "========================================"

    # 设置清理陷阱
    trap cleanup EXIT

    # 执行部署步骤
    check_dependencies
    create_directories
    setup_environment
    build_image
    start_services
    wait_for_services
    show_status

    echo "========================================"
    log_success "yiya-crawler 部署完成！"
    echo ""
    echo "📋 管理命令："
    echo "  查看状态: docker-compose ps"
    echo "  查看日志: docker-compose logs -f yiya-crawler"
    echo "  重启服务: docker-compose restart yiya-crawler"
    echo "  停止服务: docker-compose down"
    echo ""
    echo "📁 数据目录："
    echo "  输出文件: ./outputs/"
    echo "  下载文件: ./downloads/"
    echo "  日志文件: ./logs/"
    echo ""
    echo "⚙️ 配置文件："
    echo "  环境配置: .env"
    echo "  应用配置: src/config/constants.js"
}

# 解析命令行参数
case "${1:-}" in
    "build")
        log_info "仅构建镜像..."
        build_image
        ;;
    "start")
        log_info "启动服务..."
        start_services
        show_status
        ;;
    "stop")
        log_info "停止服务..."
        docker-compose down
        ;;
    "restart")
        log_info "重启服务..."
        docker-compose restart
        show_status
        ;;
    "logs")
        docker-compose logs -f yiya-crawler
        ;;
    "status")
        show_status
        ;;
    "clean")
        log_info "清理资源..."
        docker-compose down -v
        docker system prune -f
        ;;
    *)
        main
        ;;
esac