# 工业AI质检系统（AOI辅助系统）

基于主动学习和异常检测的车灯制造产线AOI辅助系统

## 项目结构

```
aoi_quality_inspection/
├── image_collector/          # 图像采集模块
├── inference_engine/         # 推理引擎模块
├── active_learning/          # 主动学习模块
├── model_updater/            # 模型更新模块
├── web_terminal/             # Web终端模块
│   ├── backend/              # Flask后端
│   └── frontend/             # Vue前端
├── data_storage/             # 数据存储模块
├── common/                   # 公共工具
├── tests/                    # 测试代码
├── docs/                     # 文档
├── scripts/                  # 脚本工具
├── config/                   # 配置文件
├── requirements.txt          # Python依赖
└── CMakeLists.txt            # C++构建配置
```

## 快速开始

### 1. 安装Python依赖

```bash
cd aoi_quality_inspection
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. 配置系统

编辑 `config/config.yaml` 文件，配置数据库路径、模型路径等参数。

### 3. 初始化数据库

```bash
python scripts/init_db.py
```

### 4. 启动服务

```bash
# 启动推理引擎
python inference_engine/server.py

# 启动Web后端
python web_terminal/backend/app.py

# 启动Web前端
cd web_terminal/frontend
npm install
npm run dev
```

## 核心功能

- **异常检测**: 基于PatchCore的无缺陷样本异常检测
- **主动学习**: 自动筛选不确定样本供人工标注
- **模型更新**: 利用标注数据持续优化模型
- **多产品支持**: 支持多产品型号动态切换
- **Web标注终端**: 提供友好的标注界面

## 技术栈

- **后端**: Python 3.8+, Flask, PyTorch, FAISS
- **推理引擎**: C++17, TensorRT, CUDA
- **前端**: Vue 3, Element Plus, ECharts
- **数据库**: SQLite
- **通信**: gRPC, REST API

## 文档

- [用户手册](docs/user_manual.md)
- [部署指南](docs/deployment_guide.md)
- [API文档](docs/api_documentation.md)
- [开发指南](docs/developer_guide.md)

## 许可证

MIT License
