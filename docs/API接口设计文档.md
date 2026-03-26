# API 接口设计文档

> **文档版本**: v1.0
> **创建日期**: 2026-03-25
> **项目路径**: d:/Workspaces/well-info-extraction/

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

## 三、场景1: 单文档信息提取

### 3.1 接口定义

**接口路径**: `POST /api/v1/extract/single`

**功能**: 上传单个文档,返回结构化抽取结果

### 3.2 请求参数

#### 方式1: 文件上传

```http
POST /api/v1/extract/single
Content-Type: multipart/form-data

file: [文件]
target_fields: ["WellNo", "SpudDate", "TotalDepth"]  // 可选
category: drilling  // 可选,一级分类
doc_category: 钻井日报  // 可选,二级文档分类
enhance_images: true  // 可选,默认true
clean_text: true  // 可选,默认true
```

#### 方式2: 文件路径

```json
{
  "file_path": "/path/to/document.pdf",
  "target_fields": ["WellNo", "SpudDate", "TotalDepth"],
  "category": "drilling",
  "doc_category": "钻井日报",
  "enhance_images": true,
  "clean_text": true
}
```

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

## 四、场景2: 多文档批量信息提取

### 4.1 接口定义

**接口路径**: `POST /api/v1/extract/batch`

**功能**: 上传多个文档(可含多口井混合),返回按井分组结果

### 4.2 请求参数

#### 方式1: 文件上传

```http
POST /api/v1/extract/batch
Content-Type: multipart/form-data

files: [文件1, 文件2, ...]
target_fields: ["WellNo", "SpudDate"]  // 可选
category: drilling  // 可选
doc_category: 钻井日报  // 可选
group_by_well: true  // 可选,默认true,是否按井号分组
enhance_images: true  // 可选
clean_text: true  // 可选
```

#### 方式2: 文件路径

