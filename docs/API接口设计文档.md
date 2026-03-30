# API 接口设计文档

> **文档版本**: v1.2
> **更新日期**: 2026-03-26
> **项目路径**: d:/Workspaces/well-info-extraction/

---

## 变更说明

**v1.2** (2026-03-26):
- **API_PREFIX 改为包含项目名称**: 从 `/api/v1` 改为 `/wellie/api/v1`
- **原因**: 避免多个项目部署在同一域名时的接口冲突
- **影响**: 所有接口路径都增加了 `/wellie` 项目前缀
- **示例**: `/wellie/api/v1/process/upload`, `/wellie/api/v1/query/well/{well_no}` 等

**v1.1** (2026-03-26):
- 更新接口路径,使用实际实现的路径
- 修正单文档接口,改为 `POST /api/v1/process/upload` 支持文件上传
- 更新批量接口路径为 `/api/v1/process/batch` (本地文件) 和 `/api/v1/process/batch/group` (上传文件并按井分组)
- 新增验证接口: `POST /api/v1/validate` (验证数据) 和 `POST /api/v1/validate/summary` (获取验证摘要)
- 新增质量检查接口: `POST /api/v1/quality/check` (检查数据质量)
- 新增查询接口:
  - `GET /api/v1/query/well/{well_no}` - 查询井完整信息
  - `GET /api/v1/query/well/{well_no}/fields` - 查询井字段
  - `GET /api/v1/query/well/{well_no}/documents` - 查询井文档
  - `GET /api/v1/query/wells` - 查询井列表
- 移除场景3 (单井批量资料处理),因为实际代码中未实现
- 删除实现代码示例章节,保持文档聚焦于接口定义
- 更新所有接口定义以匹配实际代码实现 (api/routes.py)
- 调整章节编号,从十五章调整到十五章完整

**v1.0** (2026-03-25):
- 初始版本

---

## 一、接口设计原则

### 1.1 设计理念

基于三大核心业务场景,设计统一的API接口规范:
- **场景1**: 单口井批量资料一键入库
- **场景2**: 多口井混合资料批量处理
- **场景3**: 历史资料治理与补录

### 1.2 统一性要求

**请求参数相似性**:
- 支持文件路径和文件上传两种方式
- 支持目标字段过滤
- 支持分类提示(category/doc_category)
- 支持处理选项(图像增强、文本清洗等)

**返回参数相似性**:
- 统一的字段命名规范(驼峰命名法)
- 统一的数据类型定义
- 统一的响应结构(success, message, data)
- 统一的字段级别元数据(value, confidence, source)

---

## 二、基础数据模型

### 2.1 字段提取结果模型

```json
{
  "field_name": {
    "value": "提取的值",
    "confidence": 0.95,
    "source": "来源描述",
    "unit": "单位(如有)",
    "validated": true
  }
}
```

**字段说明**:
- `field_name`: 字段名(英文),对应字段库中的标准字段名
- `value`: 提取的值,可以是字符串、数字、日期、null等
- `confidence`: 置信度(0-1),表示AI对该字段提取结果的信心
- `source`: 值来源描述,如"文档第3页表格"、"文档标题"等
- `unit`: 单位(如适用),如"米"、"天"、"吨/日"等
- `validated`: 是否通过规则校验

### 2.2 基础响应模型

```json
{
  "success": true,
  "message": "处理成功",
  "timestamp": "2026-03-25T10:30:00Z",
  "request_id": "req_20260325_103000_001"
}
```

**字段说明**:
- `success`: 请求是否成功
- `message`: 响应消息描述
- `timestamp`: 响应时间戳(ISO 8601格式)
- `request_id`: 请求唯一标识符

---

## 三、处理接口

### 3.1 文件上传并处理

**接口路径**: `POST /wellie/api/v1/process/upload`

**功能**: 上传单个文档,自动保存并处理,返回结构化抽取结果

### 3.2 请求参数

