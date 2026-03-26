# AI 驱动油气井关键信息提取 - 系统架构设计 (最终开发版)

> **文档版本**: v2.0 (可直接开发版)
> **创建日期**: 2025-03-23
> **项目路径**: d:/Workspaces/well-info-extraction/
> **说明**: 基于PROJECT_CONTEXT.md优化,简化复杂度,聚焦核心功能

---

## 一、系统概述

### 1.1 系统定位

AI 驱动油气井关键信息提取系统 - 基于 LLM 的结构化信息提取平台。

**核心能力**: 将非结构化油气井资料 → 结构化JSON数据

### 1.2 核心目标 (MVP阶段)

| 指标 | 目标值 |
|------|--------|
| 单文档处理时间 | <30秒 |
| 文档分类准确率 | ≥90% |
| 关键字段抽取准确率 | ≥90% |
| 井号识别率 | ≥90% |
| 人工审核率 | <15% |

### 1.3 系统特色 (MVP)

- **多格式支持**: PDF、Word、Excel、TXT
- **智能分类**: 8大类文档自动分类
- **精准抽取**: LLM驱动的结构化信息抽取
- **质量保障**: 规则校验 + 置信度评估
- **API服务**: RESTful API,支持单文档/批量处理

---

## 二、架构设计 (简化版)

### 2.1 总体架构

```
┌─────────────────────────────────────────────────────────┐
│                    客户端层                             │
│  ┌──────────────┐  ┌──────────────┐                     │
│  │  API测试工具  │  │  简单Web界面 │                     │
│  │  (Postman)   │  │  (Streamlit) │                     │
│  └──────┬───────┘  └──────┬───────┘                     │
└─────────┼────────────────┼────────────────────────────┘
          │                │
          └────────────────┼────────────── HTTPS
                           │
┌──────────────────────────┼────────────────────────────┐
│                  FastAPI 服务层                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  - RESTful API                                   │  │
│  │  - 认证鉴权 (JWT)                                │  │
│  │  - 限流保护                                      │  │
│  │  - 请求日志                                      │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────────┼────────────────────────────┘
                           │
┌──────────────────────────┼────────────────────────────┐
│                 业务逻辑层 (Pipeline)                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │  1. 文档预处理 (OCR + 解析)                       │  │
│  │  2. 文档分类 (LLM)                                 │  │
│  │  3. 井号识别 (规则 + LLM)                          │  │
│  │  4. 字段抽取 (LLM)                                │  │
│  │  5. 规则校验 + 置信度评估                          │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────────┼────────────────────────────┘
                           │
┌──────────────────────────┼────────────────────────────┐
│                  数据存储层                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │PostgreSQL│  │  Redis   │  │  本地文件 │           │
│  │(元数据)   │  │  (缓存)  │  │  (文档)  │           │
│  └──────────┘  └──────────┘  └──────────┘           │
└─────────────────────────────────────────────────────┘
                           │
┌──────────────────────────┼────────────────────────────┐
│                  外部服务层                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │  LLM API │  │ PaddleOCR│  │  Embedding│           │
│  │(Qwen/DS)  │  │  (Docker)│  │  (本地)   │           │
│  └──────────┘  └──────────┘  └──────────┘           │
└─────────────────────────────────────────────────────┘
```

### 2.2 核心处理流程

```
文档上传
   ↓
【Stage 1】文档预处理
   ├─ PDF解析 (PyMuPDF)
   ├─ OCR识别 (PaddleOCR,如需)
   ├─ Word/Excel 解析
   └─ 提取: full_text + text_preview + tables
   ↓
【Stage 2】文档分类
   ├─ 使用 LLM (Qwen2.5-14B/DeepSeek-V3)
   └─ 返回: category + confidence
   ↓
【Stage 3】井号识别
   ├─ 正则规则提取 (优先)
   ├─ LLM 归一化 (候选项≤3个)
   └─ LLM 直接识别 (候选项>3个)
   ↓
【Stage 4】字段抽取
   ├─ 根据分类选择提示词模板
   ├─ LLM 提取字段
   └─ 返回: fields + confidence
   ↓
【Stage 5】校验与评分
   ├─ 数值范围校验
   ├─ 日期格式校验
   ├─ 必填字段检查
   └─ 计算整体置信度
   ↓
结构化 JSON 输出
```

---

## 三、核心模块设计

### 3.1 项目目录结构

