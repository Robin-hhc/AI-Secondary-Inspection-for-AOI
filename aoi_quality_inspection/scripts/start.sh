#!/bin/bash

# 工业AI质检系统启动脚本

set -e

echo "========================================="
echo "  工业AI质检系统启动脚本"
echo "========================================="

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose未安装"
    exit 1
fi

# 检查NVIDIA Docker (可选)
if command -v nvidia-smi &> /dev/null; then
    echo "检测到NVIDIA GPU, 启用GPU支持"
    GPU_SUPPORT=true
else
    echo "未检测到GPU, 使用CPU模式"
    GPU_SUPPORT=false
fi

# 创建必要的目录
echo "创建数据目录..."
mkdir -p data/images data/models data/feature_libs logs

# 初始化数据库
if [ ! -f "data/aoi_system.db" ]; then
    echo "初始化数据库..."
    python scripts/init_db.py
fi

# 启动服务
echo "启动服务..."
if [ "$GPU_SUPPORT" = true ]; then
    docker-compose up -d
else
    docker-compose up -d web-backend image-collector active-learning model-updater
fi

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 健康检查
echo "检查服务状态..."
docker-compose ps

echo ""
echo "========================================="
echo "  系统启动完成!"
echo "========================================="
echo ""
echo "访问地址:"
echo "  Web终端: http://localhost:5000"
echo "  API文档: http://localhost:5000/api"
echo ""
echo "默认管理员账号:"
echo "  用户名: admin"
echo "  密码: admin123"
echo ""
echo "查看日志: docker-compose logs -f"
echo "停止系统: docker-compose down"
echo ""