```http
POST /wellie/api/v1/process/upload
Content-Type: multipart/form-data

file: [文件]  // 必需
target_fields: ["WellNo", "DocCategory", "Oilfield", "WellType", "SpudDate", "TotalDepth"]  // 可选
enhance_images: true  // 可选,默认true
clean_text: true  // 可选,默认true
```

**参数说明**:
- `file`: 上传的文件(支持PDF、Word、Excel、TXT、图片)
  - 支持扩展名: `.pdf`, `.docx`, `.doc`, `.xlsx`, `.xls`, `.txt`, `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`
  - 文件大小限制: 100MB
- `target_fields`: 目标字段列表,不传则提取所有字段
- `enhance_images`: 是否对图像进行增强处理
- `clean_text`: 是否对文本进行清洗

**参数说明**:
- `file`: 上传的文件(支持PDF、Word、Excel、PPT、TXT、图片)
- `file_path`: 服务器本地文件路径
- `target_fields`: 目标字段列表,不传则提取所有字段
- `category`: 一级分类(drilling/mudlogging/wireline/testing/completion/geology/production)
- `doc_category`: 二级文档分类(如:钻井设计、完井设计、钻井日报等)
- `enhance_images`: 是否对图像进行增强处理
- `clean_text`: 是否对文本进行清洗

### 3.3 响应参数

```json
{
  "success": true,
  "message": "文件处理成功",
  "data": {
    "document_info": {
      "document_id": "doc_20260326_001",
      "filename": "drilling_report.pdf",
      "file_size": 2048576,
      "file_extension": ".pdf",
      "mime_type": "application/pdf",
      "document_type": "pdf",
      "category": "drilling",
      "doc_category": "钻井日报"
    },
    "well_info": {
      "well_no": "TS1-1",
      "well_no_confidence": 0.98,
      "is_multi_well": false
    },
    "extracted_fields": {
      "WellNo": {
        "value": "TS1-1",
        "confidence": 0.98,
        "source": "文档标题",
        "unit": null,
        "validated": true
      },
      "SpudDate": {
        "value": "2025-01-15",
        "confidence": 0.95,
        "source": "文档第2页",
        "unit": null,
        "validated": true
      }
    },
    "validation_results": {
      "total_fields": 21,
      "valid_fields": 19,
      "invalid_fields": 2,
      "warnings": [],
      "errors": []
    },
    "quality_metrics": {
      "completeness": 0.90,
      "accuracy": 0.93,
      "confidence": 0.92,
      "overall_score": 0.92
    },
    "processing_info": {
      "processing_time_ms": 12500,
      "stages": {
        "preprocessing": 2000,
        "classification": 500,
        "well_extraction": 300,
        "field_extraction": 8000,
        "validation": 1000,
        "postprocessing": 700
      }
    }
  }
}
```

```json
{
  "success": true,
  "message": "文档处理成功",
  "timestamp": "2026-03-25T10:30:00Z",
  "request_id": "req_20260325_103000_001",

  "document_info": {
    "document_id": "doc_20260325_001",
    "filename": "drilling_report.pdf",
    "file_size": 2048576,
    "document_type": "application/pdf",
    "category": "drilling",
    "category_name": "钻井资料",
    "doc_category": "钻井日报",
    "classification_confidence": 0.95
  },

  "well_info": {
    "well_no": "TS1-1",
    "well_no_confidence": 0.98,
    "is_multi_well": false
  },

  "extracted_fields": {
    "WellNo": {
      "value": "TS1-1",
      "confidence": 0.98,
      "source": "文档标题",
      "unit": null,
      "validated": true
    },
    "SpudDate": {
      "value": "2025-01-15",
      "confidence": 0.95,
      "source": "文档第2页",
      "unit": null,
      "validated": true
    },
    "TotalDepth": {
      "value": 5230.5,
      "confidence": 0.92,
      "source": "文档第3页表格",
      "unit": "米",
      "validated": true
    },
    "RigModel": {
      "value": "ZJ50DB",
      "confidence": 0.85,
      "source": "文档第1页",
      "unit": null,
      "validated": true
    }
  },

  "validation_results": {
    "total_fields": 21,
    "valid_fields": 19,
    "invalid_fields": 2,
    "warnings": [
      {
        "field": "CreateDate",
        "level": "warning",
        "message": "日期格式可能存在歧义,建议人工确认"
      }
    ],
    "errors": []
  },

  "quality_metrics": {
    "completeness": 0.90,
    "accuracy": 0.93,
    "confidence": 0.92,
    "overall_score": 0.92
  },

  "processing_info": {
    "processing_time_ms": 12500,
    "stages": {
      "preprocessing": 2000,
      "classification": 500,
      "well_extraction": 300,
      "field_extraction": 8000,
      "validation": 1000,
      "postprocessing": 700
    }
  }
}
```