```
wellinfo_extractor/
├── config/                      # 配置模块
│   ├── __init__.py
│   ├── settings.py              # 全局配置 (API keys、模型endpoint)
│   ├── field_schemas.py         # 各类文档字段定义
│   └── prompts.py               # 提示词模板 (集中管理)
│
├── preprocess/                  # 文档预处理模块
│   ├── __init__.py
│   ├── ocr_engine.py           # OCR 引擎 (PaddleOCR)
│   ├── pdf_parser.py            # PDF 解析器
│   ├── doc_parser.py            # Word/Excel/PPT 解析器
│   └── table_extractor.py       # 表格提取
│
├── models/                      # AI 模型模块
│   ├── __init__.py
│   ├── classifier.py           # 文档分类模型
│   ├── wellno_extractor.py     # 井号识别模型
│   └── field_extractor.py      # 字段抽取模型
│
├── validation/                  # 校验模块
│   ├── __init__.py
│   ├── rule_validator.py       # 规则校验引擎
│   └── confidence_scorer.py    # 置信度评估引擎
│
├── pipeline/                    # 处理管道
│   ├── __init__.py
│   ├── single_well.py          # 单文档处理管道
│   └── batch_processor.py      # 批量处理管道
│
├── api/                         # API 接口层
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── routes.py               # 路由定义
│   ├── auth.py                 # 认证鉴权
│   └── middleware.py           # 中间件
│
├── db/                          # 数据库模块
│   ├── __init__.py
│   ├── models.py               # SQLAlchemy 模型
│   ├── crud.py                 # CRUD 操作
│   └── database.py             # 数据库连接
│
├── schemas/                     # Pydantic 模型
│   ├── __init__.py
│   ├── request.py              # 请求模型
│   └── response.py             # 响应模型
│
├── utils/                       # 工具模块
│   ├── __init__.py
│   ├── logger.py               # 日志工具
│   ├── exceptions.py           # 自定义异常
│   └── helpers.py              # 辅助函数
│
├── tests/                       # 测试模块
│   ├── __init__.py
│   ├── test_pipeline.py
│   └── test_api.py
│
├── storage/                     # 本地存储
│   ├── uploads/                 # 上传的原始文档
│   ├── processed/               # 处理结果 (JSON)
│   └── cache/                   # Embedding缓存
│
├── requirements.txt              # Python 依赖
├── .env.example                # 环境变量示例
├── Dockerfile                  # Docker 镜像
├── docker-compose.yml          # Docker Compose 配置
└── README.md                   # 项目说明
```

### 3.2 配置模块 (config/)

#### 3.2.1 全局配置

```python
# config/settings.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """全局配置"""
    
    # ========== 应用配置 ==========
    APP_NAME: str = "WellInfo Extractor"
    APP_VERSION: str = "v1.0.0"
    DEBUG: bool = False
    
    # ========== LLM 配置 ==========
    LLM_API_KEY: str
    LLM_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"  # 通义千问
    LLM_MODEL_CLASSIFY: str = "qwen2.5-14b-instruct"      # 分类模型
    LLM_MODEL_EXTRACT: str = "qwen2.5-72b-instruct"      # 抽取模型
    LLM_MODEL_WELLNO: str = "qwen2.5-7b-instruct"        # 井号识别
    LLM_TEMPERATURE: float = 0.05
    LLM_MAX_TOKENS: int = 4096
    
    # ========== OCR 配置 ==========
    OCR_USE_GPU: bool = False
    OCR_LANG: str = "ch"
    
    # ========== 数据库配置 ==========
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/wellinfo"
    
    # ========== Redis 配置 ==========
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_TTL: int = 3600  # 缓存过期时间 (秒)
    
    # ========== 存储配置 ==========
    STORAGE_PATH: str = "./storage"
    UPLOAD_DIR: str = "./storage/uploads"
    PROCESSED_DIR: str = "./storage/processed"
    CACHE_DIR: str = "./storage/cache"
    
    # ========== API 配置 ==========
    API_PREFIX: str = "/api/v1"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    BATCH_MAX_FILES: int = 100
    
    # ========== JWT 配置 ==========
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时
    
    # ========== 限流配置 ==========
    RATE_LIMIT_PER_USER: int = 10  # 每秒请求数
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

#### 3.2.2 字段Schema定义

```python
# config/field_schemas.py
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class FieldDefinition:
    """字段定义"""
    name: str                    # 字段名
    display_name: str            # 显示名
    data_type: str              # 数据类型: string | float | int | date
    required: bool              # 是否必填
    weight: float = 1.0         # 权重 (用于置信度计算)
    min_value: float = None     # 最小值 (数值型)
    max_value: float = None     # 最大值 (数值型)

