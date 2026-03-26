# AI 驱动油气井关键信息提取系统

> 基于 LLM 的结构化信息提取平台

## 项目简介

本项目是一个基于大语言模型的智能信息提取系统,旨在将非结构化的油气井资料自动转换为结构化数据。

### 核心能力

- **多格式支持**: PDF、Word、Excel、TXT
- **智能分类**: 8大类文档自动分类
- **精准抽取**: LLM驱动的结构化信息抽取
- **质量保障**: 规则校验 + 置信度评估
- **API服务**: RESTful API,支持单文档/批量处理

### 支持的文档类型

1. 基本信息 (23个字段)
2. 钻井资料 (21个字段)
3. 录井资料 (20个字段)
4. 测井资料 (20个字段)
5. 试油测试资料 (20个字段)
6. 完井资料 (21个字段)
7. 地质资料 (21个字段)
8. 生产资料 (21个字段)

## 快速开始

### 环境要求

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- 通义千问 API Key (或其他兼容 OpenAI API 的服务)

### 本地开发

```bash
# 1. 克隆项目
git clone <repo_url>
cd well-info-extraction

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件,填写必要的配置

# 5. 初始化数据库
# 首先创建数据库
createdb wellinfo

# 运行迁移
alembic upgrade head

# 6. 启动服务
uvicorn api.main:app --reload --port 8000

# 7. 访问文档
# API文档: http://localhost:8000/docs
# 健康检查: http://localhost:8000/api/v1/health
```

### Docker 部署

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 2. 启动所有服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f app

# 4. 停止服务
docker-compose down
```

## API 使用示例

### 健康检查

```bash
curl http://localhost:8000/api/v1/health
```

### 单文档提取

```bash
curl -X POST http://localhost:8000/api/v1/extract/single \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/document.pdf"
```

### 批量提取

```bash
curl -X POST http://localhost:8000/api/v1/extract/batch \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "files=@/path/to/doc1.pdf" \
  -F "files=@/path/to/doc2.pdf"
```

## 项目结构

```
well-info-extraction/
├── config/                      # 配置模块
│   ├── settings.py              # 全局配置
│   ├── field_schemas.py         # 字段定义
│   └── prompts.py               # 提示词模板
├── preprocess/                  # 文档预处理
│   ├── ocr_engine.py            # OCR 引擎
│   ├── pdf_parser.py            # PDF 解析
│   └── doc_parser.py            # Word/Excel 解析
├── models/                      # AI 模型
│   ├── classifier.py            # 文档分类
│   ├── wellno_extractor.py      # 井号识别
│   └── field_extractor.py       # 字段抽取
├── validation/                  # 校验模块
│   ├── rule_validator.py        # 规则校验
│   └── confidence_scorer.py     # 置信度评估
├── pipeline/                    # 处理管道
│   ├── single_well.py           # 单文档处理
│   └── batch_processor.py       # 批量处理
├── api/                         # API 接口
│   ├── main.py                  # FastAPI 应用
│   ├── routes.py                # 路由定义
│   └── auth.py                  # 认证鉴权
├── db/                          # 数据库
│   ├── models.py                # SQLAlchemy 模型
│   ├── database.py              # 数据库连接
│   └── crud.py                  # CRUD 操作
├── schemas/                     # Pydantic 模型
│   ├── request.py               # 请求模型
│   └── response.py              # 响应模型
├── utils/                       # 工具模块
│   ├── logger.py                # 日志工具
│   └── exceptions.py            # 自定义异常
├── storage/                     # 本地存储
│   ├── uploads/                 # 上传的原始文档
│   ├── processed/               # 处理结果
│   └── cache/                   # 缓存文件
├── tests/                       # 测试模块
├── logs/                        # 日志文件
├── requirements.txt             # Python 依赖
├── .env.example                # 环境变量示例
├── Dockerfile                  # Docker 镜像
├── docker-compose.yml          # Docker Compose
└── README.md                   # 项目说明
```

## 配置说明

### LLM 配置

项目使用通义千问 API,需要配置以下环境变量:

```env
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_CLASSIFY=qwen2.5-14b-instruct
LLM_MODEL_EXTRACT=qwen2.5-72b-instruct
LLM_MODEL_WELLNO=qwen2.5-7b-instruct
```

也可以使用其他兼容 OpenAI API 的服务,只需修改 `LLM_BASE_URL` 和模型名称即可。

### 数据库配置

```env
DATABASE_URL=postgresql://wellinfo:wellinfo123@localhost:5432/wellinfo
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

### 存储配置

```env
STORAGE_PATH=./storage
UPLOAD_DIR=./storage/uploads
PROCESSED_DIR=./storage/processed
CACHE_DIR=./storage/cache
```

## 开发计划

### Phase 1: 核心功能 (第1-4周)

- [x] 项目结构搭建
- [x] 配置模块开发
- [x] 数据库设计与初始化
- [ ] 文档解析模块
- [ ] 文档分类模型
- [ ] 井号识别模型
- [ ] 字段抽取模型
- [ ] 规则校验引擎
- [ ] 单文档处理管道
- [ ] FastAPI 基础接口

### Phase 2: 功能完善 (第5-6周)

- [ ] 批量处理管道
- [ ] 认证鉴权模块
- [ ] Redis 缓存集成
- [ ] 完善其他文档分类的提示词
- [ ] 错误处理与重试机制
- [ ] 单元测试

### Phase 3: 用户体验 (第7-8周)

- [ ] 简单Web界面 (Streamlit)
- [ ] 数据导出功能
- [ ] 日志记录与监控
- [ ] 性能优化

## 文档

- [项目上下文](./PROJECT_CONTEXT.md)
- [架构设计](./docs/AI-驱动油气井关键信息提取-架构设计-最终版.md)
- [需求分析](./docs/AI-驱动油气井关键信息提取-需求分析.md)

## 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| API层 | FastAPI | 高性能异步框架 |
| 数据库 | PostgreSQL 15 | 关系型数据库 |
| 缓存 | Redis 7 | 内存数据库 |
| OCR | PaddleOCR v4 | 文字识别 |
| LLM | Qwen2.5 / DeepSeek-V3 | 大语言模型 |
| 容器化 | Docker + Docker Compose | 容器编排 |

## 许可证

MIT License

## 联系方式

如有问题,请提交 Issue 或联系开发团队。
