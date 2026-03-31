# 工业AI质检系统API文档

## 1. API概述

### 1.1 基础信息

- 基础URL: `http://localhost:5000/api`
- 数据格式: JSON
- 认证方式: JWT Token

### 1.2 认证

除登录接口外,所有API请求需要在Header中携带JWT Token:

```
Authorization: Bearer <access_token>
```

### 1.3 响应格式

所有API响应格式统一:

```json
{
    "code": 200,
    "message": "success",
    "data": {...}
}
```

错误响应:

```json
{
    "code": 400,
    "message": "错误信息"
}
```

## 2. 认证接口

### 2.1 用户登录

**POST** `/api/auth/login`

**请求:**

```json
{
    "username": "admin",
    "password": "admin123"
}
```

**响应:**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "user": {
            "id": 1,
            "username": "admin",
            "role": "admin"
        }
    }
}
```

### 2.2 用户登出

**POST** `/api/auth/logout`

**Header:** 需要JWT Token

**响应:**

```json
{
    "code": 200,
    "message": "success"
}
```

### 2.3 获取用户信息

**GET** `/api/auth/profile`

**Header:** 需要JWT Token

**响应:**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "username": "admin",
        "role": "admin",
        "created_at": "2024-03-31 10:00:00"
    }
}
```

## 3. 标注接口

### 3.1 获取待标注样本

**GET** `/api/annotation/pending`

**参数:**
- `limit`: 返回数量 (默认100)
- `offset`: 偏移量 (默认0)

**响应:**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "samples": [
            {
                "id": 1,
                "image_path": "/data/images/20240331/img_001.jpg",
                "ai_score": 0.52,
                "ai_label": -1,
                "timestamp": "2024-03-31 10:00:00",
                "product_code": "product_a"
            }
        ],
        "total": 10
    }
}
```

### 3.2 提交标注结果

**POST** `/api/annotation/submit`

**请求:**

```json
{
    "sample_id": 1,
    "label": 0,
    "defect_type": "划痕",
    "notes": "表面有轻微划痕"
}
```

**字段说明:**
- `sample_id`: 样本ID (必填)
- `label`: 标注标签, 0=正常, 1=缺陷 (必填)
- `defect_type`: 缺陷类型 (可选)
- `notes`: 备注 (可选)

**响应:**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "annotation_id": 1
    }
}
```

### 3.3 获取标注历史

**GET** `/api/annotation/history`

**参数:**
- `limit`: 返回数量 (默认100)
- `product_model_id`: 产品型号ID (可选)

**响应:**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "annotations": [
            {
                "id": 1,
                "sample_id": 1,
                "label": 0,
                "operator": "admin",
                "annotated_at": "2024-03-31 10:30:00"
            }
        ]
    }
}
```

### 3.4 获取标注详情

**GET** `/api/annotation/<annotation_id>`

**响应:**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "sample_id": 1,
        "label": 0,
        "defect_type": null,
        "operator": "admin",
        "annotated_at": "2024-03-31 10:30:00",
        "notes": null
    }
}
```

## 4. 模型管理接口

### 4.1 获取产品型号列表

**GET** `/api/model/list`

**响应:**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "models": [
            {
                "id": 1,
                "code": "product_a",
                "name": "产品A",
                "threshold": 0.5,
                "is_active": 1
            }
        ]
    }
}
```

### 4.2 切换产品型号

**POST** `/api/model/switch`

**请求:**

```json
{
    "model_id": 1
}
```

**响应:**

```json
{
    "code": 200,
    "message": "success"
}
```

### 4.3 添加产品型号

**POST** `/api/model/add`

**请求:**

```json
{
    "code": "product_b",
    "name": "产品B",
    "description": "新产品型号",
    "threshold": 0.5
}
```

**响应:**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "model_id": 2
    }
}
```

### 4.4 获取当前活跃型号

**GET** `/api/model/active`

**响应:**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "code": "product_a",
        "name": "产品A",
        "is_active": 1
    }
}
```

## 5. 统计接口

### 5.1 获取统计概览

**GET** `/api/statistics/overview`

**响应:**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "total_samples": 1000,
        "total_annotations": 500,
        "normal_count": 400,
        "defect_count": 100,
        "uncertain_count": 50
    }
}
```

### 5.2 获取性能趋势

**GET** `/api/statistics/performance`

**参数:**
- `days`: 统计天数 (默认7)

**响应:**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "total": {
            "normal_count": 400,
            "defect_count": 100
        },
        "by_operator": [
            {
                "operator": "admin",
                "count": 300
            }
        ],
        "by_defect_type": [
            {
                "defect_type": "划痕",
                "count": 50
            }
        ]
    }
}
```

### 5.3 获取标注统计

**GET** `/api/statistics/labeling`

**参数:**
- `product_model_id`: 产品型号ID (可选)

**响应:**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "total": {
            "normal_count": 400,
            "defect_count": 100,
            "total_count": 500
        },
        "by_operator": [...],
        "by_defect_type": [...]
    }
}
```

## 6. 推理接口

### 6.1 执行推理

**POST** `/api/infer`

**请求:**

```json
{
    "image_path": "/data/images/20240331/img_001.jpg"
}
```

**响应:**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "score": 0.52,
        "label": -1,
        "confidence": 0.8,
        "is_uncertain": true,
        "elapsed_ms": 120.5
    }
}
```

### 6.2 批量推理

**POST** `/api/infer/batch`

**请求:**

```json
{
    "image_paths": [
        "/data/images/20240331/img_001.jpg",
        "/data/images/20240331/img_002.jpg"
    ]
}
```

**响应:**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "results": [
            {
                "score": 0.52,
                "label": -1,
                "is_uncertain": true
            },
            {
                "score": 0.3,
                "label": 0,
                "is_uncertain": false
            }
        ]
    }
}
```

## 7. 错误码说明

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权/认证失败 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 8. 调用示例

### Python示例

```python
import requests

# 登录
response = requests.post('http://localhost:5000/api/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
token = response.json()['data']['access_token']

# 设置Header
headers = {'Authorization': f'Bearer {token}'}

# 获取待标注样本
response = requests.get(
    'http://localhost:5000/api/annotation/pending',
    headers=headers
)
samples = response.json()['data']['samples']

# 提交标注
response = requests.post(
    'http://localhost:5000/api/annotation/submit',
    headers=headers,
    json={
        'sample_id': 1,
        'label': 0
    }
)
```

### JavaScript示例

```javascript
// 登录
const loginResponse = await fetch('http://localhost:5000/api/auth/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        username: 'admin',
        password: 'admin123'
    })
});
const {data: {access_token}} = await loginResponse.json();

// 获取待标注样本
const samplesResponse = await fetch('http://localhost:5000/api/annotation/pending', {
    headers: {'Authorization': `Bearer ${access_token}`}
});
const {data: {samples}} = await samplesResponse.json();

// 提交标注
await fetch('http://localhost:5000/api/annotation/submit', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${access_token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        sample_id: 1,
        label: 0
    })
});
```