**响应字段说明**:

#### document_info(文档信息)
- `document_id`: 文档唯一标识
- `filename`: 文件名
- `file_size`: 文件大小(字节)
- `document_type`: 文档MIME类型
- `category`: 一级分类代码
- `category_name`: 一级分类名称
- `doc_category`: 二级文档分类
- `classification_confidence`: 分类置信度

#### well_info(井信息)
- `well_no`: 井号
- `well_no_confidence`: 井号识别置信度
- `is_multi_well`: 是否包含多口井

#### extracted_fields(提取字段)
- 每个字段的提取结果,遵循字段提取结果模型

#### validation_results(校验结果)
- `total_fields`: 总字段数
- `valid_fields`: 有效字段数
- `invalid_fields`: 无效字段数
- `warnings`: 警告列表
- `errors`: 错误列表

#### quality_metrics(质量指标)
- `completeness`: 完整性(0-1)
- `accuracy`: 准确性(0-1)
- `confidence`: 置信度(0-1)
- `overall_score`: 总体评分(0-1)

#### processing_info(处理信息)
- `processing_time_ms`: 总处理时间(毫秒)
- `stages`: 各阶段耗时

---

## 四、批量处理接口

### 4.1 批量处理文件(本地路径)

**接口路径**: `POST /wellie/api/v1/process/batch`

**功能**: 批量处理本地文件路径列表,返回处理结果

### 4.2 请求参数

```json
{
  "file_paths": [
    "/path/to/doc1.pdf",
    "/path/to/doc2.pdf"
  ],
  "target_fields": ["WellNo", "SpudDate"]
}
```

**参数说明**:
- `file_paths`: 本地文件路径列表(必需)
- `target_fields`: 目标字段列表(可选)

**参数说明**:
- `files`: 上传的文件列表
- `file_paths`: 服务器本地文件路径列表
- `target_fields`: 目标字段列表
- `category`: 一级分类
- `doc_category`: 二级文档分类
- `group_by_well`: 是否按井号分组(默认true)
- `enhance_images`: 是否增强图像
- `clean_text`: 是否清洗文本

### 4.3 响应参数

```json
{
  "success": true,
  "message": "批量处理完成: 10 个文件",
  "data": [
    {
      "document_info": {
        "document_id": "doc_20260326_001",
        "filename": "drilling_report.pdf",
        "file_size": 2048576
      },
      "well_info": {
        "well_no": "TS1-1",
        "well_no_confidence": 0.98
      },
      "extracted_fields": {
        "WellNo": {
          "value": "TS1-1",
          "confidence": 0.98,
          "source": "文档标题"
        }
      },
      "quality_metrics": {
        "completeness": 0.90,
        "accuracy": 0.93,
        "overall_score": 0.92
      }
    }
  ],
  "summary": {
    "total_files": 10,
    "successful": 8,
    "failed": 2,
    "avg_confidence": 0.91,
    "avg_quality_score": 0.90
  }
}
```

**响应字段说明**:

#### batch_info(批次信息)
- `total_documents`: 总文档数
- `successful_documents`: 成功处理文档数
- `partial_documents`: 部分成功文档数
- `failed_documents`: 失败文档数
- `total_wells`: 识别到的井数
- `unrecognized_wells`: 未识别到井的文档数
- `processing_time_ms`: 总处理时间

