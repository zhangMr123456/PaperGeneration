from typing import ClassVar, Literal
from pydantic import BaseModel
from typing import List

"""
知识点
"""


class Neo4jKnowledgePointNode(BaseModel):
    __label__: ClassVar[str] = "knowledge_point"

    """Neo4j 中的知识点节点"""
    code: str
    """唯一编码，作为节点 ID 和索引键"""
    name: str
    """可命题标题"""
    level: str
    """知识点层级：大概念|主题|知识点|易错点"""
    section_id: str
    """所属小节ID"""
    module: str
    """教材模块，如 HS-经社"""
    zone_id: str
    """教材分区 Z01/Z02..."""
    textbook_core_statement: str
    """核心教材陈述句"""

    # 用于全文检索或关键词匹配（可选）
    trigger_terms: List[str]
    """信号词列表，用于 Neo4j 全文索引或相似搜索"""

    # 时间戳（用于同步一致性）
    created_at: str  # ISO 8601
    updated_at: str  # ISO 8601


"""
主线关联
"""


class Neo4jFrameworkHubNode(BaseModel):
    """框架本体节点（类型/轴/主线 的二级节点）"""
    __rel_type__: ClassVar[str] = "framework_hub"

    framework_type: str  # "type", "axis", "mainline"
    level1: str  # 一级名称，如 "经济与发展"
    level2: str  # 二级名称，如 "高质量发展"
    description: str  # 可选描述（来自 Prompt 固定列表）


class Neo4jPrimaryAlignmentRel(BaseModel):
    """主挂关系（每条知识点有且仅有一条 per framework）"""
    __rel_type__: ClassVar[str] = "primary_alignment"

    from_code: str
    to_framework_type: Literal["type", "axis", "mainline"]
    to_level2: str
    # 无属性（主挂是确定性关系）


class Neo4jSecondaryAlignmentRel(BaseModel):
    """次挂关系（最多2条 per framework）"""
    __rel_type__: ClassVar[str] = "secondary_alignment"

    from_code: str
    to_framework_type: Literal["axis", "mainline"]  # type 一般无次挂
    to_level2: str
    boundary_reason: str  # 触发语境边界


"""
知识点关联
"""


class Neo4jKnowledgeRelationRel(BaseModel):
    """知识点之间的关系边"""
    from_code: str
    to_code: str
    level1: str  # RelationLevel1
    level2: str  # RelationLevel2
    strength: str  # "strong"/"medium"/"weak"
    match_rationale: str
    evidence_current: List[str]
    evidence_linked: List[str]
    use_value: List[str]

    class Config:
        neo4j_rel_type = "RELATED_TO"
