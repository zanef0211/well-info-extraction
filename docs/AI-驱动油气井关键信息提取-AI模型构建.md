# AI 模型构建细化方案
## —— 油气井关键信息提取系统

> 对应落地路径第 2 阶段（第 3～6 周），覆盖：模型选择 → 提示词设计 → 代码开发 → 流程组装

---

## 一、模型选择

### 1.1 整体技术路线

```
文档输入
   │
   ▼
【Stage 1】文档预处理          → OCR + 版面解析（非结构化→文本块）
   │
   ▼
【Stage 2】文档分类模型         → 判断文档属于 8 大类中的哪一类
   │
   ▼
【Stage 3】井号识别模型         → 从文档中提取唯一 WellNo
   │
   ▼
【Stage 4】关键字段抽取模型     → 按分类字段库精准提取各字段值
   │
   ▼
【Stage 5】校验与置信度评估     → 规则校验 + 模型置信度打分
   │
   ▼
结构化 JSON 输出（送人工审核 / 入库）
```

---

### 1.2 各阶段模型选型

| 阶段 | 任务 | 推荐模型 | 理由 |
|------|------|----------|------|
| 文档预处理 | PDF/扫描件版面解析+OCR | **PaddleOCR v4** + **PyMuPDF** | 中文支持优秀，表格/图文混排识别准确率高；PaddleOCR 专业版对石油类手写字体友好 |
| 文档分类 | 8分类文本分类 | **BGE-M3** Embedding + 余弦相似度（少样本场景）<br>或 **BERT-wwm-ext** fine-tune（有标注样本≥200条） | BGE-M3 零样本效果好，可快速上线；有足够样本后换 fine-tune 模型提升至 95%+ |
| 井号识别 | NER 实体识别 | **正则规则 + ChatGLM3-6B / Qwen2.5-7B**（混合策略） | 井号格式相对规律（X-XXX格式），规则先行覆盖 80%；LLM 兜底处理异常格式 |
| 关键字段抽取 | 结构化信息抽取 | **Qwen2.5-72B / DeepSeek-V3**（API调用）<br>或私有化部署 **Qwen2.5-14B-Instruct** | 长文本理解能力强，支持复杂表格和专业术语；可私有化部署保障数据安全 |
| 置信度评估 | 字段质量打分 | 规则引擎 + LLM 自评分 | 结合业务规则（单位合法性、数值范围）和模型输出 logprob |

---

### 1.3 私有化部署 vs API 调用决策

```
数据敏感度高（甲方要求）？
    ├── 是 → 私有化部署 Qwen2.5-14B-Instruct（A100/H20 × 2）
    │         推理延迟 ~3s/文档，吞吐 ~20文档/分钟
    └── 否 → 调用 DeepSeek-V3 / Qwen-Max API
              成本 ~0.002元/千token，单文档 ~0.05元
```

---

## 二、提示词设计

### 2.1 提示词设计原则

1. **角色定义**：明确 AI 是"石油工程文档分析专家"
2. **任务约束**：严格按字段库输出，不能臆造不存在的字段值
3. **格式强制**：输出固定为 JSON，含 `value` 和 `confidence` 双字段
4. **缺省处理**：文档中找不到的字段输出 `null`，不猜测
5. **专业词典注入**：将行业术语、单位、层位名称注入 System Prompt

---

### 2.2 System Prompt（通用基础）

```
你是一名资深石油工程文档分析专家，熟悉中国石油行业标准 SY/T 5788、
SY/T 5089、SY/T 5132、SY/T 5483、SY/T 5320、SY/T 5154 等规范。

你的任务是从油气井相关文档中提取结构化信息。

【行为规则】
1. 仅根据文档内容提取，绝对不能推断或捏造未出现的信息；
2. 所有数值保留原始单位，不换算；
3. 无法确定的字段输出 null，并在 reason 中说明；
4. 输出严格遵循 JSON Schema，不输出任何额外文字；
5. confidence 为 0.0~1.0 的浮点数，表示提取置信度。

【专业词典】
- 井号格式：X井、XX-X、XXXX-XXX 等，如"塔中1井"、"HZ21-3"
- 常见层位：奥陶系、志留系、石炭系、二叠系、三叠系、侏罗系、白垩系、
            古近系、新近系、第四系，以及各区块本地地层名称
- 钻井液类型：水基钻井液、油基钻井液、合成基钻井液、气体钻井
- 完井方式：射孔完井、裸眼完井、砾石充填完井、尾管完井、膨胀管完井
- 试油方式：DST测试、常规试油、压裂测试、酸化测试
```

