from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from models.utils.snowflake import generator as snowflake_generator


# ============= 枚举定义 (使用Enum类) =============

class KnowledgePointLevelEnum(str, Enum):
    """知识点层级枚举"""
    BIG_CONCEPT = "大概念"
    THEME = "主题"
    KNOWLEDGE_POINT = "知识点"
    COMMON_MISTAKE = "易错点"


class QuestionTypeEnum(str, Enum):
    """考题题型枚举"""
    SINGLE_CHOICE = "单选题"
    MULTIPLE_CHOICE = "多选题"
    TRUE_FALSE = "判断题"
    ANALYSIS = "辨析题"
    SHORT_ANSWER = "简答题"
    MATERIAL_ANALYSIS = "材料分析题"
    ESSAY = "论述题"


class AbilityFocusEnum(str, Enum):
    """能力层级枚举"""
    MEMORIZATION = "识记"
    UNDERSTANDING = "理解"
    APPLICATION = "应用"
    SYNTHESIS = "综合"
    EVALUATION = "评价"


# class HighFrequencyFormEnum(str, Enum):
#     """高频考题形式枚举"""
#     SIGNIFICANCE_CHOICE = "意义类选择题"
#     MEASURES_MATERIAL = "措施类材料题"
#     DISCRIMINATION_QUESTION = "辨析题"
#     ENLIGHTENMENT_SHORT_ANSWER = "启示类简答题"
#     COUNTERMEASURE_DESIGN = "对策设计题"
#     REASON_CHOICE = "原因类选择题"
#     COMMENTARY_DISSERTATION = "评析类论述题"
#     # ... 可根据需要继续添加


# ============= 核心模型定义 =============

class TeachingForLecture(BaseModel):
    """用于【讲授】讲清的结构化产物"""
    concept: str = Field(..., description="一句话核心定义或观点，力求精准、易懂。")
    mechanism_chain: List[str] = Field(..., description="机制链条，用箭头（→）展示至少两个关键环节的逻辑关系。")
    scenario_example: str = Field(..., description="一个源自教材或贴近教材的简例，用于课堂情境导入或说明。")


class ReviewForMemorization(BaseModel):
    """用于【复习】记牢的结构化产物"""
    core_statement: str = Field(..., description="需背诵的核心结论句（贴近教材原句）。")
    logical_hook: str = Field(..., description="可串联本知识点与其他知识点的逻辑钩子或记忆口诀。")
    high_frequency_forms: List[str] = Field(
        ...,
        min_items=2,
        max_items=2,
        description="本知识点最常出现的2种考题形式。"
    )


class AssessmentForQuestions(BaseModel):
    """用于【测评】命题的结构化产物"""
    question_types: List[QuestionTypeEnum] = Field(..., description="建议用于考查本知识点的具体题型。")
    ability_focus: AbilityFocusEnum = Field(..., description="题目主要考查的能力层级。")
    sample_question_stem: str = Field(..., description="一个贴近考情的示例题干的简要描述（无需写出完整选项或答案）。")


class ScoringForGrading(BaseModel):
    """用于【阅卷】给分的结构化产物"""
    key_scoring_points: List[str] = Field(
        ...,
        min_items=3,
        max_items=5,
        description="3-5条可独立给分的评分点短句。每条应包含具体行动、对象或条件。"
    )
    common_pitfalls: List[str] = Field(
        ...,
        min_items=1,
        max_items=2,
        description="阅卷时需重点关注的1-2个常见错误答法或混淆点。"
    )
    boundary_condition: str = Field(..., description="该评分点的适用前提或边界限制。")


class PoliticsKnowledgePoint(BaseModel):
    """最小可考知识点单元，包含完整的四用产物"""
    id: int = Field(default_factory=snowflake_generator.generate, description="ID")
    outline_id: Optional[int] = Field(
        default=0,
        description='大纲ID'
    )
    document_id: Optional[int] = Field(
        default=0,
        description='文档ID'
    )
    code: str = Field(
        description='格式为"{{学科}}-{{课本名称}}-{{段落序号}}-{{知识点序号}}"'
    )
    content: Optional[str] = Field(
        default="",
        description="段落正文内容"
    )
    name: str = Field(..., description="一句话可命题的知识点名称（如：××的含义/要求/实现路径）")
    level: KnowledgePointLevelEnum = Field(..., description="知识点层级")

    # 四用产物
    teaching_for_lecture: TeachingForLecture
    review_for_memorization: ReviewForMemorization
    assessment_for_questions: AssessmentForQuestions
    scoring_for_grading: ScoringForGrading

    evidence_sentences: List[str] = Field(
        ...,
        min_items=1,
        max_items=3,
        description="支撑该知识点的教材原句（1-3句）"
    )


class PoliticsKnowledgePointPackage(BaseModel):
    """整个知识点包的输出结构，对应最终的JSON数组"""
    knowledge_points: List[PoliticsKnowledgePoint]
