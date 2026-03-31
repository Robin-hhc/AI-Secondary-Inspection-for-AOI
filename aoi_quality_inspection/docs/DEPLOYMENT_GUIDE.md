# 工业AI质检系统部署指南

## 1. 环境要求

### 1.1 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 4核 | 8核+ |
| 内存 | 8GB | 16GB+ |
| 存储 | 100GB SSD | 500GB SSD |
| GPU | - | NVIDIA GPU 8GB+ |

### 1.2 软件要求

| 软件 | 版本 |
|------|------|
| 操作系统 | Ubuntu 20.04/22.04 或 Windows 10+ |
| Docker | 20.10+ |
| Docker Compose | 2.0+ |
| NVIDIA Docker | 2.0+ (GPU部署) |
| Python | 3.8+ |

## 2. 部署方式

### 2.1 Docker部署 (推荐)

#### 2.1.1 安装Docker

**Ubuntu:**

```bash
# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 安装NVIDIA Docker (GPU支持)
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

**Windows:**

下载并安装 [Docker Desktop](https://www.docker.com/products/docker-desktop)

#### 2.1.2 部署系统

```bash
# 1. 克隆项目
git clone <repository_url>
cd aoi_quality_inspection

# 2. 配置环境变量 (可选)
cp .env.example .env
# 编辑.env文件

# 3. 启动系统
bash scripts/start.sh

# 4. 检查服务状态
docker-compose ps

# 5. 查看日志
docker-compose logs -f
```

### 2.2 手动部署

#### 2.2.1 安装Python环境

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 2.2.2 安装CUDA和TensorRT (GPU部署)

```bash
# 安装CUDA Toolkit
# 参考: https://developer.nvidia.com/cuda-downloads

# 安装TensorRT
# 参考: https://developer.nvidia.com/tensorrt
```

#### 2.2.3 初始化系统

```bash
# 初始化数据库
python scripts/init_db.py

# 准备模型文件
# 将预训练模型放到 models/ 目录
```

#### 2.2.4 启动服务

```bash
# 启动Web服务
python web_terminal/backend/app.py

# 启动推理引擎 (另一个终端)
python inference_engine/server.py

# 启动图像采集服务 (另一个终端)
python image_collector/collector_service.py
```

## 3. 配置说明

### 3.1 主配置文件

编辑 `config/config.yaml`:

```yaml
# 数据库配置
system:
  database:
    path: "./data/aoi_system.db"

# 推理引擎配置
inference:
  model:
    backbone: "wide_resnet50"
    input_size: [256, 256]
  threshold:
    anomaly_threshold: 0.5

# Web服务配置
web:
  backend:
    host: "0.0.0.0"
    port: 5000
```

### 3.2 环境变量

创建 `.env` 文件:

```bash
# 数据库路径
DB_PATH=./data/aoi_system.db

# 模型路径
MODEL_PATH=./models/feature_extractor.onnx

# GPU设备
CUDA_VISIBLE_DEVICES=0

# Web服务端口
WEB_PORT=5000
```

## 4. 数据准备

### 4.1 准备正常样本

对于新产品,需要准备20-30张合格品图像:

```bash
# 创建产品目录
mkdir -p data/samples/product_a/normal

# 将正常样本图像放入该目录
```

### 4.2 构建初始特征库

```bash
# 运行特征提取脚本
python scripts/build_feature_lib.py \
    --product product_a \
    --input data/samples/product_a/normal \
    --output data/feature_libs/product_a.bin
```

### 4.3 配置产品型号

在数据库中添加产品型号:

```python
from data_storage import DatabaseManager
from data_storage.dao import ProductModelDAO

db = DatabaseManager()
product_dao = ProductModelDAO(db)

product_dao.create(
    code="product_a",
    name="产品A",
    feature_lib_path="./data/feature_libs/product_a.bin",
    threshold=0.5
)
```

## 5. 与AOI设备对接

### 5.1 配置共享目录

**方式一: SMB/CIFS (Windows)**

```bash
# 挂载Windows共享目录
sudo mount -t cifs //server/aoi_share /mnt/aoi-share \
    -o username=user,password=pass,uid=1000,gid=1000
```

**方式二: NFS (Linux)**

```bash
# 挂载NFS目录
sudo mount -t nfs server:/aoi_share /mnt/aoi-share
```

### 5.2 配置监控路径

编辑 `config/config.yaml`:

```yaml
collector:
  watch:
    paths:
      - "/mnt/aoi-share/output"
    file_patterns:
      - "*.jpg"
      - "*.png"
```

### 5.3 AOI输出格式

AOI设备应输出CSV文件:

```csv
timestamp,board_id,component_id,image_path,aoi_result
2024-03-31 10:00:01,B001,C12,/mnt/aoi-share/images/img_001.jpg,FAIL
```

## 6. 性能优化

### 6.1 GPU加速

```yaml
inference:
  performance:
    use_gpu: true
    gpu_id: 0
```

### 6.2 TensorRT优化

```bash
# 导出ONNX模型
python scripts/export_onnx.py

# 转换为TensorRT引擎
trtexec --onnx=models/feature_extractor.onnx \
        --saveEngine=models/feature_extractor.engine \
        --fp16
```

### 6.3 批量推理

```yaml
inference:
  performance:
    batch_size: 16
    num_threads: 4
```

## 7. 监控与维护

### 7.1 日志查看

```bash
# 查看系统日志
tail -f logs/aoi_system.log

# 查看Docker日志
docker-compose logs -f web-backend
```

### 7.2 性能监控

访问 Prometheus metrics:

```bash
curl http://localhost:5000/metrics
```

### 7.3 数据备份

```bash
# 备份数据库
cp data/aoi_system.db data/backup/aoi_system_$(date +%Y%m%d).db

# 备份特征库
tar -czf feature_libs_$(date +%Y%m%d).tar.gz data/feature_libs/
```

### 7.4 清理旧数据

```bash
# 清理90天前的图像
python scripts/cleanup.py --days 90
```

## 8. 故障排查

### 8.1 服务无法启动

```bash
# 检查端口占用
netstat -tulpn | grep 5000

# 检查Docker状态
docker-compose ps

# 查看错误日志
docker-compose logs web-backend
```

### 8.2 GPU不可用

```bash
# 检查NVIDIA驱动
nvidia-smi

# 检查CUDA
nvcc --version

# 检查Docker GPU支持
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### 8.3 数据库错误

```bash
# 检查数据库文件
ls -lh data/aoi_system.db

# 重建数据库
rm data/aoi_system.db
python scripts/init_db.py
```

## 9. 安全建议

1. **修改默认密码**: 首次登录后立即修改admin密码
2. **启用HTTPS**: 配置SSL证书
3. **限制访问**: 使用防火墙限制访问IP
4. **定期备份**: 设置自动备份任务
5. **日志审计**: 定期检查系统日志

## 10. 升级更新

```bash
# 1. 备份数据
bash scripts/backup.sh

# 2. 拉取最新代码
git pull

# 3. 重新构建
docker-compose build

# 4. 重启服务
docker-compose down
docker-compose up -d
```
