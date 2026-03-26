# API 辅助查询接口文档

本文档描述系统提供的辅助查询接口,主要用于按井号查询相关信息。

## 目录

1. [按井号查询完整信息](#1-按井号查询完整信息)
2. [按井号查询字段](#2-按井号查询字段)
3. [按井号查询文档](#3-按井号查询文档)
4. [查询井列表](#4-查询井列表)

---

## 1. 按井号查询完整信息

获取指定井号的完整信息,包括井信息、关联文档、提取字段、质量报告、处理日志等。

### 接口信息

- **路径**: `GET /api/v1/query/well/{well_no}`
- **描述**: 根据井号返回该井的所有相关信息
- **认证**: 可选

### 请求参数

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| well_no | String | 是 | 井号 | XX-1-1 |

### 响应示例

```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "well_info": {
      "well_no": "XX-1-1",
      "well_name": "XX油田1-1井",
      "oilfield": "XX油田",
      "block": "XX区块",
      "well_type": "开发井",
      "well_pattern": "水平井",
      "well_class": "生产井",
      "latitude": 38.123456,
      "longitude": 116.654321,
      "elevation": 150.5,
      "ground_elevation": 145.2,
      "drill_date": "2024-01-15",
      "completion_date": "2024-03-20",
      "status": "active",
      "created_at": "2024-01-10T08:00:00",
      "updated_at": "2024-03-25T10:30:00"
    },
    "documents": [
      {
        "id": 1,
        "document_id": "doc_001",
        "filename": "drilling_report.pdf",
        "file_path": "/storage/uploads/doc_001.pdf",
        "file_size": 2048576,
        "file_extension": "pdf",
        "mime_type": "application/pdf",
        "document_type": "钻井日报",
        "category": "drilling",
        "doc_category": "钻井日报",
        "upload_date": "2024-01-20",
        "uploaded_by": "admin",
        "status": "success",
        "created_at": "2024-01-20T09:00:00"
      }
    ],
    "extracted_fields": [
      {
        "id": 1,
        "document_id": 1,
        "well_no": "XX-1-1",
        "field_name": "RigModel",
        "field_value": "ZJ50DB",
        "field_type": "string",
        "confidence": 0.95,
        "is_valid": true,
        "validation_errors": null,
        "source": "ocr",
        "created_at": "2024-01-20T09:05:00"
      }
    ],
    "quality_reports": [
      {
        "id": 1,
        "document_id": 1,
        "well_no": "XX-1-1",
        "completeness": 0.92,
        "accuracy": 0.95,
        "consistency": 0.90,
        "confidence": 0.93,
        "overall_score": 0.92,
        "quality_level": "优秀",
        "issues": [],
        "suggestions": [],
        "validated_at": "2024-01-20T09:10:00"
      }
    ],
    "processing_logs": [
      {
        "id": 1,
        "document_id": 1,
        "well_no": "XX-1-1",
        "stage": "ocr",
        "status": "success",
        "duration_ms": 1500,
        "message": "OCR处理成功",
        "error_message": null,
        "log_metadata": {},
        "created_at": "2024-01-20T09:02:00"
      }
    ],
    "summary": {
      "total_documents": 5,
      "total_fields": 50,
      "valid_fields": 48,
      "avg_confidence": 0.93,
      "avg_quality_score": 0.91,
      "document_status_counts": {
        "pending": 0,
        "processing": 0,
        "success": 5,
        "failed": 0
      }
    }
  }
}
```

### 错误响应

```json
{
  "detail": "井号不存在: XX-1-1"
}
```

### cURL 示例

```bash
curl -X GET "http://localhost:8000/api/v1/query/well/XX-1-1" \
  -H "Content-Type: application/json"
```

### Python 示例

```python
import requests

well_no = "XX-1-1"
url = f"http://localhost:8000/api/v1/query/well/{well_no}"

response = requests.get(url)
result = response.json()

if result["success"]:
    well_info = result["data"]["well_info"]
    print(f"井名: {well_info['well_name']}")
    print(f"油田: {well_info['oilfield']}")
    print(f"文档数: {result['data']['summary']['total_documents']}")
    print(f"字段数: {result['data']['summary']['total_fields']}")
```

---

## 2. 按井号查询字段

获取指定井号的提取字段信息,支持字段筛选和有效性筛选。

### 接口信息

- **路径**: `GET /api/v1/query/well/{well_no}/fields`
- **描述**: 根据井号返回提取的字段数据
- **认证**: 可选

### 请求参数

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| well_no | String | 是 | 井号 | XX-1-1 |
| field_names | String | 否 | 字段名列表(逗号分隔) | WellNo,RigModel,TotalDepth |
| include_invalid | Boolean | 否 | 是否包含无效字段 | false |

### 响应示例

```json
{
  "success": true,
  "message": "查询到 3 个字段",
  "data": {
    "well_no": "XX-1-1",
    "total_fields": 3,
    "total_values": 5,
    "fields": [
      {
        "field_name": "WellNo",
        "values": [
          {
            "value": "XX-1-1",
            "document_id": 1,
            "confidence": 0.95,
            "is_valid": true,
            "source": "ocr",
            "created_at": "2024-01-20T09:05:00"
          },
          {
            "value": "XX-1-1",
            "document_id": 2,
            "confidence": 0.98,
            "is_valid": true,
            "source": "llm",
            "created_at": "2024-01-21T10:00:00"
          }
        ]
      },
      {
        "field_name": "RigModel",
        "values": [
          {
            "value": "ZJ50DB",
            "document_id": 1,
            "confidence": 0.92,
            "is_valid": true,
            "source": "ocr",
            "created_at": "2024-01-20T09:05:00"
          }
        ]
      },
      {
        "field_name": "TotalDepth",
        "values": [
          {
            "value": "3500.5",
            "document_id": 3,
            "confidence": 0.88,
            "is_valid": true,
            "source": "llm",
            "created_at": "2024-01-22T11:00:00"
          },
          {
            "value": "3500",
            "document_id": 4,
            "confidence": 0.75,
            "is_valid": true,
            "source": "ocr",
            "created_at": "2024-01-23T12:00:00"
          }
        ]
      }
    ]
  }
}
```

### cURL 示例

```bash
# 查询所有有效字段
curl -X GET "http://localhost:8000/api/v1/query/well/XX-1-1/fields"

# 查询特定字段
curl -X GET "http://localhost:8000/api/v1/query/well/XX-1-1/fields?field_names=WellNo,RigModel,TotalDepth"

# 包含无效字段
curl -X GET "http://localhost:8000/api/v1/query/well/XX-1-1/fields?include_invalid=true"
```

### Python 示例

```python
import requests

well_no = "XX-1-1"
field_names = "WellNo,RigModel,TotalDepth"

url = f"http://localhost:8000/api/v1/query/well/{well_no}/fields"
params = {"field_names": field_names, "include_invalid": False}

response = requests.get(url, params=params)
result = response.json()

if result["success"]:
    for field in result["data"]["fields"]:
        print(f"字段: {field['field_name']}")
        for value in field["values"]:
            print(f"  值: {value['value']}, 置信度: {value['confidence']}")
```

---

## 3. 按井号查询文档

获取指定井号的关联文档信息,支持分类和状态筛选。

### 接口信息

- **路径**: `GET /api/v1/query/well/{well_no}/documents`
- **描述**: 根据井号返回关联的文档
- **认证**: 可选

### 请求参数

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| well_no | String | 是 | 井号 | XX-1-1 |
| category | String | 否 | 一级分类筛选 | drilling |
| status | String | 否 | 状态筛选 | success |

### 响应示例

```json
{
  "success": true,
  "message": "查询到 3 份文档",
  "data": {
    "well_no": "XX-1-1",
    "documents": [
      {
        "id": 1,
        "document_id": "doc_001",
        "filename": "drilling_report.pdf",
        "file_path": "/storage/uploads/doc_001.pdf",
        "file_size": 2048576,
        "file_extension": "pdf",
        "document_type": "钻井日报",
        "category": "drilling",
        "doc_category": "钻井日报",
        "upload_date": "2024-01-20",
        "status": "success",
        "created_at": "2024-01-20T09:00:00"
      },
      {
        "id": 2,
        "document_id": "doc_002",
        "filename": "mudlogging_report.pdf",
        "file_path": "/storage/uploads/doc_002.pdf",
        "file_size": 1536000,
        "file_extension": "pdf",
        "document_type": "录井日报",
        "category": "mudlogging",
        "doc_category": "录井日报",
        "upload_date": "2024-01-21",
        "status": "success",
        "created_at": "2024-01-21T10:00:00"
      }
    ],
    "summary": {
      "total_documents": 3,
      "by_category": {
        "drilling": 1,
        "mudlogging": 1,
        "wireline": 1
      },
      "by_status": {
        "pending": 0,
        "processing": 0,
        "success": 3,
        "failed": 0
      },
      "total_fields": 45
    }
  }
}
```

### cURL 示例

```bash
# 查询所有文档
curl -X GET "http://localhost:8000/api/v1/query/well/XX-1-1/documents"

# 按分类筛选
curl -X GET "http://localhost:8000/api/v1/query/well/XX-1-1/documents?category=drilling"

# 按状态筛选
curl -X GET "http://localhost:8000/api/v1/query/well/XX-1-1/documents?status=success"
```

### Python 示例

```python
import requests

well_no = "XX-1-1"
category = "drilling"

url = f"http://localhost:8000/api/v1/query/well/{well_no}/documents"
params = {"category": category}

response = requests.get(url, params=params)
result = response.json()

if result["success"]:
    documents = result["data"]["documents"]
    summary = result["data"]["summary"]
    
    print(f"总文档数: {summary['total_documents']}")
    print(f"总字段数: {summary['total_fields']}")
    print(f"分类统计: {summary['by_category']}")
    
    for doc in documents:
        print(f"  - {doc['filename']} ({doc['category']})")
```

---

## 4. 查询井列表

查询井列表,支持按油田、区块、井别等条件筛选和分页。

### 接口信息

- **路径**: `GET /api/v1/query/wells`
- **描述**: 查询井列表,支持筛选和分页
- **认证**: 可选

### 请求参数

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| oilfield | String | 否 | 油田筛选 | XX油田 |
| block | String | 否 | 区块筛选 | XX区块 |
| well_type | String | 否 | 井别筛选 | 开发井 |
| status | String | 否 | 状态筛选,默认active | active |
| limit | Integer | 否 | 返回数量限制,默认100 | 10 |
| skip | Integer | 否 | 跳过数量,默认0 | 0 |

### 响应示例

```json
{
  "success": true,
  "message": "查询到 10 口井",
  "data": {
    "total": 25,
    "limit": 10,
    "skip": 0,
    "wells": [
      {
        "well_no": "XX-1-1",
        "well_name": "XX油田1-1井",
        "oilfield": "XX油田",
        "block": "XX区块",
        "well_type": "开发井",
        "well_pattern": "水平井",
        "well_class": "生产井",
        "drill_date": "2024-01-15",
        "completion_date": "2024-03-20",
        "status": "active",
        "document_count": 5,
        "created_at": "2024-01-10T08:00:00"
      },
      {
        "well_no": "XX-1-2",
        "well_name": "XX油田1-2井",
        "oilfield": "XX油田",
        "block": "XX区块",
        "well_type": "开发井",
        "well_pattern": "定向井",
        "well_class": "生产井",
        "drill_date": "2024-02-10",
        "completion_date": "2024-04-15",
        "status": "active",
        "document_count": 3,
        "created_at": "2024-02-05T09:00:00"
      }
    ]
  }
}
```

### cURL 示例

```bash
# 查询所有活跃井
curl -X GET "http://localhost:8000/api/v1/query/wells"

# 按油田筛选
curl -X GET "http://localhost:8000/api/v1/query/wells?oilfield=XX油田"

# 分页查询
curl -X GET "http://localhost:8000/api/v1/query/wells?limit=10&skip=0"

# 组合筛选
curl -X GET "http://localhost:8000/api/v1/query/wells?oilfield=XX油田&block=XX区块&well_type=开发井&limit=5"
```

### Python 示例

```python
import requests

url = "http://localhost:8000/api/v1/query/wells"
params = {
    "oilfield": "XX油田",
    "block": "XX区块",
    "well_type": "开发井",
    "status": "active",
    "limit": 10,
    "skip": 0
}

response = requests.get(url, params=params)
result = response.json()

if result["success"]:
    data = result["data"]
    print(f"总井数: {data['total']}")
    print(f"当前页: {data['skip'] // data['limit'] + 1}")
    
    for well in data["wells"]:
        print(f"  - {well['well_no']}: {well['well_name']}")
        print(f"    文档数: {well['document_count']}")
```

---

## 错误码说明

| 状态码 | 说明 | 示例 |
|--------|------|------|
| 200 | 成功 | - |
| 404 | 资源不存在 | 井号不存在、文档不存在 |
| 500 | 服务器错误 | 数据库连接失败、查询失败 |

---

## 使用场景

### 场景1: 查看某口井的完整信息

用于查看一口井的所有关联信息,包括井信息、文档、提取字段等。

```python
# 查询井号 XX-1-1 的完整信息
well_no = "XX-1-1"
url = f"http://localhost:8000/api/v1/query/well/{well_no}"
response = requests.get(url)
```

### 场景2: 查看某口井的特定字段

用于查看一口井的特定字段值,如只查看井号、钻机型号等。

```python
# 查询井号 XX-1-1 的 WellNo 和 RigModel 字段
well_no = "XX-1-1"
field_names = "WellNo,RigModel"
url = f"http://localhost:8000/api/v1/query/well/{well_no}/fields"
params = {"field_names": field_names}
response = requests.get(url, params=params)
```

### 场景3: 查看某口井的所有钻井文档

用于查看一口井的所有钻井相关文档。

```python
# 查询井号 XX-1-1 的所有 drilling 分类文档
well_no = "XX-1-1"
category = "drilling"
url = f"http://localhost:8000/api/v1/query/well/{well_no}/documents"
params = {"category": category}
response = requests.get(url, params=params)
```

### 场景4: 列出某油田的所有井

用于列出某油田的所有井,便于管理和浏览。

```python
# 查询 XX油田的所有活跃井
oilfield = "XX油田"
status = "active"
url = "http://localhost:8000/api/v1/query/wells"
params = {"oilfield": oilfield, "status": status}
response = requests.get(url, params=params)
```

---

## 注意事项

1. **井号大小写**: 井号区分大小写,请确保传入正确的井号
2. **权限要求**: 部分接口可能需要认证,请确保已登录
3. **分页限制**: 查询井列表时,limit 最大值为 100
4. **数据时效性**: 数据为实时查询,反映数据库最新状态
5. **性能优化**: 大量查询时建议使用分页,避免一次性获取过多数据

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-03-25 | 初始版本,包含4个查询接口 |