class FieldSchemas:
    """各类文档字段定义"""
    
    # ========== 基本信息 (23个字段) ==========
    BASIC_FIELDS: List[FieldDefinition] = [
        FieldDefinition("WellNo", "井号", "string", True, 2.0),
        FieldDefinition("DocCategory", "文档分类", "string", True, 1.5),
        FieldDefinition("Oilfield", "油田/区块", "string", False),
        FieldDefinition("WellType", "井别", "string", False),
        FieldDefinition("WellPattern", "井型", "string", False),
        FieldDefinition("SpudDate", "开钻日期", "date", False),
        FieldDefinition("CompletionDate", "完钻日期", "date", False),
        FieldDefinition("WellCompletionDate", "完井日期", "date", False),
        FieldDefinition("DrillingDays", "钻井周期", "int", False, 1.0, 0, 365),
        FieldDefinition("CompletionDays", "完井周期", "int", False, 1.0, 0, 365),
        FieldDefinition("DesignDepth", "设计井深", "float", False, 1.2, 0, 12000),
        FieldDefinition("TotalDepth", "完钻井深", "float", False, 1.5, 100, 12000),
        FieldDefinition("BottomFormation", "完钻层位", "string", False),
        FieldDefinition("DrillingPurpose", "钻探目的", "string", False),
        # ... 更多字段
    ]
    
    # ========== 钻井资料 (21个字段) ==========
    DRILLING_FIELDS: List[FieldDefinition] = [
        FieldDefinition("RigModel", "钻机型号", "string", False),
        FieldDefinition("BitProgram", "钻头程序", "string", False, 1.2),
        FieldDefinition("CasingProgram", "套管程序", "string", False, 1.2),
        FieldDefinition("MudSystem", "钻井液体系", "string", False),
        FieldDefinition("WellStructure", "井身结构", "string", False),
        FieldDefinition("DeviationData", "井斜数据", "string", False),
        FieldDefinition("CementingData", "固井数据", "string", False),
        FieldDefinition("Accidents", "钻井事故", "string", False),
        FieldDefinition("CreateDate", "编制日期", "date", False),
        FieldDefinition("CreateUnit", "编制单位", "string", False),
        FieldDefinition("Creator", "编制人", "string", False),
        # ... 更多字段
    ]
    
    # ========== 试油测试资料 (20个字段,重点) ==========
    TESTING_FIELDS: List[FieldDefinition] = [
        FieldDefinition("TestFormation", "试油层位", "string", True, 1.5),
        FieldDefinition("TestInterval", "试油井段", "string", True, 1.5),
        FieldDefinition("TestDate", "试油日期", "date", True, 1.2),
        FieldDefinition("TestMethod", "试油方式", "string", False),
        FieldDefinition("OilRate", "日产油量", "float", True, 2.0, 0, 5000),
        FieldDefinition("GasRate", "日产气量", "float", False, 2.0, 0, 1000),
        FieldDefinition("WaterRate", "日产水量", "float", False, 2.0, 0, 10000),
        FieldDefinition("TubingPressure", "油压", "float", False, 1.5, 0, 200),
        FieldDefinition("CasingPressure", "套压", "float", False, 1.5, 0, 200),
        FieldDefinition("FormationPressure", "地层压力", "float", False, 1.5, 0, 300),
        FieldDefinition("FormationTemp", "地层温度", "float", False, 1.2, 10, 350),
        FieldDefinition("OilProperties", "原油性质", "string", False),
        FieldDefinition("Conclusion", "结论", "string", False),
        # ... 更多字段
    ]
    
    # ========== 其他文档分类 ==========
    MUDLOGGING_FIELDS: List[FieldDefinition] = [...]  # 录井资料
    WIRELINE_FIELDS: List[FieldDefinition] = [...]     # 测井资料
    COMPLETION_FIELDS: List[FieldDefinition] = [...]  # 完井资料
    GEOLOGY_FIELDS: List[FieldDefinition] = [...]     # 地质资料
    PRODUCTION_FIELDS: List[FieldDefinition] = [...]  # 生产资料
    
    # ========== 分类映射 ==========
    CATEGORY_MAP: Dict[str, str] = {
        "basic": "基本信息",
        "drilling": "钻井资料",
        "mudlogging": "录井资料",
        "wireline": "测井资料",
        "testing": "试油测试资料",
        "completion": "完井资料",
        "geology": "地质资料",
        "production": "生产资料",
    }
    
    # ========== 字段定义映射 ==========
    CATEGORY_FIELDS_MAP: Dict[str, List[FieldDefinition]] = {
        "basic": BASIC_FIELDS,
        "drilling": DRILLING_FIELDS,
        "mudlogging": MUDLOGGING_FIELDS,
        "wireline": WIRELINE_FIELDS,
        "testing": TESTING_FIELDS,
        "completion": COMPLETION_FIELDS,
        "geology": GEOLOGY_FIELDS,
        "production": PRODUCTION_FIELDS,
    }
    
    @classmethod
    def get_fields_by_category(cls, category: str) -> List[FieldDefinition]:
        """根据分类获取字段定义"""
        return cls.CATEGORY_FIELDS_MAP.get(category, cls.BASIC_FIELDS)
    
    @classmethod
    def get_field_names(cls, category: str) -> List[str]:
        """获取字段名列表"""
        fields = cls.get_fields_by_category(category)
        return [f.name for f in fields]