```json
{
  "file_paths": [
    "/path/to/doc1.pdf",
    "/path/to/doc2.pdf"
  ],
  "target_fields": ["WellNo", "SpudDate"],
  "category": "drilling",
  "doc_category": "钻井日报",
  "group_by_well": true,
  "enhance_images": true,
  "clean_text": true
}
```

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
  "message": "批量处理完成",
  "timestamp": "2026-03-25T10:35:00Z",
  "request_id": "req_20260325_103500_002",

  "batch_info": {
    "total_documents": 10,
    "successful_documents": 8,
    "partial_documents": 1,
    "failed_documents": 1,
    "total_wells": 3,
    "unrecognized_wells": 0,
    "processing_time_ms": 45000
  },

  "document_results": [
    {
      "document_id": "doc_20260325_001",
      "filename": "drilling_report.pdf",
      "status": "success",
      "well_no": "TS1-1",
      "category": "drilling",
      "category_name": "钻井资料",
      "doc_category": "钻井日报",
      "extracted_fields": {
        "WellNo": {
          "value": "TS1-1",
          "confidence": 0.98,
          "source": "文档标题",
          "unit": null,
          "validated": true
        }
        // ... 其他字段
      },
      "quality_metrics": {
        "completeness": 0.90,
        "accuracy": 0.93,
        "confidence": 0.92,
        "overall_score": 0.92
      },
      "processing_time_ms": 12000
    }
    // ... 其他文档结果
  ],

  "well_groups": {
    "TS1-1": {
      "well_info": {
        "well_no": "TS1-1",
        "document_count": 5,
        "categories": ["drilling", "mudlogging", "wireline"],
        "avg_confidence": 0.91
      },
      "documents": [
        {
          "document_id": "doc_20260325_001",
          "filename": "drilling_report.pdf",
          "category": "drilling",
          "doc_category": "钻井日报",
          "extracted_fields": { /* ... */ },
          "quality_metrics": { /* ... */ }
        }
        // ... 该井的其他文档
      ]
    },
    "HZ21-3": {
      "well_info": {
        "well_no": "HZ21-3",
        "document_count": 3,
        "categories": ["drilling", "completion"],
        "avg_confidence": 0.89
      },
      "documents": [ /* ... */ ]
    }
    // ... 其他井
  },

  "summary": {
    "by_category": {
      "drilling": {
        "count": 4,
        "avg_confidence": 0.92,
        "avg_quality": 0.91
      },
      "mudlogging": {
        "count": 2,
        "avg_confidence": 0.90,
        "avg_quality": 0.89
      }
      // ... 其他分类统计
    },
    "by_well": [
      {
        "well_no": "TS1-1",
        "document_count": 5,
        "categories": ["drilling", "mudlogging", "wireline"],
        "avg_confidence": 0.91,
        "avg_quality": 0.90
      }
      // ... 其他井统计
    ],
    "overall": {
      "avg_confidence": 0.91,
      "avg_quality": 0.90,
      "processing_speed": "13.3 docs/minute"
    }
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

## 五、场景3: 单口井批量资料处理

### 5.1 接口定义

**接口路径**: `POST /api/v1/extract/single-well-batch`

**功能**: 批量上传单口井的全部资料,返回该井的完整信息汇总

### 5.2 请求参数

```http
POST /api/v1/extract/single-well-batch
Content-Type: multipart/form-data

files: [文件1, 文件2, ...]
well_no: TS1-1  // 可选,提供可提高准确性
target_categories: ["drilling", "mudlogging", "wireline"]  // 可选
target_fields: ["WellNo", "SpudDate", "TotalDepth"]  // 可选
enhance_images: true  // 可选
clean_text: true  // 可选
```

或

```json
{
  "file_paths": [
    "/path/to/doc1.pdf",
    "/path/to/doc2.pdf"
  ],
  "well_no": "TS1-1",
  "target_categories": ["drilling", "mudlogging", "wireline"],
  "target_fields": ["WellNo", "SpudDate", "TotalDepth"],
  "enhance_images": true,
  "clean_text": true
}
```

**参数说明**:
- `files`: 上传的文件列表
- `file_paths`: 服务器本地文件路径列表
- `well_no`: 井号(可选,提供可提高准确性)
- `target_categories`: 目标分类列表
- `target_fields`: 目标字段列表
- `enhance_images`: 是否增强图像
- `clean_text`: 是否清洗文本

### 5.3 响应参数

```json
{
  "success": true,
  "message": "单井资料处理完成",
  "timestamp": "2026-03-25T10:40:00Z",
  "request_id": "req_20260325_104000_003",

  "well_info": {
    "well_no": "TS1-1",
    "well_no_confidence": 0.99,
    "document_count": 10,
    "categories": ["basic", "drilling", "mudlogging", "wireline", "testing", "completion"],
    "avg_confidence": 0.92
  },

  "document_results": [
    {
      "document_id": "doc_20260325_001",
      "filename": "drilling_design.pdf",
      "category": "drilling",
      "category_name": "钻井资料",
      "doc_category": "钻井设计",
      "status": "success",
      "extracted_fields": {
        "WellNo": {
          "value": "TS1-1",
          "confidence": 0.98,
          "source": "文档标题",
          "unit": null,
          "validated": true
        }
        // ... 其他字段
      },
      "quality_metrics": {
        "completeness": 0.95,
        "accuracy": 0.94,
        "confidence": 0.93,
        "overall_score": 0.94
      }
    }
    // ... 其他文档
  ],

  "merged_fields": {
    "basic": {
      "WellNo": {
        "value": "TS1-1",
        "confidence": 0.99,
        "sources": [
          {
            "document_id": "doc_20260325_001",
            "value": "TS1-1",
            "confidence": 0.98
          }
        ],
        "unit": null,
        "validated": true
      },
      "SpudDate": {
        "value": "2025-01-15",
        "confidence": 0.96,
        "sources": [
          {
            "document_id": "doc_20260325_001",
            "value": "2025-01-15",
            "confidence": 0.95
          },
          {
            "document_id": "doc_20260325_002",
            "value": "2025-01-15",
            "confidence": 0.97
          }
        ],
        "unit": null,
        "validated": true
      }
      // ... 其他basic字段
    },
    "drilling": {
      "RigModel": {
        "value": "ZJ50DB",
        "confidence": 0.92,
        "sources": [
          {
            "document_id": "doc_20260325_001",
            "value": "ZJ50DB",
            "confidence": 0.92
          }
        ],
        "unit": null,
        "validated": true
      }
      // ... 其他drilling字段
    }
    // ... 其他分类的字段
  },

  "quality_summary": {
    "overall_quality": 0.93,
    "by_category": {
      "basic": {
        "completeness": 1.0,
        "accuracy": 0.98,
        "confidence": 0.97
      },
      "drilling": {
        "completeness": 0.95,
        "accuracy": 0.94,
        "confidence": 0.93
      }
      // ... 其他分类
    },
    "issues": [
      {
        "category": "testing",
        "field": "OilRate",
        "issue": "文档中该字段缺失",
        "severity": "warning"
      }
    ]
  },

  "validation_summary": {
    "total_fields": 167,
    "valid_fields": 155,
    "invalid_fields": 8,
    "missing_fields": 4,
    "warnings": 12,
    "errors": 3,
    "validation_rate": 0.93
  },

  "export_data": {
    "json_url": "/api/v1/export/doc_20260325_003.json",
    "excel_url": "/api/v1/export/doc_20260325_003.xlsx",
    "database_ready": true
  },

  "processing_info": {
    "total_time_ms": 38000,
    "avg_time_per_doc_ms": 3800,
    "stages": {
      "preprocessing": 5000,
      "classification": 2000,
      "well_extraction": 1500,
      "field_extraction": 25000,
      "merging": 3000,
      "validation": 1500
    }
  }
}
```

**响应字段说明**:

#### well_info(井信息)
- `well_no`: 井号
- `well_no_confidence`: 井号置信度
- `document_count`: 文档数量
- `categories`: 涉及的分类列表
- `avg_confidence`: 平均置信度

#### document_results(文档结果列表)
- 各文档的处理结果

#### merged_fields(合并字段)
- 按分类组织的合并字段
- 每个字段包含多个来源的值和置信度
- 系统会选择置信度最高的值作为合并结果

#### quality_summary(质量汇总)
- `overall_quality`: 总体质量评分
- `by_category`: 各分类质量评分
- `issues`: 问题列表

#### validation_summary(校验汇总)
- 各类校验统计

#### export_data(导出数据)
- 各格式导出链接
- `database_ready`: 是否可以入库

---

## 六、辅助接口

### 6.1 健康检查

**接口路径**: `GET /api/v1/health`

**响应**:
```json
{
  "status": "ok",
  "service": "wellinfo-extractor",
  "version": "1.0.0",
  "timestamp": "2026-03-25T10:00:00Z"
}
```

### 6.2 文档分类查询

**接口路径**: `GET /api/v1/categories`

**响应**:
```json
{
  "categories": {
    "basic": {
      "name": "基本信息",
      "doc_categories": ["井位信息", "基础数据"]
    },
    "drilling": {
      "name": "钻井资料",
      "doc_categories": ["钻井设计", "完井设计", "钻井日报", "钻井总结"]
    },
    "mudlogging": {
      "name": "录井资料",
      "doc_categories": ["录井设计", "录井日报", "录井总结"]
    },
    "wireline": {
      "name": "测井资料",
      "doc_categories": ["测井设计", "测井解释报告", "测井成果图"]
    },
    "testing": {
      "name": "试油测试资料",
      "doc_categories": ["试油设计", "试油日报", "试油总结"]
    },
    "completion": {
      "name": "完井资料",
      "doc_categories": ["完井设计", "完井总结"]
    },
    "geology": {
      "name": "地质资料",
      "doc_categories": ["地质设计", "地质总结"]
    },
    "production": {
      "name": "生产资料",
      "doc_categories": ["生产日报", "月报", "年报"]
    }
  }
}
```

### 6.3 字段库查询

**接口路径**: `GET /api/v1/fields?category={category}`

**请求参数**:
- `category`: 分类代码(可选,不传则返回所有字段)

**响应**:
```json
{
  "category": "drilling",
  "fields": [
    {
      "name": "RigModel",
      "display_name": "钻机型号",
      "type": "string",
      "required": false,
      "description": "使用的钻机型号"
    },
    {
      "name": "TotalDepth",
      "display_name": "完钻井深",
      "type": "float",
      "required": true,
      "unit": "米",
      "description": "完钻时的井深"
    }
    // ... 其他字段
  ]
}
```

---

## 七、错误处理

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

## 八、接口版本管理

### 8.1 版本策略

- 主版本号(v1)在`/api/v{version}`路径中体现
- 兼容性变更: 增加新字段、新接口
- 不兼容变更: 升级主版本号(v2)
- 废弃接口: 保留3个版本后删除

### 8.2 版本演进

- **v1.0**: 初始版本
- **v1.1**: 增加按井分组功能
- **v2.0**: 重大架构升级(待定)

---

## 九、性能指标

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

## 十、安全规范

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

## 十一、实现代码

### 11.1 Schema定义 (schemas/models.py)

基于字段库(`config.field_schemas`)的Pydantic模型,实现双向校验:

```python
from typing import Optional, List, Any, Dict, Literal
from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime

from config.field_schemas import FIELD_SCHEMAS


class BaseProcessRequest(BaseModel):
    """基础处理请求 - 所有处理接口的通用参数"""
    target_fields: Optional[List[str]] = Field(None, description="目标字段列表")
    category: Optional[Literal["basic", "drilling", "mudlogging", ...]] = Field(None)
    doc_category: Optional[str] = Field(None)
    enhance_images: bool = Field(True)
    clean_text: bool = Field(True)

    @validator('category')
    def validate_category(cls, v):
        """校验分类是否在字段库中"""
        if v is not None and v not in FIELD_SCHEMAS.CATEGORY_MAP:
            raise ValueError(f"无效的分类: {v}")
        return v

    @validator('doc_category')
    def validate_doc_category(cls, v, values):
        """校验二级分类是否与一级分类匹配"""
        if v is not None and 'category' in values:
            doc_categories = FIELD_SCHEMAS.DOC_CATEGORIES.get(values['category'], [])
            if v not in doc_categories:
                raise ValueError(f"二级分类'{v}'不属于一级分类'{values['category']}'")
        return v

    @validator('target_fields')
    def validate_target_fields(cls, v, values):
        """校验目标字段是否在字段库中"""
        if v is not None and 'category' in values:
            valid_fields = FIELD_SCHEMAS.get_field_names(values['category'])
            invalid_fields = [f for f in v if f not in valid_fields]
            if invalid_fields:
                raise ValueError(f"无效的字段: {invalid_fields}")
        return v


class ProcessingResponse(BaseResponse):
    """单文档处理响应"""
    document_info: Optional[DocumentInfo]
    well_info: Optional[WellInfo]
    extracted_fields: Dict[str, FieldExtractionResult]

    @validator('extracted_fields')
    def validate_extracted_fields(cls, v, values):
        """校验提取的字段是否符合字段库定义"""
        if 'document_info' in values and values['document_info'].category:
            category = values['document_info'].category
            valid_fields = FIELD_SCHEMAS.get_field_names(category)
            invalid_fields = [f for f in v.keys() if f not in valid_fields]
            if invalid_fields:
                raise ValueError(f"提取了无效字段: {invalid_fields}")
        return v
```

### 11.2 API路由实现 (api/routes.py)

```python
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from typing import List
import json
from pathlib import Path

from schemas.models import (
    ProcessRequest, BatchProcessRequest, SingleWellBatchRequest,
    ProcessingResponse, BatchProcessingResponse, SingleWellBatchResponse
)
from config.settings import settings
from preprocess.file_handler import FileHandler
from validation.field_validator import FieldValidator

router = APIRouter()


def get_pipeline():
    """获取处理管道实例"""
    from api.app import pipeline_instance
    if pipeline_instance is None:
        raise HTTPException(status_code=503, detail="服务正在初始化")
    return pipeline_instance


# ========== 场景1: 单文档信息提取 ==========

@router.post("/extract/single", response_model=ProcessingResponse)
async def extract_single_document(
    file: UploadFile = File(...),
    target_fields: str = Form(None),
    category: str = Form(None),
    doc_category: str = Form(None),
    enhance_images: bool = Form(True),
    clean_text: bool = Form(True),
    pipeline = Depends(get_pipeline)
):
    """
    单文档信息提取

    场景1: 单口井批量资料一键入库
    上传单个文档,返回结构化抽取结果
    """
    try:
        # 1. 解析目标字段
        target_fields_list = None
        if target_fields:
            try:
                target_fields_list = json.loads(target_fields)
            except json.JSONDecodeError:
                raise HTTPException(400, "target_fields格式错误")

        # 2. 校验文件类型
        file_ext = Path(file.filename).suffix.lower()
        allowed_extensions = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".txt"}
        if file_ext not in allowed_extensions:
            raise HTTPException(400, f"不支持的文件类型: {file_ext}")

        # 3. 验证分类(双向校验: 请求参数 ↔ 字段库)
        if category and category not in FIELD_SCHEMAS.CATEGORY_MAP:
            raise HTTPException(400, f"无效的分类: {category}")

        # 4. 保存并处理文件
        file_handler = FileHandler(
            upload_dir=settings.STORAGE_UPLOAD_DIR,
            processed_dir=settings.STORAGE_PROCESSED_DIR
        )
        file_data = await file.read()
        save_result = file_handler.save_uploaded_file(
            file_data=file_data,
            filename=file.filename
        )

        # 5. 调用处理管道
        result = pipeline.process_file(
            file_path=save_result['file_path'],
            target_fields=target_fields_list,
            category=category,
            doc_category=doc_category
        )

        # 6. 构建响应(确保字段符合Schema定义)
        return ProcessingResponse(
            success=True,
            message="文档处理成功",
            request_id=f"req_{datetime.now().timestamp()}",
            document_info=result['document_info'],
            well_info=result['well_info'],
            extracted_fields=result['extracted_fields'],
            validation_results=result['validation_results'],
            quality_metrics=result['quality_metrics'],
            processing_info=result['processing_info']
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"处理失败: {str(e)}")


# ========== 场景2: 多文档批量信息提取 ==========

@router.post("/extract/batch", response_model=BatchProcessingResponse)
async def extract_batch_documents(
    files: List[UploadFile] = File(...),
    target_fields: str = Form(None),
    category: str = Form(None),
    group_by_well: bool = Form(True),
    pipeline = Depends(get_pipeline)
):
    """
    多文档批量信息提取

    场景2: 多口井混合资料批量处理
    批量上传文档,返回按井分组结果
    """
    try:
        if len(files) > 100:
            raise HTTPException(400, "批量处理最多支持100个文件")

        # 解析参数
        target_fields_list = json.loads(target_fields) if target_fields else None

        # 处理所有文件
        results = []
        for file in files:
            file_data = await file.read()
            save_result = file_handler.save_uploaded_file(
                file_data=file_data,
                filename=file.filename
            )

            result = pipeline.process_file(
                file_path=save_result['file_path'],
                target_fields=target_fields_list,
                category=category
            )
            results.append(result)

        # 按井号分组
        well_groups = {}
        for result in results:
            well_no = result['well_info'].well_no or "未识别"
            if well_no not in well_groups:
                well_groups[well_no] = []
            well_groups[well_no].append(result)

        # 构建响应
        return BatchProcessingResponse(
            success=True,
            message="批量处理完成",
            batch_info=pipeline.calculate_batch_info(results, well_groups),
            document_results=results,
            well_groups=well_groups,
            summary=pipeline.calculate_summary(results, well_groups)
        )

    except Exception as e:
        raise HTTPException(500, f"批量处理失败: {str(e)}")


# ========== 场景3: 单井批量资料处理 ==========

@router.post("/extract/single-well-batch", response_model=SingleWellBatchResponse)
async def extract_single_well_batch(
    files: List[UploadFile] = File(...),
    well_no: str = Form(None),
    target_categories: str = Form(None),
    pipeline = Depends(get_pipeline)
):
    """
    单井批量资料处理

    场景3: 单口井批量资料一键入库
    批量上传单井资料,返回完整井信息
    """
    try:
        # 解析目标分类
        target_categories_list = (
            json.loads(target_categories) if target_categories else None
        )

        # 处理所有文档
        results = []
        for file in files:
            file_data = await file.read()
            save_result = file_handler.save_uploaded_file(
                file_data=file_data,
                filename=file.filename
            )

            result = pipeline.process_file(
                file_path=save_result['file_path'],
                target_categories=target_categories_list
            )
            results.append(result)

        # 合并字段(跨文档)
        merged_fields = pipeline.merge_fields_across_documents(results, well_no)

        # 质量汇总
        quality_summary = pipeline.calculate_quality_summary(results)

        # 校验汇总
        validation_summary = pipeline.calculate_validation_summary(results)

        # 构建响应
        return SingleWellBatchResponse(
            success=True,
            message="单井资料处理完成",
            well_info=WellInfo(
                well_no=well_no,
                well_no_confidence=max(r['well_info'].well_no_confidence for r in results)
            ),
            document_results=results,
            merged_fields=merged_fields,
            quality_summary=quality_summary,
            validation_summary=validation_summary,
            export_data=ExportData(database_ready=True),
            processing_info=ProcessingInfo(
                processing_time_ms=sum(r['processing_info'].processing_time_ms for r in results)
            )
        )

    except Exception as e:
        raise HTTPException(500, f"单井批量处理失败: {str(e)}")
```

### 11.3 双向校验实现

#### 方向1: 请求参数 → 字段库

```python
@validator('category')
def validate_category(cls, v):
    """校验分类是否在字段库中"""
    if v is not None:
        valid_categories = list(FIELD_SCHEMAS.CATEGORY_MAP.keys())
        if v not in valid_categories:
            raise ValueError(f"无效的分类: {v}, 支持的分类: {valid_categories}")
    return v


@validator('target_fields')
def validate_target_fields(cls, v, values):
    """校验目标字段是否在字段库中"""
    if v is not None and 'category' in values:
        category = values['category']
        valid_fields = FIELD_SCHEMAS.get_field_names(category)
        invalid_fields = [f for f in v if f not in valid_fields]
        if invalid_fields:
            raise ValueError(f"无效的字段: {invalid_fields}")
    return v
```

#### 方向2: 响应数据 → 字段库

```python
@validator('extracted_fields')
def validate_extracted_fields(cls, v, values):
    """校验提取的字段是否符合字段库定义"""
    if 'document_info' in values and values['document_info']:
        category = values['document_info'].category
        if category:
            valid_fields = FIELD_SCHEMAS.get_field_names(category)
            invalid_fields = [f for f in v.keys() if f not in valid_fields]
            if invalid_fields:
                raise ValueError(
                    f"提取了无效字段: {invalid_fields}。"
                    f"分类'{category}'支持的字段: {valid_fields}"
                )
    return v
```

#### 方向3: 字段值校验(结合字段定义)

```python
class FieldValidator:
    """字段验证器 - 基于字段库定义校验字段值"""

    def validate(self, field_name: str, field_value: Any, category: str):
        """根据字段库定义验证字段值"""
        # 获取字段定义
        field_def = self._get_field_definition(field_name, category)

        if field_def:
            # 1. 类型校验
            if field_def.data_type == "date":
                self._validate_date(field_value)
            elif field_def.data_type in ["int", "float"]:
                self._validate_number(field_value, field_def)

            # 2. 范围校验
            if field_def.min_value is not None:
                if float(field_value) < field_def.min_value:
                    raise ValueError(f"值过小: {field_value} < {field_def.min_value}")

            if field_def.max_value is not None:
                if float(field_value) > field_def.max_value:
                    raise ValueError(f"值过大: {field_value} > {field_def.max_value}")

            # 3. 必填校验
            if field_def.required and (field_value is None or field_value == ""):
                raise ValueError(f"必填字段为空: {field_name}")
```

### 11.4 测试用例

```python
import pytest
from schemas.models import ProcessRequest, ProcessingResponse

def test_validate_category():
    """测试分类校验"""
    # 有效分类
    request = ProcessRequest(category="drilling")
    assert request.category == "drilling"

    # 无效分类
    with pytest.raises(ValueError):
        ProcessRequest(category="invalid_category")


def test_validate_target_fields():
    """测试目标字段校验"""
    # 有效字段
    request = ProcessRequest(
        category="drilling",
        target_fields=["WellNo", "RigModel", "TotalDepth"]
    )
    assert request.target_fields == ["WellNo", "RigModel", "TotalDepth"]

    # 无效字段
    with pytest.raises(ValueError):
        ProcessRequest(
            category="drilling",
            target_fields=["WellNo", "InvalidField"]
        )


def test_validate_extracted_fields():
    """测试提取字段校验"""
    # 有效字段
    response = ProcessingResponse(
        success=True,
        message="OK",
        document_info={
            "category": "drilling",
            "document_id": "doc001"
        },
        extracted_fields={
            "WellNo": {"value": "TS1-1", "confidence": 0.95},
            "RigModel": {"value": "ZJ50DB", "confidence": 0.85}
        }
    )

    # 无效字段
    with pytest.raises(ValueError):
        ProcessingResponse(
            success=True,
            message="OK",
            document_info={
                "category": "drilling",
                "document_id": "doc001"
            },
            extracted_fields={
                "WellNo": {"value": "TS1-1", "confidence": 0.95},
                "InvalidField": {"value": "xxx", "confidence": 0.5}
            }
        )
```

---

**文档结束**
