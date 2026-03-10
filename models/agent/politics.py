from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, Field

"""
主线关联
"""


# ==================== 枚举定义 ====================

class KnowledgeTypeLevel1(str, Enum):
    """知识点类型一级节点枚举"""
    CONCEPT = "概念类"
    VIEWPOINT = "观点类"
    MECHANISM = "机制类"
    INSTITUTION = "制度类"
    METHOD = "方法类"
    ANALYSIS = "辨析类"


class KnowledgeTypeLevel2(str, Enum):
    """知识点类型二级节点枚举"""
    # 概念类
    DEFINITION = "定义"
    FEATURE = "特征"
    BOUNDARY_CONDITION = "边界/条件"
    DIFFERENCE_RELATION = "区别/联系"

    # 观点类
    STATUS = "地位"
    SIGNIFICANCE = "意义"
    FUNCTION = "作用"
    GOAL_VALUE = "目标/价值指向"

    # 机制类
    ACTION_PATH = "作用路径/链条"
    CAUSAL_MECHANISM = "因果机制"
    INNER_CONTRADICTION = "内在矛盾与转化"

    # 制度类
    SUBJECT_DUTY = "主体职责"
    POWER_STRUCTURE = "权力结构"
    PROCEDURE_RULE = "程序规则"
    SUPERVISION_CHECK = "监督制约"

    # 方法类
    ANALYSIS_FRAMEWORK = "分析框架"
    PROBLEM_SOLVING = "解题方法"
    GOVERNANCE_METHOD = "治理方法"
    THINKING_METHOD = "思维方法"

    # 辨析类
    COMMON_MISCONCEPTION = "常见误区"
    COUNTEREXAMPLE_CORRECTION = "反例纠偏"
    CONDITION_LIMITATION = "条件限制"
    OPTION_INTERFERENCE = "选项干扰点"


class AxisLevel1(str, Enum):
    """大概念轴一级节点枚举"""
    HUMAN_SOCIETY = "人与社会"
    STATE_POLITICS = "国家与政治"
    LAW_RIGHTS = "法治与权利"
    ECONOMY_DEVELOPMENT = "经济与发展"
    CULTURE_VALUE = "文化与价值"
    PHILOSOPHY_METHOD = "哲学与方法"
    INTERNATIONAL_COMMUNITY = "国际与共同体"


class AxisLevel2(str, Enum):
    """大概念轴二级主题簇枚举"""
    # 人与社会
    RULE_ORDER = "规则与秩序"
    RESPONSIBILITY_PARTICIPATION = "责任与参与"
    MORAL_PUBLIC_LIFE = "道德品质与公共生活"
    SOCIAL_GOVERNANCE_COORDINATION = "社会治理与社会协同"

    # 国家与政治
    STATE_NATURE_ORGAN = "国家性质与国家机构"
    DEMOCRACY_POLITICAL_PARTICIPATION = "民主政治与政治参与"
    GOVERNANCE_SYSTEM_CAPACITY = "治理体系与治理能力"
    PARTY_LEADERSHIP_POLITICAL_DIRECTION = "党的领导与政治方向"

    # 法治与权利
    CONSTITUTION_LEGAL_SYSTEM = "宪法与法律体系"
    RIGHTS_DUTIES_BOUNDARIES = "权利义务与边界"
    PROCEDURAL_JUSTICE_RELIEF = "程序正义与救济"
    SUPERVISION_POWER_REGULATION = "监督制约与权力规范"

    # 经济与发展
    PRODUCTION_DISTRIBUTION = "生产与分配"
    MARKET_GOVERNMENT = "市场与政府"
    MACRO_CONTROL_RISK = "宏观调控与风险"
    HIGH_QUALITY_DEVELOPMENT_COMMON_PROSPERITY = "高质量发展与共同富裕"

    # 文化与价值
    CORE_VALUES = "核心价值观"
    CULTURAL_INHERITANCE_INNOVATION = "文化传承创新"
    IDEOLOGY_CULTURAL_SECURITY = "意识形态与文化安全"
    CIVILIZATION_EXCHANGE_MUTUAL_LEARNING = "文明交流互鉴"

    # 哲学与方法
    PRACTICE_COGNITION = "实践与认识"
    CONNECTION_DEVELOPMENT = "联系与发展"
    CONTRADICTION_ANALYSIS = "矛盾分析"
    INNOVATION_DIALECTICAL_NEGATION = "创新与辩证否定"
    VALUE_JUDGMENT_CHOICE = "价值判断与价值选择"

    # 国际与共同体
    INTERNATIONAL_RELATIONS_PEACE = "国际关系与和平发展"
    GLOBAL_GOVERNANCE_ORGANIZATIONS = "全球治理与国际组织"
    COMMUNITY_SHARED_FUTURE_CHINA_ROLE = "人类命运共同体与中国担当"