```

#### 3.2.3 提示词模板

```python
# config/prompts.py
from typing import Dict

class Prompts:
    """提示词模板"""
    
    # ========== System Prompt ==========
    SYSTEM_PROMPT = """你是一位专业的油气井信息提取专家。
你的任务是从油气井技术文档中准确提取结构化信息。
严格按照指定的JSON Schema输出结果。
保持专业术语准确性,对于不确定的字段,设置较低的置信度。"""
    
    # ========== 文档分类提示词 ==========
    CLASSIFY_PROMPT = """请分析以下文档内容,判断其属于哪一类油气井资料。

文档内容预览:
{document_text}

可选分类:
- basic: 基本信息 (包含井号、井别、井深等基本信息)
- drilling: 钻井资料 (包含钻头程序、套管程序、固井数据等)
- mudlogging: 录井资料 (包含气测数据、岩屑描述、钻时数据等)
- wireline: 测井资料 (包含声波测井、中子测井、密度测井等)
- testing: 试油测试资料 (包含日产油量、日产气量、压力、温度等)
- completion: 完井资料 (包含射孔参数、完井管柱等)
- geology: 地质资料 (包含储层描述、岩心分析、沉积相分析等)
- production: 生产资料 (包含生产动态、含水率、累计产量等)

输出JSON格式:
{{
  "category": "分类代码",
  "confidence": 0.95,
  "evidence": "分类依据简述"
}}

请只输出JSON,不要有其他内容。"""
    
    # ========== 井号识别提示词 ==========
    WELLNO_EXTRACT_PROMPT = """从以下文档中提取油气井井号。

文档内容:
{document_text}

任务:
1. 识别文档中出现的所有井号
2. 判断哪个是主要井号 (primary_well)
3. 对井号进行归一化处理 (统一大写、去除多余字符)

输出JSON格式:
{{
  "wells": [
    {{"raw_text": "原始文本", "normalized": "归一化后", "confidence": 0.95}},
    ...
  ],
  "primary_well": "归一化后的主要井号"
}}

请只输出JSON,不要有其他内容。"""
    
    # ========== 基本信息抽取提示词 ==========
    BASIC_EXTRACT_PROMPT = """从以下油气井基本信息文档中提取关键字段。

文档内容:
{document_text}

提取字段:
- WellNo (井号)
- DocCategory (文档分类: basic)
- Oilfield (油田/区块)
- WellType (井别)
- WellPattern (井型)
- SpudDate (开钻日期,格式: YYYY-MM-DD)
- CompletionDate (完钻日期,格式: YYYY-MM-DD)
- WellCompletionDate (完井日期,格式: YYYY-MM-DD)
- DrillingDays (钻井周期,单位: 天)
- CompletionDays (完井周期,单位: 天)
- DesignDepth (设计井深,单位: 米)
- TotalDepth (完钻井深,单位: 米)
- BottomFormation (完钻层位)
- DrillingPurpose (钻探目的)

输出JSON格式:
{{
  "WellNo": {{"value": "井号", "confidence": 0.95}},
  "DocCategory": {{"value": "basic", "confidence": 1.0}},
  ...
}}

置信度说明:
- 0.95-1.0: 文档中明确提到,非常确定
- 0.80-0.95: 文档中提到,较为确定
- 0.60-0.80: 需要推断,有一定不确定性
- 0.30-0.60: 不确定,需要人工审核
- <0.30: 可能错误

请只输出JSON,不要有其他内容。"""
    
    # ========== 试油测试资料抽取提示词 ==========
    TESTING_EXTRACT_PROMPT = """从以下试油测试资料中提取关键字段。

文档内容:
{document_text}

提取字段:
- TestFormation (试油层位)
- TestInterval (试油井段)
- TestDate (试油日期,格式: YYYY-MM-DD)
- TestMethod (试油方式)
- OilRate (日产油量,单位: m³/d)
- GasRate (日产气量,单位: 10⁴m³/d)
- WaterRate (日产水量,单位: m³/d)
- TubingPressure (油压,单位: MPa)
- CasingPressure (套压,单位: MPa)
- FormationPressure (地层压力,单位: MPa)
- FormationTemp (地层温度,单位: °C)
- OilProperties (原油性质)
- Conclusion (结论)

输出JSON格式:
{{
  "WellNo": {{"value": "井号", "confidence": 0.95}},
  "DocCategory": {{"value": "testing", "confidence": 1.0}},
  "TestFormation": {{"value": "试油层位", "confidence": 0.90}},
  "TestInterval": {{"value": "试油井段", "confidence": 0.90}},
  ...
}}

注意:
1. OilRate/GasRate/WaterRate如果包含数值和单位,只提取数值部分
2. 日期格式统一为 YYYY-MM-DD
3. 置信度根据提取的确定性设置

请只输出JSON,不要有其他内容。"""
    
    # ========== 提示词映射 ==========
    PROMPT_MAP: Dict[str, str] = {
        "basic": BASIC_EXTRACT_PROMPT,
        "drilling": DRILLING_EXTRACT_PROMPT,      # 需要补充
        "mudlogging": MUDLOGGING_EXTRACT_PROMPT,  # 需要补充
        "wireline": WIRELINE_EXTRACT_PROMPT,      # 需要补充
        "testing": TESTING_EXTRACT_PROMPT,
        "completion": COMPLETION_EXTRACT_PROMPT,   # 需要补充
        "geology": GEOLOGY_EXTRACT_PROMPT,        # 需要补充
        "production": PRODUCTION_EXTRACT_PROMPT,  # 需要补充
    }