---

### 2.3 文档分类提示词

```python
CLASSIFY_PROMPT = """
【任务】判断以下文档属于哪一类油气井资料。

【文档分类定义】
- drilling     钻井资料：钻井设计、钻井日报、固井报告、钻井总结等
- mudlogging   录井资料：综合录井报告、气测录井、岩屑录井、钻时录井等
- wireline     测井资料：测井原始数据、测井解释报告、井壁取心报告等
- testing      试油测试资料：试油设计、试油报告、DST测试报告、压力测试报告等
- completion   完井资料：完井设计、完井总结、射孔记录、完井管柱图等
- geology      地质资料：地质设计、地质总结、储量报告、岩心分析报告等
- production   生产资料：生产日报、开发方案、措施报告、动态分析报告等
- basic        基本信息：不属于以上任何专项类别的综合性文档

【文档内容（前2000字）】
{document_text}

【输出格式】
{{
  "category": "drilling|mudlogging|wireline|testing|completion|geology|production|basic",
  "confidence": 0.0~1.0,
  "evidence": "判断依据的关键词或句子（不超过100字）"
}}
"""
```

---

### 2.4 井号识别提示词

```python
WELLNO_EXTRACT_PROMPT = """
【任务】从以下文档内容中识别所有出现的油气井编号（井号）。

【井号识别规则】
- 井号通常出现在文档标题、封面、页眉、表格首行
- 常见格式：汉字+数字（塔中1井）、字母+数字（TS1-1）、
            区块+序号（HA-101）、坐标代码（QHD32-6-1）
- 同一口井的别称/简称也需识别并归一化

【文档内容】
{document_text}

【输出格式】
{{
  "wells": [
    {{
      "raw_text": "文档中原始文本",
      "normalized": "归一化标准井号",
      "confidence": 0.95,
      "location": "出现位置描述，如标题/封面/表格"
    }}
  ],
  "primary_well": "最主要的井号（单文档单井取唯一值）"
}}
"""
```

---

### 2.5 各类文档字段抽取提示词

#### 2.5.1 钻井资料抽取

```python
DRILLING_EXTRACT_PROMPT = """
【任务】从以下钻井资料文档中提取结构化字段信息。

【目标字段】
钻机型号(RigModel)、钻头程序(BitProgram)、套管程序(CasingProgram)、
钻井液体系(MudSystem)、钻井参数(DrillingParams)、井身结构(WellStructure)、
井斜数据(DeviationData)、固井数据(CementingData)、钻井事故(Accidents)、
编制日期(CreateDate)、编制单位(CreateUnit)、编制人(Creator)

【文档内容】
{document_text}

【输出 JSON Schema】
{{
  "WellNo": {{"value": "xxx", "confidence": 0.95}},
  "DocCategory": {{"value": "drilling", "confidence": 1.0}},
  "DocName": {{"value": "xxx", "confidence": 0.90}},
  "RigModel": {{"value": "xxx或null", "confidence": 0.85}},
  "BitProgram": {{
    "value": [
      {{"section": "一开", "size": "444.5mm", "type": "PDC", "depth": "0-500m"}}
    ],
    "confidence": 0.80
  }},
  "CasingProgram": {{
    "value": [
      {{"name": "导管", "od": "508mm", "depth": "50m"}},
      {{"name": "表层套管", "od": "339.7mm", "depth": "1200m"}}
    ],
    "confidence": 0.82
  }},
  "MudSystem": {{"value": "xxx或null", "confidence": 0.88}},
  "DrillingParams": {{
    "value": {{"WOB": "xxx", "RPM": "xxx", "FlowRate": "xxx"}},
    "confidence": 0.75
  }},
  "WellStructure": {{"value": "xxx或null", "confidence": 0.85}},
  "DeviationData": {{"value": "xxx或null", "confidence": 0.80}},
  "CementingData": {{"value": "xxx或null", "confidence": 0.85}},
  "Accidents": {{"value": "xxx或null", "confidence": 0.90}},
  "CreateDate": {{"value": "YYYY-MM-DD或null", "confidence": 0.92}},
  "CreateUnit": {{"value": "xxx或null", "confidence": 0.88}},
  "Creator": {{"value": "xxx或null", "confidence": 0.85}},
  "FileFormat": {{"value": "PDF", "confidence": 1.0}}
}}
"""
```