class MainlineLevel1(str, Enum):
    """主线网一级节点枚举"""
    PARTY_STATE_PEOPLE_LAW = "党—国家—人民—法治"
    DEVELOPMENT_DISTRIBUTION_FAIRNESS_COMMON_PROSPERITY = "发展—分配—公平—共同富裕"
    RIGHTS_DUTIES_RULES_RESPONSIBILITY = "权利—义务—规则—责任"
    VALUE_CULTURE_IDENTITY_CONFIDENCE = "价值—文化—认同—自信"
    PRACTICE_COGNITION_CONTRADICTION_CHOICE = "实践—认识—矛盾—选择"


class MainlineLevel2(str, Enum):
    """主线网二级节点（子线）枚举"""
    # 党—国家—人民—法治
    PARTY_LEADERSHIP = "党的领导"
    PEOPLE_MASTERSHIP = "人民当家作主"
    RULE_OF_LAW = "依法治国"
    POWER_OPERATION_SUPERVISION = "权力运行与监督"
    GOVERNANCE_MODERNIZATION_EFFICIENCY = "治理现代化与效能"

    # 发展—分配—公平—共同富裕
    HIGH_QUALITY_DEVELOPMENT = "高质量发展"
    BASIC_ECONOMIC_SYSTEM = "基本经济制度"
    DISTRIBUTION_STRUCTURE = "分配结构"
    FAIRNESS_GUARANTEE = "公平保障"
    MACRO_CONTROL_RISK_GOVERNANCE = "宏观调控与风险治理"

    # 权利—义务—规则—责任
    RIGHTS_PROTECTION_BOUNDARIES = "权利保障与边界"
    LEGAL_DUTIES_RESPONSIBILITIES = "法定义务与责任"
    RULE_AWARENESS_PUBLIC_ORDER = "规则意识与公共秩序"
    LEGAL_RIGHTS_PROTECTION_PATH = "依法维权路径"
    MINOR_PROTECTION = "未成年人保护"

    # 价值—文化—认同—自信
    CORE_VALUES = "核心价值观"
    CULTURAL_THREE_FORMS = "文化三形态"
    CULTURAL_POWER_DEVELOPMENT = "文化强国与文化发展"
    IDEOLOGY_CULTURAL_SECURITY = "意识形态与文化安全"
    EXCHANGE_MUTUAL_LEARNING_CIVILIZATION = "交流互鉴与文明互鉴"

    # 实践—认识—矛盾—选择
    PRACTICE_COGNITION = "实践与认识"
    CONNECTION_DEVELOPMENT = "联系与发展"
    CONTRADICTION_ANALYSIS = "矛盾分析"
    DIALECTICAL_NEGATION_INNOVATION = "辩证否定与创新"
    VALUE_JUDGMENT_CHOICE = "价值判断与价值选择"


class RoleFunction(str, Enum):
    """知识点在推理链中的功能角色枚举"""
    PRECONDITION = "前提"  # 作为推理的前提条件
    BRIDGE = "桥"  # 作为连接两个知识点的桥梁
    CONCLUSION = "落点"  # 作为推理的最终结论
    METHODOLOGY_UPGRADE = "方法论升格"  # 提供方法论层面的升华