```

### 3.3 数据库设计

#### 3.3.1 表结构 (PostgreSQL)

```sql
-- 文档表
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_size BIGINT NOT NULL,
    file_format VARCHAR(20) NOT NULL,
    
    well_no VARCHAR(50),
    doc_category VARCHAR(20) NOT NULL,
    
    upload_user_id UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000000',
    upload_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    process_time TIMESTAMP,
    
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending | processing | success | failed
    overall_confidence DECIMAL(5,3),
    processing_time_ms INT,
    error_message TEXT,
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_well_no (well_no),
    INDEX idx_category (doc_category),
    INDEX idx_status (status),
    INDEX idx_upload_time (upload_time),
    INDEX idx_upload_user (upload_user_id)
);

-- 提取结果表
CREATE TABLE extracted_fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    field_name VARCHAR(100) NOT NULL,
    field_value TEXT,
    field_confidence DECIMAL(5,3),
    field_source VARCHAR(20) DEFAULT 'llm',  -- ocr | llm | manual
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (document_id, field_name),
    INDEX idx_document_id (document_id),
    INDEX idx_field_name (field_name)
);

-- 校验结果表
CREATE TABLE validation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    field_name VARCHAR(100) NOT NULL,
    passed BOOLEAN NOT NULL,
    error_type VARCHAR(20),      -- missing | format | range
    error_message TEXT,
    suggestion TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_document_id (document_id),
    INDEX idx_passed (passed)
);

-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',  -- admin | reviewer | user
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    
    INDEX idx_username (username),
    INDEX idx_role (role)
);

-- 统计数据表
CREATE TABLE statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stat_date DATE NOT NULL,
    total_documents INT NOT NULL DEFAULT 0,
    success_documents INT NOT NULL DEFAULT 0,
    failed_documents INT NOT NULL DEFAULT 0,
    avg_confidence DECIMAL(5,3),
    avg_processing_time_ms INT,
    total_fields_extracted INT DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (stat_date),
    INDEX idx_stat_date (stat_date)
);

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 3.4 API 接口设计