#### document_results(文档结果列表)
- 每个文档的处理结果,结构与单文档响应类似(不包含顶层success/message等)

#### well_groups(井分组)
- 按井号组织的文档结果
- `well_info`: 井的汇总信息
- `documents`: 该井的所有文档

#### summary(汇总统计)
- `by_category`: 按分类统计
- `by_well`: 按井统计
- `overall`: 总体统计

---

## 五、批量处理并按井分组

### 5.1 接口定义

**接口路径**: `POST /wellie/api/v1/process/batch/group`

**功能**: 批量上传文件,自动识别井号并按井号分组返回结果

### 5.2 请求参数

```http
POST /wellie/api/v1/process/batch/group
Content-Type: multipart/form-data

files: [文件1, 文件2, ...]  // 必需
```

**功能说明**:
1. 批量上传文件
2. 识别每份文件的井号
3. 按井号分组
4. 返回按井号组织的文档结构

### 5.3 响应参数

```json
{
  "success": true,
  "message": "处理完成: 3 口井, 10 份文档",
  "total_files": 10,
  "unique_wells": 3,
  "unrecognized_files": 1,
  "well_groups": {
    "TS1-1": [
      {
        "document_id": "doc_20260326_001",
        "original_filename": "drilling_report.pdf",
        "well_no": "TS1-1",
        "extracted_fields": {
          "WellNo": {
            "value": "TS1-1",
            "confidence": 0.98
          }
        }
      },
      {
        "document_id": "doc_20260326_002",
        "original_filename": "well_design.pdf",
        "well_no": "TS1-1",
        "extracted_fields": {
          "WellNo": {
            "value": "TS1-1",
            "confidence": 0.95
          }
        }
      }
    ],
    "HZ21-3": [
      {
        "document_id": "doc_20260326_003",
        "original_filename": "hz21_report.pdf",
        "well_no": "HZ21-3",
        "extracted_fields": {
          "WellNo": {
            "value": "HZ21-3",
            "confidence": 0.92
          }
        }
      }
    ],
    "未识别": [
      {
        "document_id": "doc_20260326_010",
        "original_filename": "unknown.pdf",
        "well_no": null,
        "extracted_fields": {}
      }
    ]
  }
}
```

**响应字段说明**:
- `total_files`: 总文件数
- `unique_wells`: 识别到的井数(不包括未识别)
- `unrecognized_files`: 未识别井号的文件数
- `well_groups`: 按井号分组的文档列表
  - 键名: 井号或"未识别"
  - 值: 该井的所有文档处理结果

---

## 六、验证接口

### 6.1 验证数据

**接口路径**: `POST /wellie/api/v1/validate`

**功能**: 验证提取的字段数据,返回每个字段的验证结果

### 6.2 请求参数

```json
{
  "data": {
    "WellNo": "TS1-1",
    "TotalDepth": 5230.5,
    "SpudDate": "2025-01-15"
  },
  "document_type": "drilling"
}
```

**参数说明**:
- `data`: 要验证的字段数据
- `document_type`: 文档类型,决定使用的验证规则

### 6.3 响应参数

```json
[
  {
    "field_name": "WellNo",
    "is_valid": true,
    "errors": [],
    "warnings": [],
    "confidence": 0.98
  },
  {
    "field_name": "TotalDepth",
    "is_valid": true,
    "errors": [],
    "warnings": ["深度值较大,建议确认"],
    "confidence": 0.95
  },
  {
    "field_name": "SpudDate",
    "is_valid": false,
    "errors": ["日期格式错误"],
    "warnings": [],
    "confidence": 0.5
  }
]
```

### 6.4 获取验证摘要

**接口路径**: `POST /wellie/api/v1/validate/summary`

**功能**: 获取批量验证的摘要统计信息

### 6.5 请求参数

与验证接口相同,使用相同的请求参数

### 6.6 响应参数