class ConfidenceLevel(str, Enum):
    """对齐置信度枚举"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FrameworkType(str, Enum):
    """框架类型枚举，用于 dominant_level1_hubs"""
    MAINLINE = "mainline"
    AXIS = "axis"


# ==================== 嵌套模型定义 ====================

class SecondaryAlignment(BaseModel):
    """次挂对齐信息模型"""
    axis_level1: Optional[AxisLevel1] = Field(None, description="大概念轴一级节点（仅axis_alignment使用）")
    axis_level2: Optional[AxisLevel2] = Field(None, description="大概念轴二级节点（仅axis_alignment使用）")
    mainline_level1: Optional[MainlineLevel1] = Field(None, description="主线网一级节点（仅mainline_alignment使用）")
    mainline_level2: Optional[MainlineLevel2] = Field(None, description="主线网二级节点（仅mainline_alignment使用）")
    boundary_reason: str = Field(..., description="触发次挂的语境边界说明")


class AlignmentReason(BaseModel):
    """对齐理由模型"""
    hit_rules: List[str] = Field(..., description="命中规则列表，至少包含判别A和判别B")
    exclude_reason: str = Field(..., description="排除最易混淆节点的理由")


class EvidenceAnchors(BaseModel):
    """双锚证据模型"""
    anchor_A_normative: List[str] = Field(..., description="规范性表述证据锚点列表")
    anchor_B_mechanism_or_definition: List[str] = Field(..., description="机制/定义/细节证据锚点列表")
    missing_anchor_B_note: str = Field(..., description="若缺anchor_B，说明原因；否则为'none'")


class TypeAlignment(BaseModel):
    """知识点类型对齐模型"""
    primary_level1: KnowledgeTypeLevel1 = Field(..., description="知识点类型一级主挂")
    primary_level2: KnowledgeTypeLevel2 = Field(..., description="知识点类型二级主挂")
    secondary_level2: List[KnowledgeTypeLevel2] = Field(default=[], description="知识点类型二级次挂列表")
    reason: AlignmentReason = Field(..., description="类型对齐的理由和排除理由")


class AxisAlignment(BaseModel):
    """大概念轴对齐模型"""
    primary_level1: AxisLevel1 = Field(..., description="大概念轴一级主挂")
    primary_level2: AxisLevel2 = Field(..., description="大概念轴二级主挂")
    secondary_level2: List[SecondaryAlignment] = Field(default=[], description="大概念轴二级次挂列表")
    reason: AlignmentReason = Field(..., description="大概念轴对齐的理由和排除理由")


class MainlineAlignment(BaseModel):
    """主线网对齐模型"""
    primary_level1: MainlineLevel1 = Field(..., description="主线网一级主挂")
    primary_level2: MainlineLevel2 = Field(..., description="主线网二级主挂")
    secondary_level2: List[SecondaryAlignment] = Field(default=[], description="主线网二级次挂列表")
    role_function: RoleFunction = Field(..., description="知识点在推理链中的功能角色")
    bridge_explanation: str = Field(..., description="串联说明：如何连接其他知识点形成推理链")
    evidence_anchors: EvidenceAnchors = Field(..., description="双锚证据信息")


class FrameworkAlignmentItem(BaseModel):
    """单条知识点的框架对齐信息模型"""
    code: str = Field(..., description="知识点代码")
    name: str = Field(..., description="知识点名称")
    type_alignment: TypeAlignment = Field(..., description="知识点类型对齐信息")
    axis_alignment: AxisAlignment = Field(..., description="大概念轴对齐信息")
    mainline_alignment: MainlineAlignment = Field(..., description="主线网对齐信息")
    confidence: ConfidenceLevel = Field(..., description="对齐置信度")
    missing_info_note: str = Field(..., description="纠偏说明/证据不足说明/需要补充的文本位置")


class MainlineRelation(BaseModel):
    """完整的输出JSON结构模型"""
    table2_framework_alignment: List[FrameworkAlignmentItem] = Field(..., description="框架对齐信息列表")


"""
知识点关联
"""


# ==================== 枚举定义 ====================

class LinkingPrinciple(str, Enum):
    """图谱关联原则枚举，对应 graph_linking_principles_used 字段"""
    KG1 = "KG1"
    KG2 = "KG2"
    KG3 = "KG3"
    KG4 = "KG4"
    KG5 = "KG5"


class RelationLevel1(str, Enum):
    """一级关系类型枚举"""
    SEMANTIC_SAME = "语义同一/近义复述"
    SUPER_SUB = "上位-下位"
    PART_WHOLE = "组成-整体"
    CAUSE_EFFECT = "前因-后果"
    CONDITION_CONCLUSION = "条件-结论"
    PRINCIPLE_MEASURE = "原则-措施"
    SYSTEM_PROCEDURE_SUBJECT = "制度-程序-主体职责"
    COMPARISON_CONFUSION = "对比辨析/易混干扰"
    MAINLINE_MIGRATION = "同主线迁移"
    AXIS_MIGRATION = "同轴迁移"


class RelationLevel2(str, Enum):
    """二级关系方向/位置枚举"""
    # 语义同一/近义复述
    SYNONYM = "同义"
    NEAR_SYNONYM = "近义"
    TERM_ALIGNMENT = "口径统一(术语对齐)"

    # 上位-下位
    SUPERORDINATE = "上位"
    SUBORDINATE = "下位"

    # 组成-整体
    WHOLE = "整体"
    PART = "部分"

    # 前因-后果
    CAUSE = "原因"
    EFFECT = "结果"

    # 条件-结论
    CONDITION = "条件"
    CONCLUSION = "结论"

    # 原则-措施
    PRINCIPLE = "原则"
    MEASURE = "措施"

    # 制度-程序-主体职责
    SYSTEM_FRAMEWORK = "制度框架"
    PROCEDURE_NODE = "程序节点"
    SUBJECT_RESPONSIBILITY = "主体职责"
    SUPERVISION_CONSTRAINT = "监督约束"

    # 对比辨析/易混干扰
    CONCEPT_CONFUSION = "概念混淆"
    SUBJECT_CONFUSION = "主体混淆"
    PROCEDURE_CONFUSION = "程序混淆"
    CONDITION_CONFUSION = "条件混淆"
    CAUSAL_REVERSAL = "因果倒置"
    SCOPE_EXPANSION = "范围扩大/缩小"

    # 同主线迁移
    SAME_SUBLINE_MIGRATION = "同二级subline迁移"
    CROSS_SUBLINE_MIGRATION = "跨二级subline迁移（但同一级主线）"

    # 同轴迁移
    SAME_THEME_MIGRATION = "同二级主题簇迁移"
    CROSS_THEME_MIGRATION = "跨二级主题簇迁移（但同一级轴）"


class RelationStrength(str, Enum):
    """关系强度枚举"""
    STRONG = "strong"
    MEDIUM = "medium"
    WEAK = "weak"


class UseValue(str, Enum):
    """关系使用价值枚举"""
    GRAPH_RETRIEVAL_AGGREGATION = "图谱检索聚合"
    REASONING_CHAIN_COMPLETION = "推理链补全"
    CROSS_GRADE_MIGRATION_REVIEW = "跨年级迁移复习"
    COMPREHENSIVE_QUESTION_BRIDGING = "综合题搭桥"
    CHOICE_QUESTION_INTERFERENCE = "选择题干扰项辨析"
    MATERIAL_QUESTION_MEASURE_MIGRATION = "材料题措施迁移"


class GapType(str, Enum):
    """知识缺口类型枚举，用于 derived_associated_knowledge"""
    SUBJECT = "主体"
    PROCEDURE = "程序"
    CONDITION = "条件"
    MECHANISM = "机制"
    EVALUATION_CRITERIA = "评价口径"
    TERMINOLOGY_CRITERIA = "术语口径"
    BOUNDARY_COUNTEREXAMPLE = "边界反例"


class SignalType(str, Enum):
    """材料信号类型枚举"""
    POLICY_TOOL = "政策工具"
    SUBJECT_BEHAVIOR = "主体行为"
    SYSTEM_PROCEDURE = "制度程序"
    SUPERVISION_ACCOUNTABILITY = "监督问责"
    RIGHTS_REMEDY = "权利救济"
    DISTRIBUTION_DATA = "分配数据"
    DEVELOPMENT_INDICATOR = "发展指标"
    CULTURAL_PUBLIC_OPINION = "文化舆论"
    INTERNATIONAL_EXPRESSION = "国际表述"
    CONFLICT_CONTRADICTION = "矛盾冲突"


class CallOrderType(str, Enum):
    """调用顺序类型枚举"""
    PRECONDITION = "前提"
    BRIDGE = "桥"
    CONCLUSION = "落点"
    METHODOLOGY = "方法论"


class PointRole(str, Enum):
    """知识点在联合调用中的角色枚举"""
    PRECONDITION = "前提"
    BRIDGE = "桥"
    CONCLUSION = "落点"
    METHODOLOGY = "方法论"


class QuestionType(str, Enum):
    """设问类型枚举"""
    CAUSE = "原因"
    SIGNIFICANCE = "意义"
    MEASURE = "措施"
    EVALUATION = "评析"
    ENLIGHTENMENT = "启示"
    COUNTERMEASURE_DESIGN = "对策设计"


# ==================== 嵌套模型定义 ====================

class MetaInfo(BaseModel):
    """元信息模型"""
    section_title: str = Field(..., description="小节名称")


class CurrentKP(BaseModel):
    """当前知识点模型"""
    code: str = Field(..., description="知识点代码")
    name: str = Field(..., description="知识点名称")


class RelationInfo(BaseModel):
    """关系信息模型"""
    level1: RelationLevel1 = Field(..., description="一级关系类型")
    level2: RelationLevel2 = Field(..., description="二级关系方向/位置")


class Evidence(BaseModel):
    """证据模型"""
    current: List[str] = Field(..., description="当前知识点的证据短语列表")
    linked: List[str] = Field(..., description="关联知识点的证据短语列表")


class ExternalRelation(BaseModel):
    """外部关系边模型"""
    linked_code: str = Field(..., description="关联知识点的代码")
    linked_name: str = Field(..., description="关联知识点的名称")
    relation: RelationInfo = Field(..., description="关系信息")
    strength: RelationStrength = Field(..., description="关系强度")
    match_rationale: str = Field(..., description="匹配理由，必须点明限定词/主体/程序/机制链/价值口径如何对应")
    evidence: Evidence = Field(..., description="双点证据")
    use_value: List[UseValue] = Field(..., description="使用价值列表")


class AssociatedKnowledge(BaseModel):
    """关联衍生知识模型"""
    gap_type: GapType = Field(..., description="知识缺口类型")
    text: str = Field(..., description="衍生知识文本")
    from_linked_code: str = Field(..., description="来源关联知识点的代码")
    why_derived: str = Field(..., description="为何衍生，补全current_kp的哪一类缺口")
    boundary: str = Field(..., description="适用材料语境/适用范围")


class MaterialSignal(BaseModel):
    """材料信号模型"""
    signal_type: SignalType = Field(..., description="信号类型")
    signal_keywords: List[str] = Field(..., description="信号关键词列表")
    call_points: List[str] = Field(..., description="调用知识点列表，必须包含current_kp和至少一个linked_code")
    call_order: List[str] = Field(..., description="调用顺序，格式为'角色:描述'")
    why: str = Field(..., description="为何这些信号触发这些点")


class IncludedPoint(BaseModel):
    """包含的知识点模型"""
    code: str = Field(..., description="知识点代码")
    name: str = Field(..., description="知识点名称")
    role: PointRole = Field(..., description="知识点在联合调用中的角色")


class JointSet(BaseModel):
    """联合知识包模型"""
    set_name: str = Field(..., description="知识包名称")
    included_points: List[IncludedPoint] = Field(..., description="包含的知识点列表，至少3个点")
    cross_grade_bridge: str = Field(..., description="跨年级衔接说明")
    reasoning_chain: List[str] = Field(..., description="推理链，格式为'A→B'")
    typical_questions: List[QuestionType] = Field(..., description="适配的设问类型列表")


class QuestionMigrationTemplate(BaseModel):
    """设问迁移模板模型"""
    question_type: QuestionType = Field(..., description="设问类型")
    template: str = Field(..., description="迁移模板")
    required_points: List[str] = Field(..., description="必须调用的知识点列表")
    scoring_skeleton: List[str] = Field(..., description="评分骨架，3-5条可给分短句")
    boundary_reminder: str = Field(..., description="边界提醒，避免常见错误")


class ConfusionPair(BaseModel):
    """混淆对模型"""
    a_code: str = Field(..., description="混淆知识点A的代码")
    b_code: str = Field(..., description="混淆知识点B的代码")


class Misconception(BaseModel):
    """易错点模型"""
    confusion_pair: ConfusionPair = Field(..., description="混淆对")
    wrong_claim: str = Field(..., description="错误表述")
    why_wrong: str = Field(..., description="为何错误")
    right_claim: str = Field(..., description="正确表述")
    boundary_conditions: str = Field(..., description="边界条件")
    trap_design_hint: str = Field(..., description="陷阱设计提示")


class DerivedMaterialSignalMap(BaseModel):
    """材料信号映射模型"""
    material_signals: List[MaterialSignal] = Field(..., description="材料信号列表")


class DerivedJointSets(BaseModel):
    """联合知识包集合模型"""
    joint_sets: List[JointSet] = Field(..., description="联合知识包列表")


class KnowledgeNetwork(BaseModel):
    """完整的知识图谱输出模型"""
    meta: MetaInfo = Field(..., description="元信息")
    current_kp: CurrentKP = Field(..., description="当前知识点")
    graph_linking_principles_used: List[LinkingPrinciple] = Field(..., description="使用的图谱关联原则列表")
    tableX_external_relations: List[ExternalRelation] = Field(..., description="外部关系边列表")
    derived_associated_knowledge: List[AssociatedKnowledge] = Field(..., description="关联衍生知识列表")
    derived_material_signal_map: DerivedMaterialSignalMap = Field(..., description="材料信号映射")
    derived_joint_sets_for_exam: DerivedJointSets = Field(..., description="考试联合知识包")
    derived_question_migration_templates: List[QuestionMigrationTemplate] = Field(..., description="设问迁移模板列表")
    derived_misconceptions_plus: List[Misconception] = Field(..., description="强化易错点列表")
    missing_match_note: str = Field(..., description="缺失匹配说明，若无匹配写原因、建议检索词、补库方向")