#### 3.4.1 接口列表

| 路径 | 方法 | 功能 | 认证 |
|------|------|------|------|
| `/api/v1/health` | GET | 健康检查 | 无 |
| `/api/v1/auth/login` | POST | 用户登录 | 无 |
| `/api/v1/extract/single` | POST | 单文档提取 | JWT |
| `/api/v1/extract/batch` | POST | 批量提取 | JWT |
| `/api/v1/documents/{doc_id}` | GET | 查询文档详情 | JWT |
| `/api/v1/documents` | GET | 查询文档列表 | JWT |
| `/api/v1/export/json/{doc_id}` | GET | 导出JSON | JWT |

#### 3.4.2 响应格式

**成功响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "document_id": "uuid",
    "well_no": "TS1-1",
    "doc_category": "drilling",
    "overall_confidence": 0.92,
    "extracted_fields": {
      "WellNo": {"value": "TS1-1", "confidence": 0.95},
      "RigModel": {"value": "ZJ50DB", "confidence": 0.85},
      ...
    },
    "validation_issues": [...],
    "processing_time_ms": 12500
  }
}
```

**错误响应**:
```json
{
  "code": 400,
  "message": "Invalid request",
  "details": "File size exceeds limit"
}
```

### 3.5 核心处理管道

```python
# pipeline/single_well.py
from dataclasses import dataclass
from typing import Dict, List, Optional
import time
from pathlib import Path
from openai import OpenAI

from config.settings import get_settings
from config.field_schemas import FieldSchemas
from config.prompts import Prompts
from preprocess.pdf_parser import PDFParser
from preprocess.ocr_engine import OCREngine
from models.classifier import DocumentClassifier
from models.wellno_extractor import WellNoExtractor
from models.field_extractor import FieldExtractor
from validation.rule_validator import RuleValidator
from validation.confidence_scorer import ConfidenceScorer
from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ProcessingResult:
    """单文档处理结果"""
    file_path: str
    well_no: str = ""
    doc_category: str = ""
    extracted_fields: Dict = None
    validation_results: List = None
    overall_confidence: float = 0.0
    processing_time_ms: int = 0
    status: str = "pending"  # pending | success | partial | failed
    error_message: str = ""
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "file_path": self.file_path,
            "well_no": self.well_no,
            "doc_category": self.doc_category,
            "extracted_fields": self.extracted_fields,
            "validation_results": [
                {
                    "field": r.field,
                    "passed": r.passed,
                    "error_type": r.error_type,
                    "message": r.message,
                    "suggestion": r.suggestion
                } for r in (self.validation_results or [])
            ],
            "overall_confidence": self.overall_confidence,
            "processing_time_ms": self.processing_time_ms,
            "status": self.status,
            "error_message": self.error_message
        }