#### 2.5.2 试油测试资料抽取（产量数据精度要求最高）

```python
TESTING_EXTRACT_PROMPT = """
【任务】从以下试油/测试资料文档中提取结构化字段信息。

【重点关注】产量数据（日产油/气/水）、压力数据、地层参数务必精确提取，
            保留原始单位，数值不能四舍五入。

【目标字段】
试油层位(TestFormation)、试油井段(TestInterval)、试油日期(TestDate)、
试油方式(TestMethod)、日产油量(OilRate)、日产气量(GasRate)、
日产水量(WaterRate)、油压(TubingPressure)、套压(CasingPressure)、
地层压力(FormationPressure)、地层温度(FormationTemp)、
原油性质(OilProperties)、结论(Conclusion)、试油单位(TestUnit)

【文档内容】
{document_text}

【输出 JSON Schema】
{{
  "WellNo": {{"value": "xxx", "confidence": 0.95}},
  "DocCategory": {{"value": "testing", "confidence": 1.0}},
  "TestFormation": {{"value": "xxx或null", "confidence": 0.90}},
  "TestInterval": {{
    "value": {{"top": 3200.0, "bottom": 3250.5, "unit": "m"}},
    "confidence": 0.92
  }},
  "TestDate": {{"value": "YYYY-MM-DD或null", "confidence": 0.88}},
  "TestMethod": {{"value": "DST|常规试油|压裂测试|null", "confidence": 0.90}},
  "OilRate": {{"value": {{"amount": 12.5, "unit": "m³/d"}}, "confidence": 0.95}},
  "GasRate": {{"value": {{"amount": 2.3, "unit": "10⁴m³/d"}}, "confidence": 0.93}},
  "WaterRate": {{"value": {{"amount": 0.5, "unit": "m³/d"}}, "confidence": 0.94}},
  "TubingPressure": {{"value": {{"amount": 18.5, "unit": "MPa"}}, "confidence": 0.93}},
  "CasingPressure": {{"value": {{"amount": 15.2, "unit": "MPa"}}, "confidence": 0.93}},
  "FormationPressure": {{"value": {{"amount": 35.8, "unit": "MPa"}}, "confidence": 0.91}},
  "FormationTemp": {{"value": {{"amount": 120.5, "unit": "°C"}}, "confidence": 0.92}},
  "OilProperties": {{
    "value": {{"density": "0.85g/cm³", "viscosity": "5.2mPa·s", "pour_point": "18°C"}},
    "confidence": 0.85
  }},
  "Conclusion": {{"value": "xxx或null", "confidence": 0.88}},
  "TestUnit": {{"value": "xxx或null", "confidence": 0.85}}
}}
"""
```

#### 2.5.3 其他类别提示词（统一模板）

```python
# 录井、测井、完井、地质、生产资料均遵循相同结构
# 以生产资料为例

PRODUCTION_EXTRACT_PROMPT = """
【任务】从以下生产资料文档中提取结构化字段信息。

【重点关注】产量数据的时间序列完整性、累计数据与阶段数据的区分。

【目标字段】
生产日期(ProductionDate)、日产液量(LiquidRate)、日产油量(OilRate)、
日产水量(WaterRate)、日产气量(GasRate)、含水率(WaterCut)、
生产压差(Drawdown)、流压(FlowingPressure)、静压(StaticPressure)、
动液面(FluidLevel)、采油指数(PI)、累计产油(CumOil)、
累计产水(CumWater)、累计产气(CumGas)、生产状态(WellStatus)、
作业措施(Workover)

【文档内容】
{document_text}

【特殊说明】如文档包含生产数据表格，请将每行数据解析为数组中的一个对象。

【输出 JSON Schema】
{{
  "WellNo": {{"value": "xxx", "confidence": 0.95}},
  "DocCategory": {{"value": "production", "confidence": 1.0}},
  "ProductionRecords": {{
    "value": [
      {{
        "ProductionDate": "2025-03-01",
        "LiquidRate": {{"amount": 35.2, "unit": "m³/d"}},
        "OilRate": {{"amount": 28.5, "unit": "t/d"}},
        "WaterRate": {{"amount": 5.8, "unit": "m³/d"}},
        "GasRate": {{"amount": 1.2, "unit": "10⁴m³/d"}},
        "WaterCut": {{"amount": 16.5, "unit": "%"}},
        "WellStatus": "开井"
      }}
    ],
    "confidence": 0.88
  }},
  "CumOil": {{"value": {{"amount": 1.25, "unit": "10⁴t"}}, "confidence": 0.90}},
  "CumWater": {{"value": {{"amount": 0.35, "unit": "10⁴m³"}}, "confidence": 0.90}},
  "CumGas": {{"value": {{"amount": 0.85, "unit": "10⁴m³"}}, "confidence": 0.90}},
  "Workover": {{"value": "xxx或null", "confidence": 0.85}}
}}
"""
```