```json
{
  "total_fields": 167,
  "valid_fields": 155,
  "invalid_fields": 8,
  "total_errors": 12,
  "total_warnings": 25,
  "validation_rate": 0.93,
  "avg_confidence": 0.91,
  "problem_fields": [
    {
      "field_name": "OilRate",
      "error_count": 5,
      "warning_count": 8
    }
  ]
}
```

---

## 七、质量检查接口

### 7.1 检查数据质量

**接口路径**: `POST /wellie/api/v1/quality/check`

**功能**: 检查文档提取数据的综合质量指标

### 7.2 请求参数

```json
{
  "document_id": "doc_20260326_001",
  "extracted_data": {
    "WellNo": "TS1-1",
    "TotalDepth": 5230.5
  },
  "target_fields": ["WellNo", "TotalDepth", "SpudDate"],
  "metadata": {
    "category": "drilling",
    "document_type": "drilling_report"
  }
}
```

### 7.3 响应参数

```json
{
  "document_id": "doc_20260326_001",
  "metrics": {
    "completeness": 0.90,
    "accuracy": 0.93,
    "consistency": 0.95,
    "confidence": 0.92,
    "overall_score": 0.92
  },
  "issues": [
    {
      "field": "SpudDate",
      "type": "missing",
      "severity": "warning",
      "message": "字段缺失"
    }
  ],
  "suggestions": [
    "建议补充缺失的字段以提高完整性",
    "建议人工复核低置信度字段"
  ],
  "validated_at": "2026-03-26T10:30:00Z"
}
```

---

## 八、查询接口

### 8.1 按井号查询完整信息

**接口路径**: `GET /wellie/api/v1/query/well/{well_no}`

**功能**: 查询指定井号的完整信息,包括井信息、文档、提取字段、质量报告等

### 8.2 请求参数

```
GET /wellie/api/v1/query/well/TS1-1
```

**路径参数**:
- `well_no`: 井号,如 "TS1-1"

### 8.3 响应参数

```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "well_info": {
      "well_no": "TS1-1",
      "well_name": "台南1-1井",
      "oilfield": "台南油田",
      "block": "台南区块",
      "well_type": "生产井",
      "well_pattern": "直井",
      "well_class": "一类井",
      "latitude": 39.123,
      "longitude": 117.456,
      "elevation": 50.0,
      "ground_elevation": 45.0,
      "drill_date": "2025-01-15",
      "completion_date": "2025-03-20",
      "status": "active",
      "created_at": "2026-03-20T10:00:00Z",
      "updated_at": "2026-03-26T10:00:00Z"
    },
    "documents": [
      {
        "id": 1,
        "document_id": "doc_20260326_001",
        "filename": "drilling_report.pdf",
        "file_path": "/storage/uploads/drilling_report.pdf",
        "file_size": 2048576,
        "file_extension": ".pdf",
        "mime_type": "application/pdf",
        "document_type": "pdf",
        "category": "drilling",
        "doc_category": "钻井日报",
        "upload_date": "2026-03-26T10:00:00Z",
        "uploaded_by": "admin",
        "status": "success",
        "created_at": "2026-03-26T10:00:00Z"
      }
    ],
    "extracted_fields": [
      {
        "id": 1,
        "document_id": "doc_20260326_001",
        "well_no": "TS1-1",
        "field_name": "WellNo",
        "field_value": "TS1-1",
        "field_type": "string",
        "confidence": 0.98,
        "is_valid": true,
        "validation_errors": [],
        "source": "文档标题",
        "created_at": "2026-03-26T10:05:00Z"
      }
    ],
    "quality_reports": [
      {
        "id": 1,
        "document_id": "doc_20260326_001",
        "well_no": "TS1-1",
        "completeness": 0.90,
        "accuracy": 0.93,
        "consistency": 0.95,
        "confidence": 0.92,
        "overall_score": 0.92,
        "quality_level": "good",
        "issues": [],
        "suggestions": [],
        "validated_at": "2026-03-26T10:10:00Z"
      }
    ],
    "processing_logs": [
      {
        "id": 1,
        "document_id": "doc_20260326_001",
        "well_no": "TS1-1",
        "stage": "preprocessing",
        "status": "completed",
        "duration_ms": 2000,
        "message": "预处理完成",
        "error_message": null,
        "log_metadata": {},
        "created_at": "2026-03-26T10:02:00Z"
      }
    ],
    "summary": {
      "total_documents": 10,
      "total_fields": 167,
      "valid_fields": 155,
      "avg_confidence": 0.91,
      "avg_quality_score": 0.92,
      "document_status_counts": {
        "pending": 0,
        "processing": 0,
        "success": 10,
        "failed": 0
      }
    }
  }
}
```