class SingleWellPipeline:
    """单文档处理管道"""
    
    def __init__(self, config=None):
        self.settings = config or get_settings()
        
        # 初始化 LLM 客户端
        self.llm_client = OpenAI(
            api_key=self.settings.LLM_API_KEY,
            base_url=self.settings.LLM_BASE_URL
        )
        
        # 初始化 OCR 引擎
        self.ocr_engine = OCREngine(use_gpu=self.settings.OCR_USE_GPU)
        
        # 初始化文档解析器
        self.pdf_parser = PDFParser(ocr_engine=self.ocr_engine)
        
        # 初始化 AI 模型
        self.classifier = DocumentClassifier(self.llm_client, self.settings)
        self.wellno_extractor = WellNoExtractor(self.llm_client, self.settings)
        self.field_extractor = FieldExtractor(self.llm_client, self.settings)
        
        # 初始化校验引擎
        self.validator = RuleValidator()
        self.scorer = ConfidenceScorer()
    
    def process(self, file_path: str) -> ProcessingResult:
        """处理单个文档"""
        start_time = time.time()
        
        result = ProcessingResult(file_path=file_path)
        
        try:
            logger.info(f"开始处理文档: {file_path}")
            
            # ========== Step 1: 文档解析 ==========
            logger.debug("Step 1: 文档解析")
            parsed_doc = self._parse_document(file_path)
            result.doc_category = "basic"  # 默认分类
            
            # ========== Step 2: 文档分类 ==========
            logger.debug("Step 2: 文档分类")
            classify_result = self.classifier.classify(
                text_preview=parsed_doc["text_preview"]
            )
            result.doc_category = classify_result["category"]
            logger.info(f"文档分类: {result.doc_category}, 置信度: {classify_result['confidence']}")
            
            # ========== Step 3: 井号识别 ==========
            logger.debug("Step 3: 井号识别")
            wellno_result = self.wellno_extractor.extract(
                full_text=parsed_doc["full_text"]
            )
            result.well_no = wellno_result.get("primary_well", "未识别")
            logger.info(f"井号识别: {result.well_no}")
            
            # ========== Step 4: 字段抽取 ==========
            logger.debug("Step 4: 字段抽取")
            extracted = self.field_extractor.extract(
                doc_text=parsed_doc["full_text"],
                category=result.doc_category,
                tables=parsed_doc.get("tables", [])
            )
            
            # 确保 WellNo 和 DocCategory 在提取结果中
            if "WellNo" not in extracted:
                extracted["WellNo"] = {
                    "value": result.well_no,
                    "confidence": 0.95 if result.well_no != "未识别" else 0.5
                }
            if "DocCategory" not in extracted:
                extracted["DocCategory"] = {
                    "value": result.doc_category,
                    "confidence": classify_result["confidence"]
                }
            
            result.extracted_fields = extracted
            logger.info(f"提取字段数量: {len(extracted)}")
            
            # ========== Step 5: 校验与评分 ==========
            logger.debug("Step 5: 校验与评分")
            validation_results = self.validator.validate(
                extracted_data=extracted,
                category=result.doc_category
            )
            result.validation_results = validation_results
            
            overall_confidence = self.scorer.score(
                extracted_data=extracted,
                validation_results=validation_results
            )
            result.overall_confidence = overall_confidence
            logger.info(f"整体置信度: {overall_confidence}")
            
            # ========== 确定状态 ==========
            result.status = self._determine_status(validation_results, overall_confidence)
            
            # 计算处理时间
            result.processing_time_ms = int((time.time() - start_time) * 1000)
            
            logger.info(f"文档处理完成: {file_path}, 状态: {result.status}, 耗时: {result.processing_time_ms}ms")
            
        except Exception as e:
            logger.error(f"文档处理失败: {file_path}, 错误: {str(e)}", exc_info=True)
            result.status = "failed"
            result.error_message = str(e)
            result.processing_time_ms = int((time.time() - start_time) * 1000)
        
        return result
    
    def _parse_document(self, file_path: str) -> Dict:
        """解析文档"""
        file_path = Path(file_path)
        ext = file_path.suffix.lower()
        
        if ext == '.pdf':
            return self.pdf_parser.parse(str(file_path))
        elif ext in ['.doc', '.docx']:
            from preprocess.doc_parser import DocxParser
            return DocxParser().parse(str(file_path))
        elif ext in ['.xls', '.xlsx']:
            from preprocess.doc_parser import ExcelParser
            return ExcelParser().parse(str(file_path))
        elif ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            return {
                "full_text": text,
                "text_preview": text[:2000],
                "tables": []
            }
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
    
    def _determine_status(self, validation_results, overall_confidence) -> str:
        """确定处理状态"""
        # 有严重校验错误
        critical_errors = [r for r in validation_results 
                          if not r.passed and r.error_type == "missing"]
        if critical_errors:
            return "partial"
        
        # 置信度低
        if overall_confidence < 0.70:
            return "partial"
        
        return "success"
```

---

## 四、部署配置

### 4.1 Docker Compose 配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  # FastAPI 应用
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://wellinfo:wellinfo123@postgres:5432/wellinfo
      - REDIS_URL=redis://redis:6379/0
      - LLM_API_KEY=${LLM_API_KEY}
      - LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - DEBUG=false
    depends_on:
      - postgres
      - redis
    volumes:
      - ./storage:/app/storage
    restart: unless-stopped

  # PostgreSQL 数据库
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=wellinfo
      - POSTGRES_USER=wellinfo
      - POSTGRES_PASSWORD=wellinfo123
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  # Redis 缓存
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped

  # 简单的Web界面 (Streamlit)
  web:
    build: ./web
    ports:
      - "8501:8501"
    environment:
      - API_URL=http://app:8000
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### 4.2 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建存储目录
RUN mkdir -p storage/uploads storage/processed storage/cache

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4.3 依赖文件

```txt
# requirements.txt
# FastAPI
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
pydantic-settings==2.1.0

# 数据库
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1