---

## 三、代码开发

### 3.1 项目结构

```
wellinfo_extractor/
├── config/
│   ├── settings.py          # 全局配置（模型endpoint、API key、字段库）
│   └── field_schemas.py     # 各类文档字段 JSON Schema 定义
├── preprocess/
│   ├── ocr_engine.py        # OCR + 版面解析
│   ├── pdf_parser.py        # PDF 文本提取（PyMuPDF）
│   └── doc_parser.py        # Word/Excel/PPT 解析
├── models/
│   ├── classifier.py        # 文档分类模型
│   ├── wellno_extractor.py  # 井号识别（规则+LLM混合）
│   └── field_extractor.py   # 字段抽取（LLM驱动）
├── prompts/
│   ├── system_prompt.py     # 通用 System Prompt
│   └── task_prompts.py      # 各类文档任务提示词
├── validation/
│   ├── rule_validator.py    # 规则校验引擎
│   └── confidence_scorer.py # 置信度评估
├── pipeline/
│   ├── single_well.py       # 单井处理管道
│   └── batch_processor.py   # 批量处理管道
├── api/
│   └── extraction_api.py    # FastAPI 服务入口
└── tests/
    └── test_extraction.py   # 单元测试
```

---

### 3.2 文档预处理模块

```python
# preprocess/pdf_parser.py
import fitz  # PyMuPDF
import re
from dataclasses import dataclass
from typing import List

@dataclass
class DocumentBlock:
    page_num: int
    block_type: str  # "text" | "table" | "image"
    content: str
    bbox: tuple

class PDFParser:
    """PDF 文档解析器，支持文字型和扫描型 PDF"""

    def __init__(self, ocr_engine=None):
        self.ocr_engine = ocr_engine  # PaddleOCR 实例

    def parse(self, pdf_path: str) -> dict:
        doc = fitz.open(pdf_path)
        result = {
            "total_pages": len(doc),
            "is_scanned": False,
            "full_text": "",
            "blocks": [],
            "tables": []
        }

        all_text_parts = []
        for page_idx, page in enumerate(doc):
            # 提取文本
            text = page.get_text("text")
            if not text.strip() and self.ocr_engine:
                # 扫描件：走OCR
                result["is_scanned"] = True
                text = self._ocr_page(page, page_idx)

            all_text_parts.append(text)

            # 提取表格（PyMuPDF 2.x+ 支持）
            tables = page.find_tables()
            for table in tables:
                result["tables"].append({
                    "page": page_idx + 1,
                    "data": table.extract()
                })

        result["full_text"] = "\n".join(all_text_parts)
        result["text_preview"] = result["full_text"][:2000]
        doc.close()
        return result

    def _ocr_page(self, page, page_idx: int) -> str:
        """使用 PaddleOCR 识别扫描页"""
        pix = page.get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")
        ocr_result = self.ocr_engine.ocr(img_bytes, cls=True)
        lines = [line[1][0] for block in ocr_result for line in block]
        return "\n".join(lines)
```

---

### 3.3 文档分类模型

