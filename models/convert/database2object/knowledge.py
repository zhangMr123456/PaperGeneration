import json

from models.db.mysql_model import KnowledgePoint as KnowledgePointDO
from models.agent.knowledge_point import PoliticsKnowledgePoint as KnowledgePointBO


def convert_do_to_bo(knowledge_point_do: KnowledgePointDO) -> KnowledgePointBO:
    """
    将SQLAlchemy模型转换为Pydantic模型
    """
    # 处理JSON字段的反序列化
    teaching_for_lecture = knowledge_point_do.teaching_for_lecture
    review_for_memorization = knowledge_point_do.review_for_memorization
    assessment_for_questions = knowledge_point_do.assessment_for_questions
    scoring_for_grading = knowledge_point_do.scoring_for_grading
    evidence_sentences = knowledge_point_do.evidence_sentences

    # 如果字段是字符串，解析为JSON
    if isinstance(teaching_for_lecture, str):
        teaching_for_lecture = json.loads(teaching_for_lecture)
    if isinstance(review_for_memorization, str):
        review_for_memorization = json.loads(review_for_memorization)
    if isinstance(assessment_for_questions, str):
        assessment_for_questions = json.loads(assessment_for_questions)
    if isinstance(scoring_for_grading, str):
        scoring_for_grading = json.loads(scoring_for_grading)
    if isinstance(evidence_sentences, str):
        evidence_sentences = json.loads(evidence_sentences)

    # 创建Pydantic对象
    knowledge_point_bo = KnowledgePointBO(
        id=knowledge_point_do.id,
        outline_id=knowledge_point_do.outline_id,
        document_id=knowledge_point_do.document_id,
        code=knowledge_point_do.code,
        name=knowledge_point_do.name,
        content=knowledge_point_do.content,
        level=knowledge_point_do.level,
        teaching_for_lecture=teaching_for_lecture,
        review_for_memorization=review_for_memorization,
        assessment_for_questions=assessment_for_questions,
        scoring_for_grading=scoring_for_grading,
        evidence_sentences=evidence_sentences,
        created_at=knowledge_point_do.created_at,
        updated_at=knowledge_point_do.updated_at,
    )
    return knowledge_point_bo


# 可选：更简洁的转换函数（如果只需要从DO到BO的转换）
def convert(knowledge_point_do) -> KnowledgePointBO:
    """
    简洁版的转换函数（与您提供的格式一致）
    """
    return convert_do_to_bo(knowledge_point_do)


# 可选：批量转换函数
def convert_list(do_list) -> list[KnowledgePointBO]:
    """
    批量转换SQLAlchemy对象列表为Pydantic对象列表
    """
    return [convert_do_to_bo(do) for do in do_list]
