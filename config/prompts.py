"""提示词模板"""
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

可选分类(一级分类):
- drilling: 钻井资料 (包含钻头程序、套管程序、固井数据等)
- mudlogging: 录井资料 (包含气测数据、岩屑描述、钻时数据等)
- wireline: 测井资料 (包含声波测井、中子测井、密度测井等)
- testing: 试油-测试资料 (包含日产油量、日产气量、压力、温度等)
- completion: 完井资料 (包含射孔参数、完井管柱等)
- geology: 地质资料 (包含储层描述、岩心分析、沉积相分析等)
- production: 生产资料 (包含生产动态、含水率、累计产量等)

二级文档分类(请同时识别):
- 钻井资料: 钻井设计/完井设计/钻井日报/固井报告/钻井工程总结/井身结构图/钻头程序表/套管程序表/固井质量报告/复杂情况报告
- 录井资料: 录井报告/气测记录/岩屑录井/综合录井图/钻时录井/荧光录井/钻井取心报告/后效监测报告/槽面显示记录/气测组分分析
- 测井资料: 测井原始数据/测井解释报告/井壁取心报告/声波测井/密度测井/中子测井/电阻率测井/自然伽马测井/测井综合曲线图
- 试油-测试资料: 试油设计/试油报告/测试报告/DST测试/常规试油/压裂试油/试油成果报告/压力恢复测试/产能测试/流体性质分析报告
- 完井资料: 完井设计/完井总结/射孔数据/完井管柱图/射孔报告/压裂施工设计/压裂施工总结/完井工程质量报告/井下作业报告/投产报告
- 地质资料: 地质设计/地质总结/储量报告/地层分层表/岩心描述/储层评价报告/构造图/沉积相分析/砂体对比图/连井剖面图
- 生产资料: 生产日报/开发方案/措施报告/生产动态分析/采油工艺设计/修井作业报告/增产措施报告/试采报告/产能评价报告/开发调整方案