### 8.4 按井号查询字段

**接口路径**: `GET /wellie/api/v1/query/well/{well_no}/fields`

**功能**: 查询指定井号提取的字段数据,支持字段筛选

### 8.5 请求参数

```
GET /wellie/api/v1/query/well/TS1-1/fields?field_names=WellNo,RigModel,TotalDepth&include_invalid=false
```

**路径参数**:
- `well_no`: 井号

**查询参数**:
- `field_names`: 可选,字段名称列表(逗号分隔)
- `include_invalid`: 可选,是否包含无效字段,默认false

### 8.6 响应参数

```json
{
  "success": true,
  "message": "查询到 3 个字段",
  "data": {
    "well_no": "TS1-1",
    "total_fields": 3,
    "total_values": 5,
    "fields": [
      {
        "field_name": "WellNo",
        "values": [
          {
            "value": "TS1-1",
            "document_id": "doc_20260326_001",
            "confidence": 0.98,
            "is_valid": true,
            "source": "文档标题",
            "created_at": "2026-03-26T10:05:00Z"
          }
        ]
      },
      {
        "field_name": "RigModel",
        "values": [
          {
            "value": "ZJ50DB",
            "document_id": "doc_20260326_001",
            "confidence": 0.85,
            "is_valid": true,
            "source": "文档第1页",
            "created_at": "2026-03-26T10:05:00Z"
          }
        ]
      },
      {
        "field_name": "TotalDepth",
        "values": [
          {
            "value": 5230.5,
            "document_id": "doc_20260326_001",
            "confidence": 0.92,
            "is_valid": true,
            "source": "文档第3页表格",
            "created_at": "2026-03-26T10:05:00Z"
          }
        ]
      }
    ]
  }
}
```

### 8.7 按井号查询文档

**接口路径**: `GET /wellie/api/v1/query/well/{well_no}/documents`

**功能**: 查询指定井号关联的所有文档,支持分类和状态筛选

### 8.8 请求参数

```
GET /wellie/api/v1/query/well/TS1-1/documents?category=drilling&status=success
```

**路径参数**:
- `well_no`: 井号

**查询参数**:
- `category`: 可选,一级分类筛选
- `status`: 可选,状态筛选

### 8.9 响应参数

```json
{
  "success": true,
  "message": "查询到 5 份文档",
  "data": {
    "well_no": "TS1-1",
    "documents": [
      {
        "id": 1,
        "document_id": "doc_20260326_001",
        "filename": "drilling_report.pdf",
        "file_path": "/storage/uploads/drilling_report.pdf",
        "file_size": 2048576,
        "file_extension": ".pdf",
        "document_type": "pdf",
        "category": "drilling",
        "doc_category": "钻井日报",
        "upload_date": "2026-03-26T10:00:00Z",
        "status": "success",
        "created_at": "2026-03-26T10:00:00Z"
      }
    ],
    "summary": {
      "total_documents": 5,
      "by_category": {
        "drilling": 3,
        "mudlogging": 1,
        "wireline": 1
      },
      "by_status": {
        "success": 5
      },
      "total_fields": 50
    }
  }
}
```

### 8.10 查询井列表

**接口路径**: `GET /wellie/api/v1/query/wells`

**功能**: 查询井列表,支持多条件筛选和分页

### 8.11 请求参数

```
GET /wellie/api/v1/query/wells?oilfield=台南油田&block=台南区块&well_type=生产井&status=active&limit=10&skip=0
```

