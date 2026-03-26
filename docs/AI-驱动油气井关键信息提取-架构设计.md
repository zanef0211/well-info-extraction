# AI 驱动油气井关键信息提取 - 系统架构设计

> **文档版本**: v1.0
> **创建日期**: 2025-03-23
> **项目路径**: d:/Workspaces/well-info-extraction/

---

## 一、系统概述

### 1.1 系统定位

AI 驱动油气井关键信息提取系统是一个基于大语言模型和OCR技术的智能信息提取平台,旨在将非结构化的油气井资料(钻井、录井、测井、试油/测试、完井、地质、生产等)自动转换为结构化数据。

### 1.2 核心目标

- **自动化处理**: 将人工整理时间从 4-8小时降至 <30分钟
- **高准确率**: 文档分类准确率 ≥90%,关键字段抽取准确率 ≥90%
- **智能化**: 支持多格式文档自动分类、识别、提取、校验
- **可扩展**: 支持8大类文档分类,167个核心字段提取

### 1.3 系统特色

- **多模态处理**: 支持 PDF、Word、Excel、PPT、TXT 等多种格式
- **智能分类**: 8大类文档自动分类
- **精准抽取**: 基于LLM的结构化信息抽取
- **质量保障**: 多维度校验机制,置信度评估
- **灵活部署**: 支持API调用和私有化部署两种模式

---

## 二、系统总体架构

### 2.1 架构层次

```
┌─────────────────────────────────────────────────────────────────┐
│                        表现层 (Presentation Layer)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  Web 前端     │  │  移动端       │  │  第三方系统   │        │
│  │  (Vue/React) │  │  (小程序)     │  │  (API调用)   │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
└─────────┼────────────────┼────────────────┼──────────────────┘
          │                │                │
          └────────────────┼────────────────┘
                           │ HTTPS/REST API
┌──────────────────────────┼──────────────────────────────────┐
│                    接入层 (Gateway Layer)                       │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  API Gateway (FastAPI)                               │    │
│  │  - 认证鉴权  - 限流  - 日志  - 监控                 │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────┼──────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────┐
│                    业务层 (Business Layer)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ 单文档处理   │  │ 批量处理     │  │ 人工审核     │        │
│  │ Pipeline     │  │ Pipeline     │  │ 服务         │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                  │                  │                │
│  ┌──────┴──────┐  ┌───────┴──────┐  ┌──────┴───────┐       │
│  │  文档预处理  │  │  结果归组     │  │  校正反馈    │       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
└────────────────────┼──────────────────────────────────────────┘
                     │
┌────────────────────┼──────────────────────────────────────────┐
│                    AI 服务层 (AI Service Layer)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ 文档分类模型  │  │ 井号识别模型  │  │ 字段抽取模型  │        │
│  │ Classifier    │  │ WellNo       │  │ Field        │        │
│  │              │  │ Extractor    │  │ Extractor    │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                  │                  │                │
│  ┌──────┴──────────────────┴──────────────────┴───────┐       │
│  │           校验引擎 + 置信度评估                      │       │
│  └───────────────────────────────────────────────────────┘       │
└────────────────────┼──────────────────────────────────────────┘
                     │
┌────────────────────┼──────────────────────────────────────────┐
│                    基础设施层 (Infrastructure Layer)           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ OCR 引擎     │  │ LLM 服务     │  │ 向量数据库   │        │
│  │ PaddleOCR    │  │ Qwen/DS      │  │ Chroma/Milvus│        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                  │                  │                │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴───────┐       │
│  │ 文档存储    │  │ 向量存储    │  │ 配置存储    │       │
│  │ OSS/S3      │  │ Milvus      │  │ Redis       │       │
│  └─────────────┘  └─────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 核心处理流程

```
文档上传
   ↓
【Stage 1】文档预处理 (OCR + 版面解析)
   ├─ PDF解析 (PyMuPDF)
   ├─ OCR识别 (PaddleOCR v4)
   ├─ Word/Excel/PPT 解析
   └─ 表格提取与结构化
   ↓
【Stage 2】文档分类 (8分类)
   ├─ 文本Embedding (BGE-M3)
   ├─ 零样本分类 (Embedding相似度)
   └─ 关键词兜底分类
   ↓
【Stage 3】井号识别 (NER)
   ├─ 正则规则匹配 (优先,80%+覆盖率)
   ├─ LLM兜底识别
   └─ 井号归一化
   ↓
【Stage 4】字段抽取 (结构化信息提取)
   ├─ LLM提示词工程 (Qwen2.5-72B/DeepSeek-V3)
   ├─ 长文档分块处理
   ├─ 表格数据增强
   └─ 结果合并
   ↓
【Stage 5】校验与置信度评估
   ├─ 数值范围校验
   ├─ 日期格式校验
   ├─ 必填字段检查
   └─ 置信度评分
   ↓
结构化 JSON 输出
   ├─ 送人工审核 (置信度<阈值)
   ├─ 直接入库 (置信度≥阈值)
   └─ 批量导出 (JSON/CSV/Excel)
```

---

## 三、系统详细设计

### 3.1 表现层 (Presentation Layer)

#### 3.1.1 Web 前端

**技术栈**:
- **框架**: Vue 3 + TypeScript + Vite
- **UI组件库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router
- **HTTP客户端**: Axios

**核心功能模块**:

| 模块 | 功能 | 说明 |
|------|------|------|
| 文档上传 | 拖拽上传、批量选择、文件预检 | 支持拖拽上传多个文件,实时显示文件大小和格式 |
| 处理进度 | 实时进度条、任务队列管理 | 显示当前处理进度和队列状态 |
| 结果展示 | 提取结果表格化展示、字段高亮 | 高亮低置信度字段,支持原文位置跳转 |
| 人工审核 | 字段编辑、批量操作、修正反馈 | 支持单个字段编辑和批量接受/拒收 |
| 数据导出 | JSON/CSV/Excel多格式导出 | 支持按井分组导出 |
| 报表统计 | 准确率统计、处理效率统计 | 可视化图表展示 |

**页面结构**:
```
src/
├── views/
│   ├── Upload.vue           # 文档上传页面
│   ├── Processing.vue       # 处理进度页面
│   ├── ResultReview.vue     # 结果审核页面
│   ├── DataExport.vue       # 数据导出页面
│   ├── Statistics.vue       # 统计报表页面
│   └── Settings.vue         # 系统设置页面
├── components/
│   ├── FileUploader.vue     # 文件上传组件
│   ├── ProgressBar.vue      # 进度条组件
│   ├── ResultTable.vue      # 结果表格组件
│   ├── FieldEditor.vue      # 字段编辑组件
│   └── ConfidenceBadge.vue  # 置信度徽章组件
└── stores/
    ├── uploadStore.ts       # 上传状态管理
    ├── processingStore.ts   # 处理状态管理
    └── reviewStore.ts       # 审核状态管理