```python
# models/classifier.py
from typing import Literal
import json
from openai import OpenAI  # 兼容 OpenAI SDK 的本地/云端 LLM

DOC_CATEGORIES = Literal[
    "drilling", "mudlogging", "wireline",
    "testing", "completion", "geology", "production", "basic"
]

class DocumentClassifier:
    """文档类型分类器（LLM驱动）"""

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

    def classify(self, text_preview: str) -> dict:
        """
        Returns:
            {"category": "drilling", "confidence": 0.95, "evidence": "..."}
        """
        from prompts.task_prompts import CLASSIFY_PROMPT
        from prompts.system_prompt import SYSTEM_PROMPT

        prompt = CLASSIFY_PROMPT.format(document_text=text_preview)

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

        # 置信度兜底：若模型输出置信度过低，降级到关键词匹配
        if result.get("confidence", 0) < 0.6:
            keyword_result = self._keyword_fallback(text_preview)
            if keyword_result:
                result["category"] = keyword_result
                result["confidence"] = 0.65
                result["evidence"] += " [关键词补充判断]"

        return result

    def _keyword_fallback(self, text: str) -> str | None:
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

        text_lower = text[:3000]
        scores = {}
        for category, keywords in keyword_rules.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[category] = score

        if scores:
            return max(scores, key=scores.get)
        return None
```

---

### 3.4 井号识别模块

```python
# models/wellno_extractor.py
import re
import json
from openai import OpenAI

class WellNoExtractor:
    """井号识别器：正则规则优先 + LLM兜底"""

    # 覆盖主流井号格式的正则表达式
    WELL_PATTERNS = [
        # 中文名称：塔中1井、苏里格6-3-5井
        r'[\u4e00-\u9fa5]{1,6}[\d\-]{1,10}[井Hh]?\b',
        # 纯字母数字：TS1-1、HZ21-3D、QHD32-6-1
        r'\b[A-Z]{1,4}[\d]{1,4}[-\d]{0,10}[DHSX]?\b',
        # 区块+序号：GS17-1-4、PL19-3-1
        r'\b[A-Z]{1,3}[\d]{1,3}-[\d]{1,3}[-\d]*\b',
        # 带井字：YS108井、YQ10-1井
        r'[A-Z]{1,4}[\d]{1,4}[-\d]*井',
    ]

    def __init__(self, client: OpenAI, model: str = "qwen2.5-7b-instruct"):
        self.client = client
        self.model = model

    def extract(self, full_text: str) -> dict:
        # 第一步：正则快速提取
        candidates = self._regex_extract(full_text[:5000])

        if candidates and len(candidates) <= 3:
            # 正则结果可信，用 LLM 归一化
            return self._normalize_with_llm(candidates, full_text[:1000])
        else:
            # 候选过多或为空，全量 LLM 识别
            return self._llm_extract(full_text[:3000])

    def _regex_extract(self, text: str) -> list:
        candidates = set()
        for pattern in self.WELL_PATTERNS:
            matches = re.findall(pattern, text)
            candidates.update(matches)
        # 过滤明显误识（纯数字、单字母等）
        return [c for c in candidates if len(c) >= 3]

    def _normalize_with_llm(self, candidates: list, context: str) -> dict:
        prompt = f"""
从以下候选项中识别正确的油气井井号，并归一化（统一大写、去除多余字符）。

候选井号：{candidates}
文档上下文：{context}

输出JSON：
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
        from prompts.task_prompts import WELLNO_EXTRACT_PROMPT
        prompt = WELLNO_EXTRACT_PROMPT.format(document_text=text)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        return json.loads(response.choices[0].message.content)
```

---

### 3.5 关键字段抽取模块

```python
# models/field_extractor.py
import json
from openai import OpenAI
from prompts.task_prompts import PROMPT_MAP
from prompts.system_prompt import SYSTEM_PROMPT

class FieldExtractor:
    """关键字段抽取器（LLM驱动，按文档类别分发）"""

    # 超长文档的分块策略：每块最多 6000 tokens
    MAX_CHUNK_TOKENS = 6000
    OVERLAP_TOKENS = 200

    def __init__(self, client: OpenAI, model: str = "qwen2.5-72b-instruct"):
        self.client = client
        self.model = model

    def extract(self, doc_text: str, category: str, tables: list = None) -> dict:
        """
        Args:
            doc_text: 文档全文
            category: 文档分类（如 "drilling"）
            tables:   从文档中解析出的表格数据列表
        Returns:
            结构化字段字典，含 value 和 confidence
        """
        prompt_template = PROMPT_MAP.get(category)
        if not prompt_template:
            raise ValueError(f"未找到分类 {category} 对应的提示词模板")

        # 构造输入：文本 + 表格数据
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
            table_str += f"\n表格{i+1}（第{table['page']}页）:\n"
            for row in table['data']:
                if row:
                    table_str += " | ".join(str(cell or "") for cell in row) + "\n"

        return text + table_str

    def _extract_single(self, text: str, prompt_template: str) -> dict:
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
        """超长文档：分块提取后合并结果"""
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
        """多块结果合并：取置信度最高的字段值"""
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
                    # 列表类型（如生产记录）则合并
                    elif isinstance(data.get("value"), list):
                        existing = merged[field].get("value", [])
                        if isinstance(existing, list):
                            merged[field]["value"] = existing + data["value"]

        return merged

    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 2  # 中文约2字/token估算

    def _split_chunks(self, text: str) -> list:
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

---

### 3.6 规则校验模块

```python
# validation/rule_validator.py
from dataclasses import dataclass
from typing import Any
import re
from datetime import datetime