# Redis
redis==5.0.1
hiredis==2.2.3

# LLM
openai==1.3.5

# OCR
paddleocr==2.7.0.3
paddlepaddle==2.5.2

# 文档处理
PyMuPDF==1.23.8
python-docx==1.1.0
openpyxl==3.1.2

# 工具库
python-dotenv==1.0.0
loguru==0.7.2
requests==2.31.0

# 认证
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

---

## 五、开发优先级

### Phase 1: 核心功能 (第1-4周)

1. ✅ 项目结构搭建
2. ✅ 配置模块开发 (settings.py, field_schemas.py, prompts.py)
3. ✅ 数据库设计与初始化
4. ✅ 文档解析模块 (PDF、Word、Excel)
5. ✅ 文档分类模型
6. ✅ 井号识别模型
7. ✅ 字段抽取模型 (优先实现 testing 类)
8. ✅ 规则校验引擎
9. ✅ 单文档处理管道
10. ✅ FastAPI 基础接口

### Phase 2: 功能完善 (第5-6周)

1. ⬜ 批量处理管道
2. ⬜ 认证鉴权模块
3. ⬜ Redis 缓存集成
4. ⬜ 完善其他文档分类的提示词
5. ⬜ 错误处理与重试机制
6. ⬜ 单元测试

### Phase 3: 用户体验 (第7-8周)

1. ⬜ 简单Web界面 (Streamlit)
2. ⬜ 数据导出功能 (JSON/Excel)
3. ⬜ 日志记录与监控
4. ⬜ 性能优化

---

## 六、关键设计决策

### 6.1 为什么简化前端?

**原因**:
- 项目初期重点是验证 AI 模型效果
- 前端开发成本高,迭代慢
- API 测试工具 + 简单Web界面足以满足需求

**方案**:
- 使用 Postman/Apifox 进行 API 测试
- 使用 Streamlit 快速搭建简单Web界面

### 6.2 为什么不使用向量数据库?

**原因**:
- 初期文档分类使用 LLM 零样本,不需要向量检索
- Embedding 缓存使用本地文件即可
- 降低系统复杂度和运维成本

**未来扩展**:
- 积累足够文档后,再引入向量库做语义搜索和相似文档推荐

### 6.3 为什么使用单一 LLM 服务?

**原因**:
- 通义千问 API 支持多种模型,统一调用接口
- 降低代码复杂度
- 易于切换不同模型

**配置**:
- 分类: qwen2.5-14b-instruct
- 抽取: qwen2.5-72b-instruct
- 井号: qwen2.5-7b-instruct

---

## 七、技术债务与风险

### 7.1 已知限制

1. **OCR 准确率**: 手写文档识别准确率较低 (~85%)
2. **LLM 幻觉**: 可能提取错误的字段值
3. **并发性能**: 单线程处理,批量处理慢
4. **错误恢复**: 异常处理不够完善

### 7.2 迭代计划

**短期 (1-2个月)**:
- 提升提示词质量
- 完善校验规则
- 优化错误处理

**中期 (3-6个月)**:
- 引入 Fine-tuning 模型
- 实现并发处理
- 添加人工审核界面

**长期 (6个月+)**:
- 引入向量数据库
- 实现模型微调
- 开发完整前端

---

## 八、快速开始

### 8.1 环境准备

```bash
# 克隆项目
git clone <repo_url>
cd well-info-extraction

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env, 填写 LLM_API_KEY 等

# 初始化数据库
alembic upgrade head
```

### 8.2 启动服务

```bash
# 开发环境
uvicorn api.main:app --reload --port 8000

# 或使用 Docker
docker-compose up -d
```

### 8.3 测试接口

```bash
# 健康检查
curl http://localhost:8000/api/v1/health

# 单文档提取
curl -X POST http://localhost:8000/api/v1/extract/single \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/document.pdf"
```

---

## 九、附录

### 9.1 环境变量

```bash
# .env.example
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DATABASE_URL=postgresql://wellinfo:wellinfo123@localhost:5432/wellinfo
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your_secret_key_here
DEBUG=false
```

### 9.2 依赖说明

| 依赖 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.104.1 | Web 框架 |
| SQLAlchemy | 2.0.23 | ORM |
| OpenAI | 1.3.5 | LLM SDK |
| PaddleOCR | 2.7.0.3 | OCR 引擎 |
| PyMuPDF | 1.23.8 | PDF 解析 |

---

**文档结束**