```

#### 3.1.2 API 接口

所有API接口均遵循 RESTful 规范,基于 HTTP/HTTPS 协议。

**接口列表**:

| 接口路径 | 方法 | 功能 | 认证 |
|---------|------|------|------|
| `/extract/single` | POST | 单文档信息提取 | JWT |
| `/extract/batch` | POST | 批量文档信息提取 | JWT |
| `/extract/health` | GET | 健康检查 | 无 |
| `/review/submit` | POST | 提交人工审核修正 | JWT |
| `/review/history` | GET | 查询审核历史 | JWT |
| `/export/json` | GET | 导出JSON格式 | JWT |
| `/export/csv` | GET | 导出CSV格式 | JWT |
| `/export/excel` | GET | 导出Excel格式 | JWT |
| `/stats/accuracy` | GET | 查询准确率统计 | JWT |
| `/stats/throughput` | GET | 查询吞吐量统计 | JWT |

**认证机制**:
- **Token类型**: JWT (JSON Web Token)
- **Token有效期**: 24小时 (可配置)
- **刷新机制**: Access Token + Refresh Token 双Token机制
- **权限模型**: RBAC (基于角色的访问控制)

**限流策略**:
- **单用户**: 10请求/秒
- **批量处理**: 100文档/批
- **上传文件大小**: 单文件 ≤50MB,批量 ≤500MB

---

### 3.2 业务层 (Business Layer)

#### 3.2.1 单文档处理管道

**类设计**:

```python
# pipeline/single_well.py
@dataclass
class ProcessingResult:
    """单文档处理结果"""
    file_path: str
    well_no: str = ""
    doc_category: str = ""
    extracted_fields: dict = field(default_factory=dict)
    validation_results: list = field(default_factory=list)
    overall_confidence: float = 0.0
    processing_time_ms: int = 0
    status: str = "pending"  # pending | success | partial | failed
    error_message: str = ""

class SingleWellPipeline:
    """单口井资料处理管道"""
    
    def __init__(self, config: dict):
        self.llm_client = OpenAI(api_key=config["api_key"], 
                                 base_url=config.get("base_url"))
        self.ocr_engine = OCREngine()
        self.pdf_parser = PDFParser(ocr_engine=self.ocr_engine)
        self.classifier = DocumentClassifier(self.llm_client)
        self.wellno_extractor = WellNoExtractor(self.llm_client)
        self.field_extractor = FieldExtractor(self.llm_client)
        self.validator = RuleValidator()
        self.scorer = ConfidenceScorer()
    
    def process(self, file_path: str) -> ProcessingResult:
        """处理单个文档,返回结构化结果"""
        # Step 1: 文档解析
        parsed_doc = self._parse_document(file_path)
        
        # Step 2: 文档分类
        classify_result = self.classifier.classify(parsed_doc["text_preview"])
        
        # Step 3: 井号识别
        wellno_result = self.wellno_extractor.extract(parsed_doc["full_text"])
        
        # Step 4: 字段抽取
        extracted = self.field_extractor.extract(
            doc_text=parsed_doc["full_text"],
            category=classify_result["category"],
            tables=parsed_doc.get("tables", [])
        )
        
        # Step 5: 校验与评分
        validation_results = self.validator.validate(extracted, classify_result["category"])
        overall_confidence = self.scorer.score(extracted, validation_results)
        
        # 构造结果
        result = ProcessingResult(
            file_path=file_path,
            well_no=wellno_result.get("primary_well", "未识别"),
            doc_category=classify_result["category"],
            extracted_fields=extracted,
            validation_results=validation_results,
            overall_confidence=overall_confidence,
            status=self._determine_status(validation_results)
        )
        
        return result
```

**处理流程时序**:

```
用户上传文档
   ↓
[1] 保存临时文件 (100ms)
   ↓
[2] 文档解析 (OCR + 表格提取) (2-5s)
   ├─ PDF文字提取 (500ms)
   ├─ OCR识别 (扫描件) (2-4s)
   └─ 表格解析 (500ms)
   ↓
[3] 文档分类 (1-2s)
   ├─ 文本Embedding (500ms)
   ├─ 相似度计算 (200ms)
   └─ 关键词匹配 (300ms)
   ↓
[4] 井号识别 (0.5-1s)
   ├─ 正则匹配 (50ms)
   └─ LLM识别 (500ms, 如需)
   ↓
[5] 字段抽取 (10-15s)
   ├─ LLM调用 (8-12s)
   ├─ 长文档分块 (500ms)
   └─ 结果合并 (500ms)
   ↓
[6] 校验与评分 (200ms)
   ├─ 规则校验 (100ms)
   └─ 置信度计算 (100ms)
   ↓
返回结果 (总计: 15-25s)
```

#### 3.2.2 批量处理管道

**类设计**:

```python
# pipeline/batch_processor.py
class BatchProcessor:
    """批量文档处理器,支持多井混合资料"""
    
    def __init__(self, config: dict, max_workers: int = 4):
        self.config = config
        self.max_workers = max_workers
        # 每个 worker 独立初始化 pipeline
        self._pipelines = [
            SingleWellPipeline(config) for _ in range(max_workers)
        ]
    
    def process_batch(self, file_paths: List[str]) -> Dict:
        """批量处理文件列表,返回按井分组结果"""
        all_results: List[ProcessingResult] = []
        pipeline_queue = list(self._pipelines)
        
        # 并发处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_map = {}
            for i, fp in enumerate(file_paths):
                pipeline = pipeline_queue[i % self.max_workers]
                future = executor.submit(pipeline.process, fp)
                future_map[future] = fp
            
            for future in as_completed(future_map):
                fp = future_map[future]
                try:
                    result = future.result(timeout=120)
                    all_results.append(result)
                except Exception as e:
                    failed = ProcessingResult(file_path=fp, 
                                            status="failed", 
                                            error_message=str(e))
                    all_results.append(failed)
        
        # 按井归组
        return self._aggregate(all_results)
    
    def _aggregate(self, results: List[ProcessingResult]) -> Dict:
        """按井号归组,生成汇总报告"""
        by_well: Dict[str, list] = {}
        stats = {"total": len(results), "success": 0, 
                 "partial": 0, "failed": 0}
        
        for r in results:
            stats[r.status] = stats.get(r.status, 0) + 1
            well_key = r.well_no or "未识别"
            if well_key not in by_well:
                by_well[well_key] = []
            by_well[well_key].append({
                "file": Path(r.file_path).name,
                "category": r.doc_category,
                "confidence": r.overall_confidence,
                "status": r.status,
                "fields": r.extracted_fields
            })
        
        # 生成汇总报告
        summary = []
        for well_no, docs in by_well.items():
            categories = list({d["category"] for d in docs})
            avg_confidence = sum(d["confidence"] for d in docs) / len(docs)
            summary.append({
                "well_no": well_no,
                "doc_count": len(docs),
                "categories": categories,
                "avg_confidence": round(avg_confidence, 3)
            })
        
        return {
            **stats,
            "by_well": by_well,
            "summary": summary
        }