@dataclass
class ValidationResult:
    field: str
    passed: bool
    error_type: str = ""      # "missing" | "format" | "range" | "unit"
    message: str = ""
    suggestion: str = ""

class RuleValidator:
    """基于业务规则的字段校验引擎"""

    # 数值合理范围规则（min, max）
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
        "OilSaturation":    (0, 100),        # %
        "ShotDensity":      (4, 40),         # 孔/m
    }

    # 日期字段列表
    DATE_FIELDS = ["SpudDate", "CompletionDate", "WellCompletionDate",
                   "CreateDate", "TestDate", "LoggingDate", "ProductionDate"]

    # 必须非空的关键字段
    REQUIRED_FIELDS = ["WellNo", "DocCategory"]

    def validate(self, extracted_data: dict, category: str) -> list[ValidationResult]:
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
                        suggestion=f"请核实原文数值与单位是否正确"
                    ))
                else:
                    results.append(ValidationResult(field=field, passed=True))
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
                    message=f"{field}='{date_str}' 日期格式不符合 YYYY-MM-DD",
                    suggestion="标准格式为 YYYY-MM-DD，如 2025-03-15"
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
        for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y年%m月%d日"]:
            try:
                datetime.strptime(date_str, fmt)
                return True
            except ValueError:
                continue
        return False
```

---

## 四、流程组装（处理管道）

### 4.1 单井处理管道

```python
# pipeline/single_well.py
import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

