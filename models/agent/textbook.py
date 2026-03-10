from enum import Enum
from typing import List, Dict, Optional

from pydantic import BaseModel, Field

from core.custom_enum.textbook_enum import SubjectEnum, GradeEnum, OutlineStageEnum
from models.utils.snowflake import generator as snowflake_generator


class Outline(BaseModel):
    id: int = Field(
        default_factory=snowflake_generator.generate,
        description="ID",
    )
    document_context_id: int = Field(
        default=None,
        description="ID",
    )
    parent_id: Optional[int] = Field(
        default=None,
        description="ParentID",
    )
    title: str = Field(
        default="",
        description="当前大纲的名字",
    )
    page_index: int = Field(
        default=0,
        description="开始页码",
    )
    begin_line_index: int = Field(
        default=0,
        description="开始行数",
    )
    end_line_index: int = Field(
        default=0,
        description="结束行数",
    )
    # 子列表
    children: List["Outline"] = Field(
        default=[],
        description="结束行数",
    )
    extra: Dict = Field(
        default={},
        description="额外信息"
    )
    stage: OutlineStageEnum = Field(
        default=OutlineStageEnum.NOT_DONE,
        description="大纲状态"
    )


class Outlines(BaseModel):
    outlines: List[Outline] = Field(
        default=None,
        description="大纲"
    )


class DocTypeEnum(str, Enum):
    """文档类型枚举"""
    TEXTBOOK = "textbook"  # 教材
    EXAMINATION_PAPER = "examination_paper"  # 试卷
    TEXT_MATERIAL = "text_material"  # 文本资料
    OTHER_TYPE = "other"  # 其他


class ConfidenceEnum(str, Enum):
    """置信度枚举"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DocumentMetadata(BaseModel):
    """文档元数据模型"""
    subject: Optional[SubjectEnum] = Field(
        default=None,
        description="文档所属科目",
    )

    grade: Optional[GradeEnum] = Field(
        default=None,
        description="文档适用年级"
    )

    doc_type: Optional[DocTypeEnum] = Field(
        default=None,
        alias="type",
        description="文档类型"
    )

    confidence: Optional[ConfidenceEnum] = Field(
        default=None,
        description="判断置信度"
    )

    evidence: Optional[str] = Field(
        default=None,
        max_length=50,
        description="原文中支持判断的关键词或句子"
    )


class DocumentContext(Outlines, DocumentMetadata):
    id: int = Field(default_factory=snowflake_generator.generate, description="ID")
    file_name: str = Field(default=None, description="文件名字")
    file_md5: str = Field(default=None, description="文件的md5")
    user_id: int = Field(default=1, description="文件的md5")
    pdf_path: str = Field(
        default="",
        description="原始的PDF路径"
    )
    md_path: str = Field(
        default=None,
        description="Markdown路径"
    )
    stage: str = Field(
        default=None,
        description="当前阶段"
    )


class SubjectContext(BaseModel):
    document: DocumentContext = Field(default="大纲内容")
    outline: Outline = Field(default="大纲内容")
    section_title: str = Field(description="小结标题")
    section_text: str = Field(description="小结正文")
    knowledge: Optional[Dict] = Field(default=None, description="知识库信息")
