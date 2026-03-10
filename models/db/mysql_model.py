from datetime import datetime

from sqlalchemy import Column, Integer, BigInteger, String, Text, TIMESTAMP, Index, func, select, \
    DateTime, JSON, UniqueConstraint, TEXT
from sqlalchemy.orm import declarative_base, validates
from sqlalchemy.dialects.mysql import ENUM
from core.custom_enum.textbook_enum import SubjectEnum, GradeEnum, ProcessStageEnum, OutlineStageEnum
from models.agent.knowledge_point import KnowledgePointLevelEnum
from models.utils.snowflake import generator as snowflake_generator

Base = declarative_base()


class DocumentContext(Base):
    """文档上下文表"""
    __tablename__ = 'document_context'

    id = Column(BigInteger().with_variant(Integer, "mysql"), primary_key=True,
                default=lambda: snowflake_generator.generate(), comment='主键ID')
    file_name = Column(String(1000), nullable=False, default=None, comment='文件名字')
    file_md5 = Column(String(200), nullable=False, default=None, comment='文件MD5')
    pdf_path = Column(String(1000), nullable=True, default=None, comment='PDF文件路径')
    md_path = Column(String(1000), nullable=True, default=None, comment='Markdown文件路径')
    stage = Column(String(100), ENUM(ProcessStageEnum), nullable=True, default=None, comment='处理阶段')
    subject = Column(String(100), ENUM(SubjectEnum), nullable=True, default=None,
                     comment='科目: 语文,数学,英语,物理,化学,生物,历史,地理,政治,信息技术,通用技术,其他')
    user_id = Column(BigInteger().with_variant(Integer, "mysql"), comment='主键ID')
    grade = Column(String(20), ENUM(GradeEnum), nullable=True, default=None,
                   comment='年级: 小学一年级到大学四年级,其他')

    doc_type = Column(String(20), nullable=True, default=None,
                      comment='文档类型: textbook,examination_paper,text_material,other')
    confidence = Column(String(10), nullable=True, default=None, comment='置信度: high,medium,low')
    evidence = Column(String(50), nullable=True, default=None, comment='判断证据')
    # 时间戳字段
    created_at = Column(TIMESTAMP, nullable=True, server_default=func.current_timestamp(), comment='创建时间')
    updated_at = Column(TIMESTAMP, nullable=True, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp(), comment='更新时间')

    __table_args__ = (
        Index('idx_subject_grade', 'subject', 'grade'), Index('idx_doc_type', 'doc_type'),
        Index('idx_confidence', 'confidence'), Index('idx_created_at', 'created_at'),
        Index('idx_updated_at', 'updated_at'),
        Index('idx_paths', pdf_path, md_path, mysql_length={'pdf_path': 200, 'md_path': 200}), {
            'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci',
            'mysql_row_format': 'DYNAMIC', 'comment': '文档上下文表'
        }
    )

    def __repr__(self):
        return f"<DocumentContext(id={self.id}, subject='{self.subject}', grade='{self.grade}')>"


class Outline(Base):
    """大纲表"""
    __tablename__ = 'outline'

    # 主键字段
    id = Column(BigInteger().with_variant(Integer, "mysql"), primary_key=True,
                default=lambda: snowflake_generator.generate(), comment='大纲ID')
    # 外键字段（无外键约束，仅逻辑关联）
    document_context_id = Column(BigInteger().with_variant(Integer, "sqlite"), nullable=False,
                                 comment='关联的文档上下文ID')
    # 大纲内容字段
    title = Column(String(500), nullable=False, default=None, comment='大纲标题')
    page_index = Column(Integer, nullable=False, default=None, comment='开始页码')
    begin_line_index = Column(Integer, nullable=False, default=None, comment='开始行索引')
    end_line_index = Column(Integer, nullable=False, default=None, comment='结束行索引')
    # 层级结构字段
    parent_id = Column(BigInteger().with_variant(Integer, "mysql"), nullable=True, default=None, comment='父级大纲ID')
    extra = Column(JSON, nullable=True, comment="额外信息")
    stage = Column(String(500), ENUM(OutlineStageEnum), nullable=False, default=None, comment='大纲标题')
    # 时间戳字段
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), comment='创建时间')
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp(), comment='更新时间')
    # 索引
    __table_args__ = (
        Index('idx_document_context', 'document_context_id'), Index('idx_parent', 'parent_id'),
        Index('idx_created', 'created_at'),
        Index('ft_title', title, mysql_prefix='FULLTEXT'),
        {
            'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci',
            'mysql_row_format': 'DYNAMIC', 'comment': '大纲表'
        }
    )

    # 验证器
    @validates('title')
    def validate_title(self, key, title):
        if len(title) > 500:
            raise ValueError("Title must be less than 500 characters")
        return title

    @validates('page_index', 'begin_line_index', 'end_line_index')
    def validate_indices(self, key, value):
        if value < 0:
            raise ValueError(f"{key} must be non-negative")
        return value

    @property
    def is_root(self):
        """是否为根节点"""
        return self.parent_id is None or self.parent_id == 0

    @property
    def page_range(self):
        """获取页码范围文本"""
        if self.begin_line_index == self.end_line_index:
            return f"Page {self.page_index}, Line {self.begin_line_index}"
        return f"Page {self.page_index}, Lines {self.begin_line_index}-{self.end_line_index}"

    # 类方法
    @classmethod
    def get_tree_query(cls, document_context_id=None):
        """获取树形查询"""
        # 基础查询
        query = select([cls]).order_by(cls.document_context_id, cls.begin_line_index)

        if document_context_id:
            query = query.where(cls.document_context_id == document_context_id)

        return query

    def __repr__(self):
        return f"<Outline(id={self.id}, title='{self.title[:30]}...', level={self.level})>"