from preprocess.pdf_parser import PDFParser
from preprocess.ocr_engine import OCREngine
from models.classifier import DocumentClassifier
from models.wellno_extractor import WellNoExtractor
from models.field_extractor import FieldExtractor
from validation.rule_validator import RuleValidator
from validation.confidence_scorer import ConfidenceScorer

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
        from openai import OpenAI

        # 初始化 LLM 客户端（兼容 OpenAI SDK）
        self.llm_client = OpenAI(
            api_key=config["api_key"],
            base_url=config.get("base_url", "https://api.openai.com/v1")
        )

        self.ocr_engine = OCREngine()
        self.pdf_parser = PDFParser(ocr_engine=self.ocr_engine)
        self.classifier = DocumentClassifier(self.llm_client, config["classify_model"])
        self.wellno_extractor = WellNoExtractor(self.llm_client, config["wellno_model"])
        self.field_extractor = FieldExtractor(self.llm_client, config["extract_model"])
        self.validator = RuleValidator()
        self.scorer = ConfidenceScorer()

    def process(self, file_path: str) -> ProcessingResult:
        """处理单个文档，返回结构化结果"""
        result = ProcessingResult(file_path=file_path)
        start_time = time.time()

        try:
            # Step 1: 文档解析
            print(f"[1/5] 解析文档: {Path(file_path).name}")
            parsed_doc = self._parse_document(file_path)

            if not parsed_doc.get("full_text", "").strip():
                result.status = "failed"
                result.error_message = "文档内容为空或无法提取文本"
                return result

            # Step 2: 文档分类
            print(f"[2/5] 文档分类...")
            classify_result = self.classifier.classify(parsed_doc["text_preview"])
            category = classify_result["category"]
            result.doc_category = category

            # Step 3: 井号识别
            print(f"[3/5] 识别井号...")
            wellno_result = self.wellno_extractor.extract(parsed_doc["full_text"])
            result.well_no = wellno_result.get("primary_well", "未识别")

            # Step 4: 字段抽取
            print(f"[4/5] 提取字段 ({category})...")
            extracted = self.field_extractor.extract(
                doc_text=parsed_doc["full_text"],
                category=category,
                tables=parsed_doc.get("tables", [])
            )
            # 注入分类和井号
            extracted["WellNo"] = {"value": result.well_no, "confidence": wellno_result.get("confidence", 0.8)}
            extracted["DocCategory"] = {"value": category, "confidence": classify_result["confidence"]}
            result.extracted_fields = extracted

            # Step 5: 校验与评分
            print(f"[5/5] 规则校验...")
            result.validation_results = self.validator.validate(extracted, category)
            result.overall_confidence = self.scorer.score(extracted, result.validation_results)

            # 判断整体状态
            failed_required = [v for v in result.validation_results
                              if not v.passed and v.error_type == "missing"]
            if failed_required:
                result.status = "partial"
            else:
                result.status = "success"

        except Exception as e:
            result.status = "failed"
            result.error_message = str(e)
            print(f"[ERROR] 处理失败: {e}")

        finally:
            result.processing_time_ms = int((time.time() - start_time) * 1000)
            print(f"处理完成，耗时 {result.processing_time_ms}ms，状态: {result.status}")

        return result

    def _parse_document(self, file_path: str) -> dict:
        suffix = Path(file_path).suffix.lower()
        if suffix == ".pdf":
            return self.pdf_parser.parse(file_path)
        elif suffix in [".doc", ".docx"]:
            from preprocess.doc_parser import DocParser
            return DocParser().parse(file_path)
        elif suffix in [".xls", ".xlsx"]:
            from preprocess.doc_parser import ExcelParser
            return ExcelParser().parse(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {suffix}")
```

---

### 4.2 批量处理管道

```python
# pipeline/batch_processor.py
import asyncio
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

from pipeline.single_well import SingleWellPipeline, ProcessingResult

class BatchProcessor:
    """批量文档处理器，支持多井混合资料"""

    def __init__(self, config: dict, max_workers: int = 4):
        self.config = config
        self.max_workers = max_workers
        # 每个 worker 独立初始化 pipeline（避免共享状态）
        self._pipelines = [
            SingleWellPipeline(config) for _ in range(max_workers)
        ]

    def process_batch(self, file_paths: List[str]) -> Dict:
        """
        批量处理文件列表
        Returns:
            {
              "total": 10,
              "success": 8,
              "partial": 1,
              "failed": 1,
              "by_well": {"TS1-1": [...], "HZ21-3": [...]},
              "results": [ProcessingResult, ...]
            }
        """
        print(f"开始批量处理，共 {len(file_paths)} 个文件，并发数: {self.max_workers}")

        all_results: List[ProcessingResult] = []
        pipeline_queue = list(self._pipelines)

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
                    print(f"✓ {Path(fp).name} → {result.well_no} [{result.status}]")
                except Exception as e:
                    print(f"✗ {Path(fp).name} → 异常: {e}")
                    failed = ProcessingResult(file_path=fp, status="failed", error_message=str(e))
                    all_results.append(failed)

        return self._aggregate(all_results)

    def _aggregate(self, results: List[ProcessingResult]) -> Dict:
        """按井号归组，生成汇总报告"""
        by_well: Dict[str, list] = {}
        stats = {"total": len(results), "success": 0, "partial": 0, "failed": 0}

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

        return {
            **stats,
            "by_well": by_well,
            "results": results,
            "summary": self._generate_summary(by_well)
        }

    def _generate_summary(self, by_well: dict) -> list:
        """生成多井汇总报告"""
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
        return summary
```

---

### 4.3 FastAPI 服务入口

```python
# api/extraction_api.py
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
import tempfile, os, json
from pathlib import Path
from typing import List

from pipeline.single_well import SingleWellPipeline
from pipeline.batch_processor import BatchProcessor
from config.settings import get_config

app = FastAPI(title="油气井信息提取 API", version="1.0.0")
config = get_config()

@app.post("/extract/single", summary="单文档信息提取")
async def extract_single(file: UploadFile = File(...)):
    """上传单个文档，返回结构化抽取结果"""
    # 保存临时文件
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        pipeline = SingleWellPipeline(config)
        result = pipeline.process(tmp_path)

        return JSONResponse({
            "status": result.status,
            "well_no": result.well_no,
            "doc_category": result.doc_category,
            "overall_confidence": result.overall_confidence,
            "extracted_fields": result.extracted_fields,
            "validation_issues": [
                {"field": v.field, "error": v.error_type, "message": v.message}
                for v in result.validation_results if not v.passed
            ],
            "processing_time_ms": result.processing_time_ms
        })
    finally:
        os.unlink(tmp_path)


@app.post("/extract/batch", summary="批量文档信息提取")
async def extract_batch(files: List[UploadFile] = File(...)):
    """上传多个文档（可含多口井混合），返回按井分组结果"""
    tmp_paths = []
    try:
        for file in files:
            suffix = Path(file.filename).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                content = await file.read()
                tmp.write(content)
                tmp_paths.append(tmp.name)

        processor = BatchProcessor(config, max_workers=4)
        batch_result = processor.process_batch(tmp_paths)

        return JSONResponse({
            "stats": {
                "total": batch_result["total"],
                "success": batch_result["success"],
                "partial": batch_result["partial"],
                "failed": batch_result["failed"]
            },
            "by_well": batch_result["by_well"],
            "summary": batch_result["summary"]
        })
    finally:
        for p in tmp_paths:
            if os.path.exists(p):
                os.unlink(p)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "wellinfo-extractor"}
