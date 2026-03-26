"""字段Schema定义"""
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class FieldDefinition:
    """字段定义"""
    name: str                    # 字段名
    display_name: str            # 显示名
    data_type: str              # 数据类型: string | float | int | date
    required: bool              # 是否必填
    weight: float = 1.0         # 权重 (用于置信度计算)
    min_value: Optional[float] = None     # 最小值 (数值型)
    max_value: Optional[float] = None     # 最大值 (数值型)
    unit: Optional[str] = None  # 单位


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
        FieldDefinition("DrillingDays", "钻井周期", "int", False, 1.0, 0, 365, "天"),
        FieldDefinition("CompletionDays", "完井周期", "int", False, 1.0, 0, 365, "天"),
        FieldDefinition("DesignDepth", "设计井深", "float", False, 1.2, 0, 12000, "米"),
        FieldDefinition("TotalDepth", "完钻井深", "float", False, 1.5, 100, 12000, "米"),
        FieldDefinition("BottomFormation", "完钻层位", "string", False),
        FieldDefinition("DrillingPurpose", "钻探目的", "string", False),
        FieldDefinition("Longitude", "经度", "float", False, 1.0, min_value=-180, max_value=180),
        FieldDefinition("Latitude", "纬度", "float", False, 1.0, min_value=-90, max_value=90),
        FieldDefinition("Operator", "作业者", "string", False),
        FieldDefinition("Contractor", "承包商", "string", False),
        FieldDefinition("DrillSite", "井场位置", "string", False),
        FieldDefinition("WaterDepth", "水深", "float", False, 1.0, min_value=0, max_value=3000, unit="米"),
        FieldDefinition("Platform", "平台名称", "string", False),
        FieldDefinition("CoordinateSystem", "坐标系", "string", False),
        FieldDefinition("Elevation", "海拔", "float", False, 1.0, min_value=-500, max_value=5000, unit="米"),
    ]

    # ========== 钻井资料 (21个字段) ==========
    DRILLING_FIELDS: List[FieldDefinition] = [
        FieldDefinition("WellNo", "井号", "string", True, 2.0),
        FieldDefinition("DocCategory", "文档分类", "string", True, 1.5),
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
        FieldDefinition("DrillPipeSpec", "钻杆规格", "string", False),
        FieldDefinition("DrillCollarSpec", "钻铤规格", "string", False),
        FieldDefinition("MudDensity", "钻井液密度", "float", False, 1.0, min_value=1.0, max_value=3.0, unit="g/cm³"),
        FieldDefinition("MudViscosity", "钻井液粘度", "float", False, 1.0, min_value=10, max_value=100, unit="mPa·s"),
        FieldDefinition("RotarySpeed", "转速", "float", False, 1.0, min_value=0, max_value=300, unit="rpm"),
        FieldDefinition("WOB", "钻压", "float", False, 1.0, min_value=0, max_value=500, unit="kN"),
        FieldDefinition("ROP", "机械钻速", "float", False, 1.0, min_value=0, max_value=50, unit="m/h"),
        FieldDefinition("CirculationLoss", "漏失量", "float", False, 1.0, min_value=0, max_value=1000, unit="m³"),
    ]

    # ========== 试油测试资料 (20个字段,重点) ==========
    TESTING_FIELDS: List[FieldDefinition] = [
        FieldDefinition("WellNo", "井号", "string", True, 2.0),
        FieldDefinition("DocCategory", "文档分类", "string", True, 1.5),
        FieldDefinition("TestFormation", "试油层位", "string", True, 1.5),
        FieldDefinition("TestInterval", "试油井段", "string", True, 1.5),
        FieldDefinition("TestDate", "试油日期", "date", True, 1.2),
        FieldDefinition("TestMethod", "试油方式", "string", False),
        FieldDefinition("OilRate", "日产油量", "float", True, 2.0, 0, 5000, "m³/d"),
        FieldDefinition("GasRate", "日产气量", "float", False, 2.0, 0, 1000, "10⁴m³/d"),
        FieldDefinition("WaterRate", "日产水量", "float", False, 2.0, 0, 10000, "m³/d"),
        FieldDefinition("TubingPressure", "油压", "float", False, 1.5, 0, 200, "MPa"),
        FieldDefinition("CasingPressure", "套压", "float", False, 1.5, 0, 200, "MPa"),
        FieldDefinition("FormationPressure", "地层压力", "float", False, 1.5, 0, 300, "MPa"),
        FieldDefinition("FormationTemp", "地层温度", "float", False, 1.2, 10, 350, "°C"),
        FieldDefinition("OilProperties", "原油性质", "string", False),
        FieldDefinition("GasProperties", "天然气性质", "string", False),
        FieldDefinition("WaterSalinity", "矿化度", "float", False, 1.0, min_value=0, max_value=300000, unit="mg/L"),
        FieldDefinition("GOR", "气油比", "float", False, 1.0, min_value=0, max_value=10000, unit="m³/m³"),
        FieldDefinition("ChokeSize", "油嘴直径", "float", False, 1.0, min_value=1, max_value=20, unit="mm"),
        FieldDefinition("Conclusion", "结论", "string", False),
        FieldDefinition("TestType", "测试类型", "string", False),
    ]

    # ========== 录井资料 (20个字段) ==========
    MUDLOGGING_FIELDS: List[FieldDefinition] = [
        FieldDefinition("WellNo", "井号", "string", True, 2.0),
        FieldDefinition("DocCategory", "文档分类", "string", True, 1.5),
        FieldDefinition("LoggingInterval", "录井井段", "string", False),
        FieldDefinition("LoggingDate", "录井日期", "date", False),
        FieldDefinition("GasShow", "气显示", "string", False),
        FieldDefinition("OilShow", "油显示", "string", False),
        FieldDefinition("CuttingsDescription", "岩屑描述", "string", False),
        FieldDefinition("DrillTime", "钻时", "float", False, 1.0, min_value=0, max_value=500, unit="min/m"),
        FieldDefinition("TotalHydrocarbon", "全烃", "float", False, 1.0, min_value=0, max_value=100, unit="%"),
        FieldDefinition("C1", "甲烷", "float", False, 1.0, min_value=0, max_value=100, unit="%"),
        FieldDefinition("C2", "乙烷", "float", False, 1.0, min_value=0, max_value=100, unit="%"),
        FieldDefinition("C3", "丙烷", "float", False, 1.0, min_value=0, max_value=100, unit="%"),
        FieldDefinition("C4", "丁烷", "float", False, 1.0, min_value=0, max_value=100, unit="%"),
        FieldDefinition("C5Plus", "戊烷以上", "float", False, 1.0, min_value=0, max_value=100, unit="%"),
        FieldDefinition("Lithology", "岩性", "string", False),
        FieldDefinition("DrillingBreak", "钻井放空", "string", False),
        FieldDefinition("MudLoss", "泥浆漏失", "float", False, 1.0, min_value=0, max_value=1000, unit="m³"),
        FieldDefinition("GasKick", "气侵", "string", False),
        FieldDefinition("SampleDepth", "取样深度", "float", False, 1.0, min_value=0, max_value=12000, unit="米"),
        FieldDefinition("FluorescenceLevel", "荧光级别", "string", False),
    ]

    # ========== 测井资料 (20个字段) ==========
    WIRELINE_FIELDS: List[FieldDefinition] = [
        FieldDefinition("WellNo", "井号", "string", True, 2.0),
        FieldDefinition("DocCategory", "文档分类", "string", True, 1.5),
        FieldDefinition("LoggingInterval", "测井井段", "string", False),
        FieldDefinition("LoggingDate", "测井日期", "date", False),
        FieldDefinition("LoggingCompany", "测井公司", "string", False),
        FieldDefinition("ToolType", "仪器类型", "string", False),
        FieldDefinition("AcousticLog", "声波测井", "string", False),
        FieldDefinition("DensityLog", "密度测井", "string", False),
        FieldDefinition("NeutronLog", "中子测井", "string", False),
        FieldDefinition("ResistivityLog", "电阻率测井", "string", False),
        FieldDefinition("GammaRayLog", "自然伽马测井", "string", False),
        FieldDefinition("CaliperLog", "井径测井", "string", False),
        FieldDefinition("SPLog", "自然电位测井", "string", False),
        FieldDefinition("Porosity", "孔隙度", "float", False, 1.0, min_value=0, max_value=50, unit="%"),
        FieldDefinition("Permeability", "渗透率", "float", False, 1.0, min_value=0, max_value=10000, unit="mD"),
        FieldDefinition("WaterSaturation", "含水饱和度", "float", False, 1.0, min_value=0, max_value=100, unit="%"),
        FieldDefinition("OilSaturation", "含油饱和度", "float", False, 1.0, min_value=0, max_value=100, unit="%"),
        FieldDefinition("ReservoirThickness", "有效厚度", "float", False, 1.0, min_value=0, max_value=500, unit="米"),
        FieldDefinition("InterpretationResult", "解释结果", "string", False),
        FieldDefinition("LASFilename", "LAS文件名", "string", False),
    ]

    # ========== 完井资料 (21个字段) ==========
    COMPLETION_FIELDS: List[FieldDefinition] = [
        FieldDefinition("WellNo", "井号", "string", True, 2.0),
        FieldDefinition("DocCategory", "文档分类", "string", True, 1.5),
        FieldDefinition("CompletionDate", "完井日期", "date", False),
        FieldDefinition("CompletionMethod", "完井方式", "string", False),
        FieldDefinition("PerforationInterval", "射孔井段", "string", True, 1.5),
        FieldDefinition("ShotDensity", "射孔密度", "float", False, 1.0, min_value=4, max_value=40, unit="孔/m"),
        FieldDefinition("PerforationGun", "射孔枪型号", "string", False),
        FieldDefinition("PerforationPhase", "射孔相位", "string", False),
        FieldDefinition("PerforationDate", "射孔日期", "date", False),
        FieldDefinition("TubingString", "油管柱", "string", False),
        FieldDefinition("CasingString", "套管柱", "string", False),
        FieldDefinition("Packer", "封隔器", "string", False),
        FieldDefinition("GravelPack", "砾石充填", "string", False),
        FieldDefinition("Screen", "筛管", "string", False),
        FieldDefinition("Acidizing", "酸化", "string", False),
        FieldDefinition("Fracturing", "压裂", "string", False),
        FieldDefinition("ProductionCasing", "生产套管", "string", False),
        FieldDefinition("IntermediateCasing", "技术套管", "string", False),
        FieldDefinition("SurfaceCasing", "表层套管", "string", False),
        FieldDefinition("CementQuality", "固井质量", "string", False),
        FieldDefinition("CompletionCompany", "完井公司", "string", False),
    ]

    # ========== 地质资料 (21个字段) ==========
    GEOLOGY_FIELDS: List[FieldDefinition] = [
        FieldDefinition("WellNo", "井号", "string", True, 2.0),
        FieldDefinition("DocCategory", "文档分类", "string", True, 1.5),
        FieldDefinition("ReservoirName", "储层名称", "string", False),
        FieldDefinition("ReservoirType", "储层类型", "string", False),
        FieldDefinition("DepositionalEnvironment", "沉积环境", "string", False),
        FieldDefinition("SedimentaryFacies", "沉积相", "string", False),
        FieldDefinition("RockType", "岩性", "string", False),
        FieldDefinition("ReservoirThickness", "储层厚度", "float", False, 1.0, min_value=0, max_value=500, unit="米"),
        FieldDefinition("ReservoirArea", "含油面积", "float", False, 1.0, min_value=0, max_value=10000, unit="km²"),
        FieldDefinition("OOIP", "地质储量", "float", False, 1.0, min_value=0, max_value=1000000, unit="10⁴t"),
        FieldDefinition("Porosity", "孔隙度", "float", False, 1.0, min_value=0, max_value=50, unit="%"),
        FieldDefinition("Permeability", "渗透率", "float", False, 1.0, min_value=0, max_value=10000, unit="mD"),
        FieldDefinition("WaterSaturation", "含水饱和度", "float", False, 1.0, min_value=0, max_value=100, unit="%"),
        FieldDefinition("OilSaturation", "含油饱和度", "float", False, 1.0, min_value=0, max_value=100, unit="%"),
        FieldDefinition("CoreAnalysis", "岩心分析", "string", False),
        FieldDefinition("ThinSection", "薄片鉴定", "string", False),
        FieldDefinition("SourceRock", "烃源岩", "string", False),
        FieldDefinition("CapRock", "盖层", "string", False),
        FieldDefinition("TrapType", "圈闭类型", "string", False),
        FieldDefinition("StructuralMap", "构造图", "string", False),
        FieldDefinition("IsochoreMap", "等厚图", "string", False),
        FieldDefinition("IsopachMap", "等值图", "string", False),
    ]

    # ========== 生产资料 (21个字段) ==========
    PRODUCTION_FIELDS: List[FieldDefinition] = [
        FieldDefinition("WellNo", "井号", "string", True, 2.0),
        FieldDefinition("DocCategory", "文档分类", "string", True, 1.5),
        FieldDefinition("ProductionDate", "生产日期", "date", False),
        FieldDefinition("DailyOilProduction", "日产油量", "float", False, 1.0, min_value=0, max_value=5000, unit="m³/d"),
        FieldDefinition("DailyGasProduction", "日产气量", "float", False, 1.0, min_value=0, max_value=1000, unit="10⁴m³/d"),
        FieldDefinition("DailyWaterProduction", "日产水量", "float", False, 1.0, min_value=0, max_value=10000, unit="m³/d"),
        FieldDefinition("CumulativeOil", "累计产油", "float", False, 1.0, min_value=0, max_value=1000000, unit="10⁴t"),
        FieldDefinition("CumulativeGas", "累计产气", "float", False, 1.0, min_value=0, max_value=100000, unit="10⁴m³"),
        FieldDefinition("CumulativeWater", "累计产水", "float", False, 1.0, min_value=0, max_value=1000000, unit="m³"),
        FieldDefinition("WaterCut", "含水率", "float", False, 1.0, min_value=0, max_value=100, unit="%"),
        FieldDefinition("WorkingSystem", "工作制度", "string", False),
        FieldDefinition("ChokeSize", "油嘴直径", "float", False, 1.0, min_value=1, max_value=20, unit="mm"),
        FieldDefinition("TubingPressure", "油压", "float", False, 1.0, min_value=0, max_value=200, unit="MPa"),
        FieldDefinition("CasingPressure", "套压", "float", False, 1.0, min_value=0, max_value=200, unit="MPa"),
        FieldDefinition("FlowingPressure", "流压", "float", False, 1.0, min_value=0, max_value=100, unit="MPa"),
        FieldDefinition("StaticPressure", "静压", "float", False, 1.0, min_value=0, max_value=100, unit="MPa"),
        FieldDefinition("FluidLevel", "动液面", "float", False, 1.0, min_value=0, max_value=5000, unit="米"),
        FieldDefinition("PumpEfficiency", "泵效", "float", False, 1.0, min_value=0, max_value=100, unit="%"),
        FieldDefinition("StrokeFrequency", "冲次", "float", False, 1.0, min_value=0, max_value=20, unit="次/分"),
        FieldDefinition("StrokeLength", "冲程", "float", False, 1.0, min_value=0, max_value=10, unit="米"),
        FieldDefinition("ProductionStatus", "生产状态", "string", False),
    ]

    # ========== 一级分类映射 ==========
    CATEGORY_MAP: Dict[str, str] = {
        "drilling": "钻井资料",
        "mudlogging": "录井资料",
        "wireline": "测井资料",
        "testing": "试油-测试资料",
        "completion": "完井资料",
        "geology": "地质资料",
        "production": "生产资料",
    }

    # ========== 二级文档分类 ==========
    # 每个一级分类下的具体文档类型
    DOC_CATEGORIES: Dict[str, List[str]] = {
        "drilling": [
            "钻井设计", "完井设计", "钻井日报", "固井报告",
            "钻井工程总结", "井身结构图", "钻头程序表",
            "套管程序表", "固井质量报告", "复杂情况报告"
        ],
        "mudlogging": [
            "录井报告", "气测记录", "岩屑录井", "综合录井图",
            "钻时录井", "荧光录井", "钻井取心报告",
            "后效监测报告", "槽面显示记录", "气测组分分析"
        ],
        "wireline": [
            "测井原始数据", "测井解释报告", "井壁取心报告",
            "声波测井", "密度测井", "中子测井",
            "电阻率测井", "自然伽马测井", "测井综合曲线图"
        ],
        "testing": [
            "试油设计", "试油报告", "测试报告", "DST测试",
            "常规试油", "压裂试油", "试油成果报告",
            "压力恢复测试", "产能测试", "流体性质分析报告"
        ],
        "completion": [
            "完井设计", "完井总结", "射孔数据", "完井管柱图",
            "射孔报告", "压裂施工设计", "压裂施工总结",
            "完井工程质量报告", "井下作业报告", "投产报告"
        ],
        "geology": [
            "地质设计", "地质总结", "储量报告", "地层分层表",
            "岩心描述", "储层评价报告", "构造图",
            "沉积相分析", "砂体对比图", "连井剖面图"
        ],
        "production": [
            "生产日报", "开发方案", "措施报告", "生产动态分析",
            "采油工艺设计", "修井作业报告", "增产措施报告",
            "试采报告", "产能评价报告", "开发调整方案"
        ],
    }

    # ========== 字段定义映射 ==========
    CATEGORY_FIELDS_MAP: Dict[str, List[FieldDefinition]] = {
        "drilling": DRILLING_FIELDS,
        "mudlogging": MUDLOGGING_FIELDS,
        "wireline": WIRELINE_FIELDS,
        "testing": TESTING_FIELDS,
        "completion": COMPLETION_FIELDS,
        "geology": GEOLOGY_FIELDS,
        "production": PRODUCTION_FIELDS,
    }

    @classmethod
    def get_all_fields(cls, category: str) -> List[FieldDefinition]:
        """获取分类的所有字段(包含基本信息字段)"""
        category_fields = cls.CATEGORY_FIELDS_MAP.get(category, cls.BASIC_FIELDS)
        # 将基本信息字段合并到所有分类中
        all_fields = cls.BASIC_FIELDS + category_fields
        return all_fields

    @classmethod
    def get_category_fields(cls, category: str) -> List[FieldDefinition]:
        """仅获取分类特定字段(不含基本信息字段)"""
        return cls.CATEGORY_FIELDS_MAP.get(category, cls.BASIC_FIELDS)

    @classmethod
    def get_fields_by_category(cls, category: str) -> List[FieldDefinition]:
        """根据分类获取字段定义(已弃用,使用get_all_fields)"""
        return cls.get_all_fields(category)

    @classmethod
    def get_field_names(cls, category: str) -> List[str]:
        """获取字段名列表"""
        fields = cls.get_fields_by_category(category)
        return [f.name for f in fields]

    @classmethod
    def get_required_fields(cls, category: str) -> List[str]:
        """获取必填字段名列表"""
        fields = cls.get_fields_by_category(category)
        return [f.name for f in fields if f.required]


# 导出所有字段定义
FIELD_SCHEMAS = FieldSchemas
DOCUMENT_TYPES = FieldSchemas.CATEGORY_MAP  # 别名，用于向后兼容