"""
知识库
"""


class KnowledgePoint(Base):
    """
    最小可考知识点单元，包含完整的四用产物
    对应表: knowledge_point
    """
    __tablename__ = 'knowledge_point'

    # 主键和基础信息
    id = Column(BigInteger().with_variant(Integer, "mysql"), primary_key=True,
                default=lambda: snowflake_generator.generate(), comment='知识点ID')
    outline_id = Column(BigInteger().with_variant(Integer, "mysql"), nullable=True, comment='大纲ID')
    document_id = Column(BigInteger().with_variant(Integer, "mysql"), nullable=True, comment='文档ID')
    code = Column(String(100), nullable=False, comment='格式为"{{学科}}-{{课本名称}}-{{段落序号}}-{{知识点序号}}"')
    name = Column(String(200), nullable=False, comment='一句话可命题的知识点名称（如：××的含义/要求/实现路径）')
    level = Column(
        ENUM(KnowledgePointLevelEnum),
        nullable=False,
        comment='知识点层级'
    )
    content = Column(TEXT, nullable=False, comment='段落正文内容')

    # 四用产物 - 使用JSON存储嵌套结构
    teaching_for_lecture = Column(JSON, nullable=False, comment='教学用讲稿')
    review_for_memorization = Column(JSON, nullable=False, comment='复习用记忆材料')
    assessment_for_questions = Column(JSON, nullable=False, comment='考评用试题')
    scoring_for_grading = Column(JSON, nullable=False, comment='评分用标准')

    # 数组字段使用JSON存储
    evidence_sentences = Column(JSON, nullable=False, comment='支撑该知识点的教材原句（1-3句）')

    # 元数据
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment='创建时间')
    updated_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment='更新时间'
    )

    # 表级约束和索引
    __table_args__ = (
        # 唯一约束
        UniqueConstraint('code', name='uk_code'),

        # 索引
        Index('idx_outline_id', 'document_id', 'outline_id'),
        Index('idx_code', 'code'),
        Index('idx_level', 'level'),
        # 表选项
        {
            'comment': '最小可考知识点单元，包含完整的四用产物',
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_unicode_ci'
        }
    )

    def __repr__(self):
        return f"<KnowledgePoint(id={self.id}, code='{self.code}', name='{self.name}', level={self.level})>"


"""
关联
"""


class KnowledgeNetwork(Base):
    """
    最小可考知识点单元，包含完整的四用产物
    对应表: knowledge_point
    """
    __tablename__ = 'knowledge_network'

    # 主键和基础信息
    id = Column(Integer, primary_key=True, autoincrement=True, comment='知识点ID')
    knowledge_point_id = Column(Integer, nullable=True, comment='大纲ID')
    # 四用产物 - 使用JSON存储嵌套结构
    relation = Column(JSON, nullable=False, comment='关系信息')

    # 表级约束和索引
    __table_args__ = (
        # 唯一约束
        Index('idx_knowledge_point_id', 'knowledge_point_id'),
        # 表选项
        {
            'comment': '知识点关系信息',
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_unicode_ci'
        }
    )

    def __repr__(self):
        return f"<KnowledgeNetwork(id={self.id}, knowledge_point_id='{self.knowledge_point_id}')>"