```

---

## 五、模型迭代优化策略

### 5.1 准确率基线与提升路径

```
阶段 0（上线初期）：纯提示词工程
    文档分类准确率：~85%
    字段抽取准确率：~75%
    → 人工审核率：~40%

阶段 1（2周后，有标注数据）：提示词优化 + 少样本示例
    → 分类：~90%，字段抽取：~82%，审核率降至 25%

阶段 2（6周后，≥500条标注）：Fine-tune 分类模型
    → 分类：~96%，字段抽取：~88%，审核率降至 15%

阶段 3（持续）：专业领域 SFT + RLHF
    → 字段抽取：~93%+，审核率降至 <10%
```

### 5.2 人工审核反馈闭环

```python
# 人工审核修正后写回训练数据
def collect_feedback(original_extraction: dict,
                     human_correction: dict,
                     doc_text: str) -> dict:
    """将人工修正转化为训练样本"""
    sample = {
        "doc_text": doc_text[:6000],
        "category": original_extraction.get("DocCategory", {}).get("value"),
        "original": original_extraction,
        "corrected": human_correction,
        "diff_fields": [
            k for k in human_correction
            if human_correction[k] != original_extraction.get(k, {}).get("value")
        ]
    }
    return sample
    # → 定期批量写入标注平台，触发模型再训练
```

---

## 六、专业词典与知识库

```python
# config/domain_knowledge.py

FORMATION_NAMES = {
    "塔里木": ["奥陶系", "志留系", "石炭系", "二叠系", "三叠系", "白垩系", "古近系"],
    "鄂尔多斯": ["延长组", "延安组", "直罗组", "安定组", "马家沟组"],
    "四川": ["须家河组", "嘉陵江组", "飞仙关组", "长兴组", "茅口组", "栖霞组"],
    "渤海湾": ["沙河街组", "东营组", "馆陶组", "明化镇组"],
    "松辽": ["萨尔图油层", "葡萄花油层", "高台子油层", "扶余油层"],
}

OIL_FIELD_WELL_PATTERNS = {
    "塔里木":  r'(TZ|TS|TC|YB|KS|DB)\d+[-\d]*[井]?',
    "鄂尔多斯": r'(S|G|T|H|M)\d+[-\d]*[井]?',
    "渤海":    r'(QHD|BZ|LD|CFD|PL|BH)\d+[-\d]+[-\d]*',
    "南海":    r'(LW|LS|HZ|PY|XJ|YC)\d+[-\d]+[-\d]*',
}
```

---

## 七、总体工期与里程碑

| 周次 | 任务 | 交付物 | 验收标准 |
|------|------|--------|----------|
| 第1周 | 环境搭建 + 文档预处理开发 | PDF/OCR解析模块 | 50份测试文档解析成功率 ≥95% |
| 第2周 | 分类模型 + 井号识别开发 | 分类+井号识别服务 | 分类准确率 ≥85%，井号识别率 ≥90% |
| 第3周 | 各类字段抽取提示词调优 | 7类提示词 + 初版抽取模块 | 关键字段（产量/压力/日期）抽取准确率 ≥80% |
| 第4周 | 规则校验 + 管道组装 + API服务 | 完整处理管道 + API | 端到端单井处理 <30秒，API可用 |
| 持续 | 标注数据积累 + 模型微调 | Fine-tune模型版本 | 每2周一次模型评估与迭代 |