输出JSON格式:
{{
  "category": "一级分类代码",
  "doc_category": "二级文档分类",
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
- Longitude (经度)
- Latitude (纬度)
- Operator (作业者)
- Contractor (承包商)
- DrillSite (井场位置)
- WaterDepth (水深,单位: 米)
- Platform (平台名称)
- CoordinateSystem (坐标系)
- Elevation (海拔,单位: 米)

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

    # ========== 钻井资料抽取提示词 ==========
    DRILLING_EXTRACT_PROMPT = """从以下钻井资料文档中提取关键字段。

文档内容:
{document_text}

提取字段:
- WellNo (井号)
- DocCategory (文档分类: drilling)
- RigModel (钻机型号)
- BitProgram (钻头程序)
- CasingProgram (套管程序)
- MudSystem (钻井液体系)
- WellStructure (井身结构)
- DeviationData (井斜数据)
- CementingData (固井数据)
- Accidents (钻井事故)
- CreateDate (编制日期,格式: YYYY-MM-DD)
- CreateUnit (编制单位)
- Creator (编制人)
- DrillPipeSpec (钻杆规格)
- DrillCollarSpec (钻铤规格)
- MudDensity (钻井液密度,单位: g/cm³)
- MudViscosity (钻井液粘度,单位: mPa·s)
- RotarySpeed (转速,单位: rpm)
- WOB (钻压,单位: kN)
- ROP (机械钻速,单位: m/h)
- CirculationLoss (漏失量,单位: m³)

输出JSON格式:
{{
  "WellNo": {{"value": "井号", "confidence": 0.95}},
  "DocCategory": {{"value": "drilling", "confidence": 1.0}},
  ...
}}

请只输出JSON,不要有其他内容。"""

    # ========== 录井资料抽取提示词 ==========
    MUDLOGGING_EXTRACT_PROMPT = """从以下录井资料文档中提取关键字段。

文档内容:
{document_text}

提取字段:
- WellNo (井号)
- DocCategory (文档分类: mudlogging)
- LoggingInterval (录井井段)
- LoggingDate (录井日期,格式: YYYY-MM-DD)
- GasShow (气显示)
- OilShow (油显示)
- CuttingsDescription (岩屑描述)
- DrillTime (钻时,单位: min/m)
- TotalHydrocarbon (全烃,单位: %)
- C1 (甲烷,单位: %)
- C2 (乙烷,单位: %)
- C3 (丙烷,单位: %)
- C4 (丁烷,单位: %)
- C5Plus (戊烷以上,单位: %)
- Lithology (岩性)
- DrillingBreak (钻井放空)
- MudLoss (泥浆漏失,单位: m³)
- GasKick (气侵)
- SampleDepth (取样深度,单位: 米)
- FluorescenceLevel (荧光级别)

输出JSON格式:
{{
  "WellNo": {{"value": "井号", "confidence": 0.95}},
  "DocCategory": {{"value": "mudlogging", "confidence": 1.0}},
  ...
}}

请只输出JSON,不要有其他内容。"""

    # ========== 测井资料抽取提示词 ==========
    WIRELINE_EXTRACT_PROMPT = """从以下测井资料文档中提取关键字段。

文档内容:
{document_text}

提取字段:
- WellNo (井号)
- DocCategory (文档分类: wireline)
- LoggingInterval (测井井段)
- LoggingDate (测井日期,格式: YYYY-MM-DD)
- LoggingCompany (测井公司)
- ToolType (仪器类型)
- AcousticLog (声波测井)
- DensityLog (密度测井)
- NeutronLog (中子测井)
- ResistivityLog (电阻率测井)
- GammaRayLog (自然伽马测井)
- CaliperLog (井径测井)
- SPLog (自然电位测井)
- Porosity (孔隙度,单位: %)
- Permeability (渗透率,单位: mD)
- WaterSaturation (含水饱和度,单位: %)
- OilSaturation (含油饱和度,单位: %)
- ReservoirThickness (有效厚度,单位: 米)
- InterpretationResult (解释结果)
- LASFilename (LAS文件名)

输出JSON格式:
{{
  "WellNo": {{"value": "井号", "confidence": 0.95}},
  "DocCategory": {{"value": "wireline", "confidence": 1.0}},
  ...
}}

请只输出JSON,不要有其他内容。"""

    # ========== 试油测试资料抽取提示词 ==========
    TESTING_EXTRACT_PROMPT = """从以下试油测试资料中提取关键字段。

文档内容:
{document_text}

提取字段:
- WellNo (井号)
- DocCategory (文档分类: testing)
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
- GasProperties (天然气性质)
- WaterSalinity (矿化度,单位: mg/L)
- GOR (气油比,单位: m³/m³)
- ChokeSize (油嘴直径,单位: mm)
- Conclusion (结论)
- TestType (测试类型)

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

    # ========== 完井资料抽取提示词 ==========
    COMPLETION_EXTRACT_PROMPT = """从以下完井资料文档中提取关键字段。

文档内容:
{document_text}

提取字段:
- WellNo (井号)
- DocCategory (文档分类: completion)
- CompletionDate (完井日期,格式: YYYY-MM-DD)
- CompletionMethod (完井方式)
- PerforationInterval (射孔井段)
- ShotDensity (射孔密度,单位: 孔/m)
- PerforationGun (射孔枪型号)
- PerforationPhase (射孔相位)
- PerforationDate (射孔日期,格式: YYYY-MM-DD)
- TubingString (油管柱)
- CasingString (套管柱)
- Packer (封隔器)
- GravelPack (砾石充填)
- Screen (筛管)
- Acidizing (酸化)
- Fracturing (压裂)
- ProductionCasing (生产套管)
- IntermediateCasing (技术套管)
- SurfaceCasing (表层套管)
- CementQuality (固井质量)
- CompletionCompany (完井公司)

输出JSON格式:
{{
  "WellNo": {{"value": "井号", "confidence": 0.95}},
  "DocCategory": {{"value": "completion", "confidence": 1.0}},
  ...
}}

请只输出JSON,不要有其他内容。"""

    # ========== 地质资料抽取提示词 ==========
    GEOLOGY_EXTRACT_PROMPT = """从以下地质资料文档中提取关键字段。

文档内容:
{document_text}

提取字段:
- WellNo (井号)
- DocCategory (文档分类: geology)
- ReservoirName (储层名称)
- ReservoirType (储层类型)
- DepositionalEnvironment (沉积环境)
- SedimentaryFacies (沉积相)
- RockType (岩性)
- ReservoirThickness (储层厚度,单位: 米)
- ReservoirArea (含油面积,单位: km²)
- OOIP (地质储量,单位: 10⁴t)
- Porosity (孔隙度,单位: %)
- Permeability (渗透率,单位: mD)
- WaterSaturation (含水饱和度,单位: %)
- OilSaturation (含油饱和度,单位: %)
- CoreAnalysis (岩心分析)
- ThinSection (薄片鉴定)
- SourceRock (烃源岩)
- CapRock (盖层)
- TrapType (圈闭类型)
- StructuralMap (构造图)
- IsochoreMap (等厚图)
- IsopachMap (等值图)

输出JSON格式:
{{
  "WellNo": {{"value": "井号", "confidence": 0.95}},
  "DocCategory": {{"value": "geology", "confidence": 1.0}},
  ...
}}

请只输出JSON,不要有其他内容。"""

    # ========== 生产资料抽取提示词 ==========
    PRODUCTION_EXTRACT_PROMPT = """从以下生产资料文档中提取关键字段。

文档内容:
{document_text}

提取字段:
- WellNo (井号)
- DocCategory (文档分类: production)
- ProductionDate (生产日期,格式: YYYY-MM-DD)
- DailyOilProduction (日产油量,单位: m³/d)
- DailyGasProduction (日产气量,单位: 10⁴m³/d)
- DailyWaterProduction (日产水量,单位: m³/d)
- CumulativeOil (累计产油,单位: 10⁴t)
- CumulativeGas (累计产气,单位: 10⁴m³)
- CumulativeWater (累计产水,单位: m³)
- WaterCut (含水率,单位: %)
- WorkingSystem (工作制度)
- ChokeSize (油嘴直径,单位: mm)
- TubingPressure (油压,单位: MPa)
- CasingPressure (套压,单位: MPa)
- FlowingPressure (流压,单位: MPa)
- StaticPressure (静压,单位: MPa)
- FluidLevel (动液面,单位: 米)
- PumpEfficiency (泵效,单位: %)
- StrokeFrequency (冲次,单位: 次/分)
- StrokeLength (冲程,单位: 米)
- ProductionStatus (生产状态)

输出JSON格式:
{{
  "WellNo": {{"value": "井号", "confidence": 0.95}},
  "DocCategory": {{"value": "production", "confidence": 1.0}},
  ...
}}

请只输出JSON,不要有其他内容。"""

    # ========== 提示词映射 ==========
    PROMPT_MAP: Dict[str, str] = {
        "basic": BASIC_EXTRACT_PROMPT,
        "drilling": DRILLING_EXTRACT_PROMPT,
        "mudlogging": MUDLOGGING_EXTRACT_PROMPT,
        "wireline": WIRELINE_EXTRACT_PROMPT,
        "testing": TESTING_EXTRACT_PROMPT,
        "completion": COMPLETION_EXTRACT_PROMPT,
        "geology": GEOLOGY_EXTRACT_PROMPT,
        "production": PRODUCTION_EXTRACT_PROMPT,
    }
