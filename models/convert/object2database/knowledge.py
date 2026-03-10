from models.db.mysql_model import KnowledgePoint as KnowledgePointDO
from models.agent.knowledge_point import PoliticsKnowledgePoint as KnowledgePointBO


def convert_bo_to_do(knowledge_point_bo: KnowledgePointBO) -> KnowledgePointDO:
    """
    将Pydantic模型转换为SQLAlchemy兼容的字典
    返回字典用于创建或更新SQLAlchemy对象
    """
    # 将Pydantic模型转换为字典
    data = knowledge_point_bo.dict()

    # 处理嵌套对象为JSON
    # if hasattr(knowledge_point_bo.teaching_for_lecture, 'dict'):
    #     data['teaching_for_lecture'] = knowledge_point_bo.teaching_for_lecture.dict()
    # if hasattr(knowledge_point_bo.review_for_memorization, 'dict'):
    #     data['review_for_memorization'] = knowledge_point_bo.review_for_memorization.dict()
    # if hasattr(knowledge_point_bo.assessment_for_questions, 'dict'):
    #     data['assessment_for_questions'] = knowledge_point_bo.assessment_for_questions.dict()
    # if hasattr(knowledge_point_bo.scoring_for_grading, 'dict'):
    #     data['scoring_for_grading'] = knowledge_point_bo.scoring_for_grading.dict()

    return KnowledgePointDO(**data)


# 可选：更简洁的转换函数（如果只需要从DO到BO的转换）
def convert(knowledge_point_bo: KnowledgePointBO) -> KnowledgePointDO:
    """
    简洁版的转换函数（与您提供的格式一致）
    """
    return convert_bo_to_do(knowledge_point_bo)


# 可选：批量转换函数
def convert_list(bo_list) -> list[KnowledgePointDO]:
    """
    批量转换SQLAlchemy对象列表为Pydantic对象列表
    """
    return [convert_bo_to_do(bo) for bo in bo_list]