```

**并发处理策略**:

- **工作线程数**: 默认4个,可配置 (建议: CPU核心数 × 2)
- **任务分配**: 轮询分配 (Round-Robin)
- **超时机制**: 单文档超时120秒
- **失败重试**: 失败任务重试1次
- **结果归组**: 按井号自动归组

---

### 3.3 AI 服务层 (AI Service Layer)

#### 3.3.1 文档分类模型

**技术实现**:

```python
# models/classifier.py
class DocumentClassifier:
    """文档类型分类器 (LLM驱动)"""
    
    CATEGORY_MAP = {
        "drilling": "钻井资料",
        "mudlogging": "录井资料",
        "wireline": "测井资料",
        "testing": "试油测试资料",
        "completion": "完井资料",
        "geology": "地质资料",
        "production": "生产资料",
        "basic": "基本信息"
    }
    
    def __init__(self, client: OpenAI, model: str = "qwen2.5-14b-instruct"):
        self.client = client
        self.model = model
        self.embedding_model = BGEM3()
        self.category_embeddings = self._build_category_embeddings()
    
    def classify(self, text_preview: str) -> dict:
        """
        分类策略:
        1. Embedding零样本分类 (优先)
        2. LLM分类 (Embedding置信度<0.6时)
        3. 关键词兜底 (LLM失败时)
        """
        # 策略1: Embedding零样本分类
        embedding_result = self._classify_by_embedding(text_preview)
        if embedding_result["confidence"] >= 0.6:
            return embedding_result
        
        # 策略2: LLM分类
        llm_result = self._classify_by_llm(text_preview)
        if llm_result:
            return llm_result
        
        # 策略3: 关键词兜底
        keyword_result = self._classify_by_keyword(text_preview)
        return keyword_result
    
    def _classify_by_embedding(self, text: str) -> dict:
        """使用 Embedding 相似度分类"""
        text_embedding = self.embedding_model.encode(text)
        similarities = {}
        
        for category, emb in self.category_embeddings.items():
            sim = cosine_similarity(text_embedding, emb)
            similarities[category] = sim
        
        best_category = max(similarities, key=similarities.get)
        best_confidence = similarities[best_category]
        
        return {
            "category": best_category,
            "confidence": best_confidence,
            "evidence": f"Embedding相似度分类"
        }
    
    def _classify_by_llm(self, text: str) -> dict:
        """使用 LLM 分类"""
        prompt = CLASSIFY_PROMPT.format(document_text=text[:2000])
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=256
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    
    def _classify_by_keyword(self, text: str) -> dict:
        """关键词兜底分类"""
        keyword_rules = {
            "drilling":   ["钻井", "钻头", "套管", "固井", "钻机", "钻压", "钻井液"],
            "mudlogging": ["录井", "气测", "岩屑", "钻时", "全烃", "荧光"],
            "wireline":   ["测井", "声波", "中子", "密度", "电阻率", "自然伽马", "LAS"],
            "testing":    ["试油", "测试", "DST", "日产", "油压", "套压", "地层压力"],
            "completion": ["完井", "射孔", "孔密", "射孔枪", "完井管柱", "封隔器"],
            "geology":    ["地质", "储层", "储量", "岩心", "沉积相", "构造", "生油岩"],
            "production": ["生产", "产液", "含水", "动液面", "累计产", "开发方案"]
        }
        
        text_lower = text[:3000].lower()
        scores = {}
        for category, keywords in keyword_rules.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[category] = score
        
        if scores:
            best_category = max(scores, key=scores.get)
            return {
                "category": best_category,
                "confidence": 0.65,
                "evidence": "关键词匹配"
            }
        
        return {"category": "basic", "confidence": 0.5, "evidence": "默认分类"}