**查询参数**:
- `oilfield`: 可选,油田筛选
- `block`: 可选,区块筛选
- `well_type`: 可选,井别筛选
- `status`: 可选,状态筛选,默认active
- `limit`: 可选,返回数量限制,默认100
- `skip`: 可选,跳过数量,默认0

### 8.12 响应参数

```json
{
  "success": true,
  "message": "查询到 10 口井",
  "data": {
    "total": 10,
    "limit": 10,
    "skip": 0,
    "wells": [
      {
        "well_no": "TS1-1",
        "well_name": "台南1-1井",
        "oilfield": "台南油田",
        "block": "台南区块",
        "well_type": "生产井",
        "well_pattern": "直井",
        "well_class": "一类井",
        "drill_date": "2025-01-15",
        "completion_date": "2025-03-20",
        "status": "active",
        "document_count": 10,
        "created_at": "2026-03-20T10:00:00Z"
      }
    ]
  }
}
```

---

## 十、辅助接口

### 10.1 健康检查

**接口路径**: `GET /wellie/health` (待实现)

**功能**: 检查服务健康状态

**响应**:
```json
{
  "status": "ok",
  "service": "wellinfo-extractor",
  "version": "1.0.0",
  "timestamp": "2026-03-26T10:00:00Z"
}
```

---

## 十一、错误处理

### 7.1 错误响应格式

```json
{
  "success": false,
  "message": "错误描述",
  "error_code": "INVALID_FILE_TYPE",
  "timestamp": "2026-03-25T10:30:00Z",
  "request_id": "req_20260325_103000_001",
  "details": {
    "field": "file",
    "expected": "PDF, Word, Excel",
    "received": "exe"
  }
}
```

### 7.2 错误码定义

| 错误码 | HTTP状态码 | 描述 |
|--------|-----------|------|
| INVALID_FILE_TYPE | 400 | 不支持的文件类型 |
| FILE_TOO_LARGE | 400 | 文件过大 |
| MISSING_REQUIRED_FIELD | 400 | 缺少必填参数 |
| INVALID_PARAMETER_VALUE | 400 | 参数值无效 |
| FILE_NOT_FOUND | 404 | 文件不存在 |
| DOCUMENT_PROCESSING_FAILED | 500 | 文档处理失败 |
| CLASSIFICATION_FAILED | 500 | 文档分类失败 |
| EXTRACTION_FAILED | 500 | 字段提取失败 |
| SERVICE_UNAVAILABLE | 503 | 服务不可用 |
| RATE_LIMIT_EXCEEDED | 429 | 请求频率超限 |

---

## 十二、接口版本管理

- 主版本号(v1)在`/api/v{version}`路径中体现
- 兼容性变更: 增加新字段、新接口
- 不兼容变更: 升级主版本号(v2)
- 废弃接口: 保留3个版本后删除

### 8.2 版本演进

- **v1.0**: 初始版本
- **v1.1**: 增加按井分组功能
- **v2.0**: 重大架构升级(待定)

---

## 十三、性能指标

### 9.1 响应时间

| 接口 | 目标响应时间 | 说明 |
|------|------------|------|
| 单文档提取 | <30秒 | 包含OCR+分类+抽取+校验 |
| 批量提取(10文档) | <3分钟 | 平均18秒/文档 |
| 单井批量(10文档) | <4分钟 | 含字段合并 |

### 9.2 并发能力

- 支持至少20个并发请求
- 批量接口支持最大100个文档

### 9.3 可用性

- 系统可用性 ≥99%
- 错误率 <1%

---

## 十四、安全规范

### 10.1 认证授权

- 使用JWT Token认证
- 支持API Key认证
- 基于角色的权限控制(RBAC)

### 10.2 数据安全

- 传输层加密(HTTPS)
- 文件大小限制(100MB)
- 文件类型白名单
- 敏感信息脱敏

### 10.3 限流策略

- 每用户每分钟最多100次请求
- 单用户并发最多10个请求
- 批量接口特殊限制

---

---

**文档结束**