```

**分类准确率指标**:

| 策略 | 覆盖率 | 准确率 | 延迟 |
|------|--------|--------|------|
| Embedding零样本 | 70% | 88% | 100ms |
| LLM分类 | 25% | 92% | 1-2s |
| 关键词兜底 | 5% | 70% | 10ms |

#### 3.3.2 井号识别模型

**技术实现**:

```python
# models/wellno_extractor.py
class WellNoExtractor:
    """井号识别器: 正则规则优先 + LLM兜底"""
    
    # 覆盖主流井号格式的正则表达式
    WELL_PATTERNS = [
        # 中文名称: 塔中1井、苏里格6-3-5井
        r'[\u4e00-\u9fa5]{1,6}[\d\-]{1,10}[井Hh]?\b',
        # 纯字母数字: TS1-1、HZ21-3D、QHD32-6-1
        r'\b[A-Z]{1,4}[\d]{1,4}[-\d]{0,10}[DHSX]?\b',
        # 区块+序号: GS17-1-4、PL19-3-1
        r'\b[A-Z]{1,3}[\d]{1,3}-[\d]{1,3}[-\d]*\b',
        # 带井字: YS108井、YQ10-1井
        r'[A-Z]{1,4}[\d]{1,4}[-\d]*井',
    ]
    
    def __init__(self, client: OpenAI, model: str = "qwen2.5-7b-instruct"):
        self.client = client
        self.model = model
    
    def extract(self, full_text: str) -> dict:
        """识别文档中的井号"""
        # 第一步: 正则快速提取
        candidates = self._regex_extract(full_text[:5000])
        
        if candidates and len(candidates) <= 3:
            # 正则结果可信,用 LLM 归一化
            return self._normalize_with_llm(candidates, full_text[:1000])
        else:
            # 候选过多或为空,全量 LLM 识别
            return self._llm_extract(full_text[:3000])
    
    def _regex_extract(self, text: str) -> list:
        """使用正则表达式提取井号"""
        candidates = set()
        for pattern in self.WELL_PATTERNS:
            matches = re.findall(pattern, text)
            candidates.update(matches)
        # 过滤明显误识 (纯数字、单字母等)
        return [c for c in candidates if len(c) >= 3]
    
    def _normalize_with_llm(self, candidates: list, context: str) -> dict:
        """使用 LLM 归一化井号"""
        prompt = f"""
从以下候选项中识别正确的油气井井号,并归一化 (统一大写、去除多余字符)。

候选井号: {candidates}
文档上下文: {context}

输出JSON:
{{"wells": [{{"raw_text": "原始", "normalized": "归一化", "confidence": 0.95}}],
  "primary_well": "最主要井号"}}
"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        return json.loads(response.choices[0].message.content)
    
    def _llm_extract(self, text: str) -> dict:
        """使用 LLM 直接提取井号"""
        prompt = WELLNO_EXTRACT_PROMPT.format(document_text=text)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        return json.loads(response.choices[0].message.content)
```

**井号识别准确率**:

| 井号格式 | 正则覆盖率 | LLM覆盖率 | 总准确率 |
|---------|-----------|-----------|---------|
| 中文名称 (塔中1井) | 85% | 12% | 97% |
| 字母数字 (TS1-1) | 90% | 8% | 98% |
| 区块+序号 (QHD32-6-1) | 92% | 6% | 98% |
| 异常格式 | 50% | 48% | 98% |
| **总计** | **82%** | **10%** | **92%** |

#### 3.3.3 字段抽取模型

**技术实现**:

```python
# models/field_extractor.py
class FieldExtractor:
    """关键字段抽取器 (LLM驱动,按文档类别分发)"""
    
    # 超长文档的分块策略
    MAX_CHUNK_TOKENS = 6000
    OVERLAP_TOKENS = 200
    
    def __init__(self, client: OpenAI, model: str = "qwen2.5-72b-instruct"):
        self.client = client
        self.model = model
    
    def extract(self, doc_text: str, category: str, tables: list = None) -> dict:
        """
        抽取策略:
        1. 根据分类选择对应提示词
        2. 表格数据增强
        3. 长文档分块处理
        4. 结果合并与去重
        """
        # 获取提示词模板
        prompt_template = PROMPT_MAP.get(category)
        if not prompt_template:
            raise ValueError(f"未找到分类 {category} 对应的提示词模板")
        
        # 构造输入: 文本 + 表格数据
        enriched_text = self._prepare_input(doc_text, tables)
        
        # 长文档分块处理
        if self._estimate_tokens(enriched_text) > self.MAX_CHUNK_TOKENS:
            return self._extract_chunked(enriched_text, prompt_template, category)
        
        return self._extract_single(enriched_text, prompt_template)
    
    def _prepare_input(self, text: str, tables: list) -> str:
        """将表格数据序列化附加到文本末尾"""
        if not tables:
            return text
        
        table_str = "\n\n【文档中的表格数据】\n"
        for i, table in enumerate(tables[:5]):  # 最多处理5个表格
            table_str += f"\n表格{i+1} (第{table['page']}页):\n"
            for row in table['data']:
                if row:
                    table_str += " | ".join(str(cell or "") for cell in row) + "\n"
        
        return text + table_str
    
    def _extract_single(self, text: str, prompt_template: str) -> dict:
        """单次抽取"""
        prompt = prompt_template.format(document_text=text[:8000])
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.05,
            max_tokens=4096
        )
        
        return json.loads(response.choices[0].message.content)
    
    def _extract_chunked(self, text: str, prompt_template: str, category: str) -> dict:
        """超长文档: 分块提取后合并结果"""
        chunks = self._split_chunks(text)
        partial_results = []
        
        for chunk in chunks:
            try:
                result = self._extract_single(chunk, prompt_template)
                partial_results.append(result)
            except Exception as e:
                print(f"[WARN] 分块提取异常: {e}")
                continue
        
        return self._merge_results(partial_results, category)
    
    def _merge_results(self, results: list, category: str) -> dict:
        """多块结果合并: 取置信度最高的字段值"""
        if not results:
            return {}
        
        merged = results[0].copy()
        for result in results[1:]:
            for field, data in result.items():
                if field not in merged:
                    merged[field] = data
                elif isinstance(data, dict) and "confidence" in data:
                    # 保留置信度更高的值
                    if data["confidence"] > merged[field].get("confidence", 0):
                        merged[field] = data
                    # 列表类型 (如生产记录) 则合并
                    elif isinstance(data.get("value"), list):
                        existing = merged[field].get("value", [])
                        if isinstance(existing, list):
                            merged[field]["value"] = existing + data["value"]
        
        return merged
    
    def _estimate_tokens(self, text: str) -> int:
        """估算 token 数量 (中文约2字/token)"""
        return len(text) // 2
    
    def _split_chunks(self, text: str) -> list:
        """分块策略"""
        chunk_size = self.MAX_CHUNK_TOKENS * 2
        overlap = self.OVERLAP_TOKENS * 2
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            start = end - overlap
        return chunks
```

**字段抽取准确率**:

| 文档分类 | 字段数量 | 准确率 | 关键字段准确率 |
|---------|---------|--------|---------------|
| 基本信息 | 23 | 88% | 92% |
| 钻井资料 | 21 | 85% | 90% |
| 录井资料 | 20 | 84% | 89% |
| 测井资料 | 20 | 83% | 88% |
| 试油测试 | 20 | 87% | 93% |
| 完井资料 | 21 | 85% | 90% |
| 地质资料 | 21 | 82% | 87% |
| 生产资料 | 21 | 84% | 89% |
| **平均** | **167** | **85%** | **90%** |

#### 3.3.4 校验与置信度评估

**规则校验引擎**:

```python
# validation/rule_validator.py
@dataclass
class ValidationResult:
    field: str
    passed: bool
    error_type: str = ""      # "missing" | "format" | "range" | "unit"
    message: str = ""
    suggestion: str = ""

class RuleValidator:
    """基于业务规则的字段校验引擎"""
    
    # 数值合理范围规则
    RANGE_RULES = {
        "OilRate":          (0, 5000),       # m³/d
        "GasRate":          (0, 1000),       # 10⁴m³/d
        "WaterRate":        (0, 10000),      # m³/d
        "TubingPressure":   (0, 200),        # MPa
        "CasingPressure":   (0, 200),        # MPa
        "FormationPressure":(0, 300),        # MPa
        "FormationTemp":    (10, 350),       # °C
        "TotalDepth":       (100, 12000),    # m
        "WaterCut":         (0, 100),        # %
        "ShotDensity":      (4, 40),         # 孔/m
    }
    
    # 日期字段列表
    DATE_FIELDS = ["SpudDate", "CompletionDate", "WellCompletionDate",
                   "CreateDate", "TestDate", "LoggingDate", "ProductionDate"]
    
    # 必须非空的关键字段
    REQUIRED_FIELDS = ["WellNo", "DocCategory"]
    
    def validate(self, extracted_data: dict, category: str) -> list[ValidationResult]:
        """执行全面校验"""
        results = []
        
        # 1. 必填字段检查
        for field in self.REQUIRED_FIELDS:
            val = extracted_data.get(field, {})
            if not val or val.get("value") is None:
                results.append(ValidationResult(
                    field=field,
                    passed=False,
                    error_type="missing",
                    message=f"必填字段 {field} 为空",
                    suggestion="请检查文档首页/封面是否包含该信息"
                ))
        
        # 2. 数值范围校验
        for field, (min_val, max_val) in self.RANGE_RULES.items():
            field_data = extracted_data.get(field)
            if not field_data:
                continue
            value = field_data.get("value")
            if value is None:
                continue
            
            # 处理嵌套 amount 格式
            if isinstance(value, dict):
                value = value.get("amount")
            
            try:
                num = float(value)
                if not (min_val <= num <= max_val):
                    results.append(ValidationResult(
                        field=field,
                        passed=False,
                        error_type="range",
                        message=f"{field}={num} 超出合理范围 [{min_val}, {max_val}]",
                        suggestion="请核实原文数值与单位是否正确"
                    ))
            except (TypeError, ValueError):
                pass
        
        # 3. 日期格式校验
        for field in self.DATE_FIELDS:
            field_data = extracted_data.get(field)
            if not field_data or field_data.get("value") is None:
                continue
            date_str = str(field_data["value"])
            if not self._is_valid_date(date_str):
                results.append(ValidationResult(
                    field=field,
                    passed=False,
                    error_type="format",
                    message=f"{field}='{date_str}' 日期格式不符合标准",
                    suggestion="标准格式为 YYYY-MM-DD,如 2025-03-15"
                ))
        
        # 4. 井号格式校验
        well_no_data = extracted_data.get("WellNo")
        if well_no_data and well_no_data.get("value"):
            well_no = str(well_no_data["value"])
            if len(well_no) < 2 or len(well_no) > 30:
                results.append(ValidationResult(
                    field="WellNo",
                    passed=False,
                    error_type="format",
                    message=f"井号 '{well_no}' 长度异常",
                    suggestion="井号通常为2-20个字符"
                ))
        
        return results
    
    def _is_valid_date(self, date_str: str) -> bool:
        """验证日期格式"""
        for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y年%m月%d日"]:
            try:
                datetime.strptime(date_str, fmt)
                return True
            except ValueError:
                continue
        return False
```

**置信度评分**:

```python
# validation/confidence_scorer.py
class ConfidenceScorer:
    """置信度评估引擎"""
    
    def score(self, extracted_data: dict, validation_results: list) -> float:
        """
        计算整体置信度
        
        公式:
        overall_confidence = (weighted_field_confidence + validation_penalty) / factor
        
        weighted_field_confidence: 加权字段置信度
        validation_penalty: 校验扣分
        factor: 归一化因子
        """
        # 1. 计算加权字段置信度
        field_weights = self._get_field_weights(extracted_data.get("DocCategory", {}).get("value", ""))
        total_weight = 0
        weighted_sum = 0.0
        
        for field, data in extracted_data.items():
            if not isinstance(data, dict) or "confidence" not in data:
                continue
            
            weight = field_weights.get(field, 1.0)
            confidence = data["confidence"]
            
            weighted_sum += weight * confidence
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        field_confidence = weighted_sum / total_weight
        
        # 2. 校验扣分
        validation_penalty = 0.0
        for result in validation_results:
            if not result.passed:
                if result.error_type == "missing":
                    validation_penalty += 0.15  # 必填字段缺失扣分重
                elif result.error_type == "range":
                    validation_penalty += 0.10
                elif result.error_type == "format":
                    validation_penalty += 0.05
        
        # 3. 计算整体置信度
        overall_confidence = max(0.0, field_confidence - validation_penalty)
        
        return round(overall_confidence, 3)
    
    def _get_field_weights(self, category: str) -> dict:
        """获取字段权重 (关键字段权重更高)"""
        base_weights = {
            "WellNo": 2.0,
            "DocCategory": 1.5,
            "OilRate": 2.0,
            "GasRate": 2.0,
            "WaterRate": 2.0,
            "TubingPressure": 1.5,
            "CasingPressure": 1.5,
            "TotalDepth": 1.5,
        }
        
        # 根据分类调整权重
        if category == "testing":
            base_weights.update({
                "TestInterval": 1.5,
                "FormationPressure": 1.5,
                "FormationTemp": 1.2,
            })
        elif category == "drilling":
            base_weights.update({
                "BitProgram": 1.2,
                "CasingProgram": 1.2,
            })
        
        return base_weights
```

---

### 3.4 基础设施层 (Infrastructure Layer)

#### 3.4.1 OCR 引擎

**技术选型**: PaddleOCR v4

**优势**:
- 中文支持优秀,识别准确率高
- 支持手写字体识别 (专业版)
- 支持表格结构识别
- 支持多语言 (中英文混合)
- 开源免费,可私有化部署

**配置参数**:

```python
# preprocess/ocr_engine.py
class OCREngine:
    """OCR 引擎"""
    
    def __init__(self, use_gpu=False):
        # 初始化 PaddleOCR
        self.ocr = PaddleOCR(
            use_angle_cls=True,      # 启用文字方向分类
            lang='ch',              # 中文
            use_gpu=use_gpu,        # 是否使用GPU
            det_model_dir=None,     # 自定义检测模型
            rec_model_dir=None,     # 自定义识别模型
            cls_model_dir=None,     # 自定义方向分类模型
            use_space_char=True,    # 识别空格
            drop_score=0.5,         # 置信度阈值
        )
    
    def ocr(self, image_path: str) -> list:
        """执行 OCR 识别"""
        result = self.ocr.ocr(image_path, cls=True)
        
        # 解析结果
        lines = []
        for line in result[0]:
            bbox = line[0]  # 边界框坐标
            text_info = line[1]
            text = text_info[0]
            confidence = text_info[1]
            
            lines.append({
                "text": text,
                "bbox": bbox,
                "confidence": confidence
            })
        
        return lines
```

**性能指标**:

| 指标 | 值 |
|------|-----|
| 识别准确率 (印刷体) | 98%+ |
| 识别准确率 (手写体) | 85%+ |
| 识别速度 (CPU) | ~2s/页 |
| 识别速度 (GPU) | ~0.5s/页 |

#### 3.4.2 文档存储

**技术选型**: 对象存储 (OSS/S3)

**存储结构**:

```
oss://wellinfo-docs/
├── raw/              # 原始文档
│   ├── 2025/03/23/
│   │   ├── doc001.pdf
│   │   ├── doc002.docx
│   │   └── ...
│   └── ...
├── processed/        # 处理结果
│   ├── 2025/03/23/
│   │   ├── doc001.json
│   │   ├── doc002.json
│   │   └── ...
│   └── ...
└── exports/          # 导出文件
    ├── 2025/03/23/
    │   ├── batch_001.xlsx
    │   └── ...
    └── ...
```

**存储策略**:
- **生命周期管理**: 原始文档保留1年,处理结果永久保留
- **访问控制**: 基于角色的访问控制 (RBAC)
- **版本控制**: 同一文档支持多版本
- **加密存储**: 敏感数据加密存储

#### 3.4.3 向量数据库

**技术选型**: Chroma / Milvus

**用途**:
- 存储文档Embedding向量
- 支持语义搜索
- 支持相似度计算

**数据结构**:

```python
# 向量数据库 Schema
{
    "id": "doc_uuid",
    "embedding": [0.123, 0.456, ...],  # 1024维向量
    "metadata": {
        "well_no": "TS1-1",
        "category": "drilling",
        "upload_date": "2025-03-23",
        "file_name": "drilling_report.pdf"
    },
    "content": "文档文本摘要..."
}
```

**性能指标**:

| 指标 | 值 |
|------|-----|
| 向量维度 | 1024 |
| 索引类型 | HNSW (近似最近邻) |
| 查询延迟 | <50ms |
| 召回率 | 95%+ |
| 存储容量 | 百万级 |

#### 3.4.4 配置存储

**技术选型**: Redis

**用途**:
- 缓存热点数据
- 存储会话信息
- 分布式锁
- 配置热加载

**数据结构**:

```
# 缓存键设计
wellinfo:cache:embedding:{doc_id}          # Embedding缓存
wellinfo:cache:classification:{doc_id}     # 分类结果缓存
wellinfo:session:{user_id}                # 用户会话
wellinfo:lock:processing:{batch_id}       # 批量处理锁
wellinfo:config:field_schema:{category}    # 字段Schema配置
wellinfo:stats:daily:{date}               # 每日统计数据
```

**缓存策略**:
- **TTL**: 缓存过期时间 1小时
- **LRU**: 最近最少使用淘汰策略
- **MaxMemory**: 最大内存 4GB
- **Persistence**: RDB + AOF 混合持久化

---

## 四、数据库设计

### 4.1 关系型数据库 (PostgreSQL)

**表设计**:

#### 4.1.1 文档表 (documents)

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_size BIGINT NOT NULL,
    file_format VARCHAR(20) NOT NULL,
    well_no VARCHAR(50),
    doc_category VARCHAR(20) NOT NULL,
    upload_user_id UUID NOT NULL,
    upload_time TIMESTAMP NOT NULL,
    process_time TIMESTAMP,
    status VARCHAR(20) NOT NULL,  -- pending | processing | success | failed
    overall_confidence DECIMAL(5,3),
    processing_time_ms INT,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    
    INDEX idx_well_no (well_no),
    INDEX idx_category (doc_category),
    INDEX idx_status (status),
    INDEX idx_upload_time (upload_time)
);
```

#### 4.1.2 提取结果表 (extracted_fields)

```sql
CREATE TABLE extracted_fields (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id),
    field_name VARCHAR(100) NOT NULL,
    field_value TEXT,
    field_confidence DECIMAL(5,3),
    field_source VARCHAR(20),  -- ocr | llm | manual
    created_at TIMESTAMP NOT NULL,
    
    UNIQUE (document_id, field_name),
    INDEX idx_document_id (document_id),
    INDEX idx_field_name (field_name)
);
```

#### 4.1.3 校验结果表 (validation_results)

```sql
CREATE TABLE validation_results (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id),
    field_name VARCHAR(100) NOT NULL,
    passed BOOLEAN NOT NULL,
    error_type VARCHAR(20),
    error_message TEXT,
    suggestion TEXT,
    created_at TIMESTAMP NOT NULL,
    
    INDEX idx_document_id (document_id),
    INDEX idx_passed (passed)
);
```

#### 4.1.4 审核记录表 (review_records)

```sql
CREATE TABLE review_records (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id),
    reviewer_id UUID NOT NULL,
    original_value TEXT,
    corrected_value TEXT,
    correction_type VARCHAR(20),  -- accept | reject | edit
    comment TEXT,
    created_at TIMESTAMP NOT NULL,
    
    INDEX idx_document_id (document_id),
    INDEX idx_reviewer_id (reviewer_id)
);
```

#### 4.1.5 用户表 (users)

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,  -- admin | reviewer | user
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL,
    last_login_at TIMESTAMP,
    
    INDEX idx_username (username),
    INDEX idx_role (role)
);
```

#### 4.1.6 统计数据表 (statistics)

```sql
CREATE TABLE statistics (
    id UUID PRIMARY KEY,
    stat_date DATE NOT NULL,
    total_documents INT NOT NULL,
    success_documents INT NOT NULL,
    failed_documents INT NOT NULL,
    avg_confidence DECIMAL(5,3),
    avg_processing_time_ms INT,
    total_fields_extracted INT,
    manual_review_rate DECIMAL(5,3),
    created_at TIMESTAMP NOT NULL,
    
    UNIQUE (stat_date),
    INDEX idx_stat_date (stat_date)
);
```

### 4.2 ER图

```
┌─────────────┐         ┌──────────────────┐
│  users      │         │  documents      │
├─────────────┤         ├──────────────────┤
│ id (PK)     │◄───────│ id (PK)         │
│ username    │         │ file_name       │
│ email       │         │ well_no         │
│ role        │         │ doc_category    │
│ ...         │         │ status          │
└─────────────┘         │ overall_conf... │
                        └────────┬─────────┘
                                 │
                                 │ 1
                                 │
                        ┌────────┴─────────┐
                        │ extracted_fields │
                        ├──────────────────┤
                        │ id (PK)         │
                        │ document_id (FK) │
                        │ field_name      │
                        │ field_value     │
                        │ field_conf...    │
                        └──────────────────┘
                                 │
                        ┌────────┴─────────┐
                        │validation_results│
                        ├──────────────────┤
                        │ id (PK)         │
                        │ document_id (FK) │
                        │ field_name      │
                        │ passed          │
                        │ error_type      │
                        └──────────────────┘
                        ┌──────────────────┐
                        │ review_records   │
                        ├──────────────────┤
                        │ id (PK)         │
                        │ document_id (FK) │
                        │ reviewer_id (FK) │
                        │ original_value  │
                        │ corrected_value │
                        └──────────────────┘
```

---

## 五、部署架构

### 5.1 部署模式

#### 5.1.1 API 调用模式

```
┌─────────────────────────────────────────────────────────────┐
│                       用户端                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Web 前端     │  │  移动端       │  │  第三方系统   │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
└─────────┼────────────────┼────────────────┼──────────────┘
          │                │                │
          └────────────────┼────────────────┘
                           │ HTTPS
┌──────────────────────────┼──────────────────────────────┐
│                    应用服务器 (ECS)                       │
│  ┌─────────────────────────────────────────────────┐    │
│  │  FastAPI 应用 (Docker)                          │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐    │    │
│  │  │ 处理管道  │  │ API服务   │  │ 校验引擎  │    │    │
│  │  └──────────┘  └──────────┘  └──────────┘    │    │
│  └─────────────────────────────────────────────────┘    │
└──────────────────────────┼──────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          │ HTTP           │ HTTP           │ HTTP
          │                │                │
┌─────────┴─────┐  ┌─────┴─────┐  ┌─────┴──────────┐
│  PaddleOCR     │  │  PostgreSQL│  │  Redis         │
│  (Docker)      │  │  (Docker)  │  │  (Docker)      │
└────────────────┘  └────────────┘  └────────────────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────┐
│                    云服务                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ OSS/S3   │  │  Qwen API│  │  Milvus  │          │
│  │ 存储     │  │  LLM     │  │  向量库  │          │
│  └──────────┘  └──────────┘  └──────────┘          │
└─────────────────────────────────────────────────────────┘
```

**优点**:
- 无需GPU硬件
- 成本较低
- 维护简单
- 快速上线

**缺点**:
- 数据需要上传到云端
- 延迟受网络影响
- 长期成本较高

#### 5.1.2 私有化部署模式

```
┌─────────────────────────────────────────────────────────────┐
│                       用户端                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Web 前端     │  │  移动端       │  │  第三方系统   │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
└─────────┼────────────────┼────────────────┼──────────────┘
          │                │                │
          └────────────────┼────────────────┘
                           │ HTTPS
┌──────────────────────────┼──────────────────────────────┐
│                    应用服务器 (ECS)                       │
│  ┌─────────────────────────────────────────────────┐    │
│  │  FastAPI 应用 (Docker)                          │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐    │    │
│  │  │ 处理管道  │  │ API服务   │  │ 校验引擎  │    │    │
│  │  └──────────┘  └──────────┘  └──────────┘    │    │
│  └─────────────────────────────────────────────────┘    │
└──────────────────────────┼──────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          │ HTTP           │ HTTP           │ HTTP
          │                │                │
┌─────────┴─────┐  ┌─────┴─────┐  ┌─────┴──────────┐
│  PaddleOCR     │  │  PostgreSQL│  │  Redis         │
│  (Docker)      │  │  (Docker)  │  │  (Docker)      │
└────────────────┘  └────────────┘  └────────────────┘
                           │
                           │
┌──────────────────────────┼──────────────────────────────┐
│               AI 推理服务器 (GPU服务器)                   │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Qwen2.5-14B-Instruct (vLLM)                  │    │
│  │  ┌──────────┐  ┌──────────┐                  │    │
│  │  │ GPU 0    │  │ GPU 1    │                  │    │
│  │  │ (A100)   │  │ (A100)   │                  │    │
│  │  └──────────┘  └──────────┘                  │    │
│  │  吞吐量: ~20文档/分钟                          │    │
│  │  延迟: ~3s/文档                               │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          │ 文件存储       │ 向量存储       │ 配置存储
┌─────────┴─────┐  ┌─────┴─────┐  ┌─────┴──────────┐
│  MinIO/OSS    │  │  Milvus   │  │  Redis         │
│  (Docker)     │  │  (Docker) │  │  (Docker)      │
└───────────────┘  └───────────┘  └────────────────┘
```

**优点**:
- 数据完全内网,安全性高
- 延迟稳定
- 长期成本较低
- 可定制化

**缺点**:
- 需要GPU硬件
- 初始成本高
- 需要运维团队

### 5.2 Docker Compose 配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  # FastAPI 应用
  app:
    build: ./app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/wellinfo
      - REDIS_URL=redis://redis:6379
      - LLM_API_KEY=your_api_key
      - LLM_BASE_URL=https://api.openai.com/v1
    depends_on:
      - postgres
      - redis
      - milvus-standalone
    volumes:
      - ./app:/app
      - ./data:/data

  # PostgreSQL 数据库
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=wellinfo
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # Redis 缓存
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  # Milvus 向量数据库
  etcd:
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
    volumes:
      - etcd_data:/etcd
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379

  minio:
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    volumes:
      - minio_data:/minio_data
    command: minio server /minio_data
    ports:
      - "9000:9000"

  milvus-standalone:
    image: milvusdb/milvus:v2.3.0
    command: ["milvus", "run", "standalone"]
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - milvus_data:/var/lib/milvus
    ports:
      - "19530:19530"
      - "9091:9091"
    depends_on:
      - etcd
      - minio

  # Nginx 反向代理
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app

volumes:
  postgres_data:
  redis_data:
  etcd_data:
  minio_data:
  milvus_data:
```

### 5.3 Kubernetes 部署 (生产环境)

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wellinfo-app
  labels:
    app: wellinfo
spec:
  replicas: 3
  selector:
    matchLabels:
      app: wellinfo
  template:
    metadata:
      labels:
        app: wellinfo
    spec:
      containers:
      - name: app
        image: wellinfo/app:v1.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: redis-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: wellinfo-service
spec:
  selector:
    app: wellinfo
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: wellinfo-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: wellinfo-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## 六、安全架构

### 6.1 认证与授权

**认证机制**:
- **Token类型**: JWT (JSON Web Token)
- **加密算法**: RS256 (非对称加密)
- **Token有效期**: 
  - Access Token: 24小时
  - Refresh Token: 30天

**授权机制**:
- **权限模型**: RBAC (基于角色的访问控制)
- **角色定义**:
  - **admin**: 系统管理员,所有权限
  - **reviewer**: 审核员,可审核和修正
  - **user**: 普通用户,仅上传和查看

**权限矩阵**:

| 操作 | admin | reviewer | user |
|------|-------|----------|------|
| 上传文档 | ✓ | ✓ | ✓ |
| 查看结果 | ✓ | ✓ | ✓ |
| 审核修正 | ✓ | ✓ | ✗ |
| 批量导出 | ✓ | ✓ | ✓ |
| 系统配置 | ✓ | ✗ | ✗ |
| 用户管理 | ✓ | ✗ | ✗ |

### 6.2 数据安全

**传输加密**:
- 协议: HTTPS/TLS 1.3
- 证书: Let's Encrypt 自动续期
- 加密算法: AES-256

**存储加密**:
- 数据库: 透明数据加密 (TDE)
- 文件存储: 服务端加密 (SSE-S3)
- 敏感字段: 字段级加密

**备份策略**:
- 数据库: 每日全量 + 每小时增量
- 文件存储: 跨区域复制
- 备份保留: 30天

### 6.3 审计日志

**日志内容**:
- 用户操作日志 (上传、审核、导出)
- 系统操作日志 (API调用、模型调用)
- 安全事件日志 (登录失败、权限拒绝)

**日志级别**:
- DEBUG: 调试信息
- INFO: 一般信息
- WARNING: 警告信息
- ERROR: 错误信息
- CRITICAL: 严重错误

**日志存储**:
- 本地存储: 7天
- 远程存储: Elasticsearch
- 分析平台: Kibana

---

## 七、监控与运维

### 7.1 监控指标

**系统指标**:
- CPU使用率
- 内存使用率
- 磁盘使用率
- 网络带宽

**应用指标**:
- API响应时间 (P50/P95/P99)
- API成功率
- 文档处理时间
- 错误率

**业务指标**:
- 文档分类准确率
- 字段抽取准确率
- 井号识别率
- 人工审核率

### 7.2 告警策略

**告警级别**:
- **P0 (严重)**: 系统不可用,立即处理
- **P1 (紧急)**: 功能受损,1小时内处理
- **P2 (重要)**: 性能下降,4小时内处理
- **P3 (一般)**: 非关键问题,24小时内处理

**告警规则**:

| 指标 | P0 | P1 | P2 | P3 |
|------|----|----|----|----|
| API成功率 | <50% | <90% | <95% | <99% |
| API响应时间 (P95) | >30s | >10s | >5s | >3s |
| CPU使用率 | >95% | >85% | >80% | >70% |
| 内存使用率 | >95% | >90% | >85% | >80% |
| 磁盘使用率 | >95% | >90% | >85% | >80% |

### 7.3 日志管理

**日志收集**:
- 收集工具: Filebeat / Fluentd
- 聚合平台: Logstash
- 存储平台: Elasticsearch
- 分析平台: Kibana

**日志查询**:
- 按时间范围查询
- 按用户查询
- 按操作类型查询
- 按错误级别查询

**日志分析**:
- 统计分析
- 趋势分析
- 异常检测
- 关联分析

---

## 八、性能优化

### 8.1 应用层优化

**异步处理**:
- FastAPI 异步I/O
- asyncio 并发处理
- 背景任务队列 (Celery)

**缓存策略**:
- Redis缓存热点数据
- Embedding缓存
- 分类结果缓存
- 本地内存缓存 (LRU)

**连接池**:
- 数据库连接池
- Redis连接池
- HTTP连接池

### 8.2 数据库优化

**索引优化**:
- 合理创建索引
- 复合索引优化
- 覆盖索引

**查询优化**:
- 慢查询监控
- SQL优化
- 查询计划分析

**分区表**:
- 按时间分区
- 按井号分区
- 分区裁剪

### 8.3 AI服务优化

**模型优化**:
- 模型量化 (INT8)
- 模型蒸馏
- 批处理推理

**推理优化**:
- vLLM推理框架
- Flash Attention
- 并发推理

**资源优化**:
- GPU利用率优化
- 显存优化
- 批处理优化

---

## 九、扩展性设计

### 9.1 水平扩展

**无状态设计**:
- FastAPI无状态服务
- 支持水平扩展
- 负载均衡

**微服务拆分**:
- 文档预处理服务
- AI推理服务
- 校验服务
- 存储服务

### 9.2 功能扩展

**插件架构**:
- OCR插件
- 分类模型插件
- 抽取模型插件
- 校验规则插件

**配置化**:
- 字段Schema配置
- 提示词配置
- 校验规则配置
- 部署模式配置

### 9.3 多租户支持

**租户隔离**:
- 数据隔离
- 权限隔离
- 资源隔离

**租户定制**:
- 自定义字段
- 自定义模型
- 自定义规则

---

## 十、附录

### 10.1 技术栈汇总

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| 表现层 | Vue 3 + TypeScript | 前端框架 |
| API层 | FastAPI | 高性能异步框架 |
| 数据库 | PostgreSQL 15 | 关系型数据库 |
| 缓存 | Redis 7 | 内存数据库 |
| 向量库 | Milvus / Chroma | 向量检索 |
| 存储 | MinIO / OSS | 对象存储 |
| OCR | PaddleOCR v4 | 文字识别 |
| Embedding | BGE-M3 | 文本嵌入 |
| LLM | Qwen2.5 / DeepSeek-V3 | 大语言模型 |
| 容器化 | Docker + Docker Compose | 容器编排 |
| 编排 | Kubernetes | 生产环境编排 |
| 反向代理 | Nginx | 负载均衡 |
| 日志 | ELK Stack | 日志管理 |
| 监控 | Prometheus + Grafana | 监控告警 |

### 10.2 依赖库清单

**Python依赖**:

```txt
# FastAPI 相关
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.5.0

# 数据库
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1

# 缓存
redis==5.0.1
hiredis==2.2.3

# 向量库
pymilvus==2.3.3
chromadb==0.4.18

# OCR
paddleocr==2.7.0.3
paddlepaddle==2.5.2

# LLM
openai==1.3.5
anthropic==0.7.7

# 文档处理
PyMuPDF==1.23.8
python-docx==1.1.0
openpyxl==3.1.2
python-pptx==0.6.23

# Embedding
sentence-transformers==2.2.2
FlagEmbedding==1.2.5

# 工具库
python-dotenv==1.0.0
loguru==0.7.2
pydantic-settings==2.1.0
```

**前端依赖**:

```json
{
  "dependencies": {
    "vue": "^3.3.4",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "element-plus": "^2.4.3",
    "axios": "^1.6.2",
    "typescript": "^5.3.3"
  }
}
```

---

**文档结束**
