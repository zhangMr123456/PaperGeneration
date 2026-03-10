from enum import Enum


class SubjectEnum(str, Enum):
    """科目枚举"""
    CHINESE = "语文"
    MATH = "数学"
    ENGLISH = "英语"
    PHYSICS = "物理"
    CHEMISTRY = "化学"
    BIOLOGY = "生物"
    HISTORY = "历史"
    GEOGRAPHY = "地理"
    POLITICS = "政治"
    INFORMATION_TECH = "信息技术"
    GENERAL_TECH = "通用技术"
    OTHER_SUBJECT = "其他"


class GradeEnum(str, Enum):
    """年级枚举"""
    # 小学
    PRIMARY_1 = "小学一年级"
    PRIMARY_2 = "小学二年级"
    PRIMARY_3 = "小学三年级"
    PRIMARY_4 = "小学四年级"
    PRIMARY_5 = "小学五年级"
    PRIMARY_6 = "小学六年级"

    # 初中
    MIDDLE_1 = "初中一年级"
    MIDDLE_2 = "初中二年级"
    MIDDLE_3 = "初中三年级"

    # 高中
    HIGH_1 = "高中一年级"
    HIGH_2 = "高中二年级"
    HIGH_3 = "高中三年级"

    # 大学
    UNIVERSITY_1 = "大学一年级"
    UNIVERSITY_2 = "大学二年级"
    UNIVERSITY_3 = "大学三年级"
    UNIVERSITY_4 = "大学四年级"

    OTHER_GRADE = "其他"


class ProcessStageEnum(str, Enum):
    # 小学
    INIT = "初始化"
    PDF2MARKDOWN = "PDF转MARKDOWN"
    PARSE_TEXTBOOK_INFO = "解析课本"
    PARSE_OUTLINE = "解析大纲"

    # 政治
    PARSE_KNOWLEDGE = "解析知识点"


class OutlineStageEnum(str, Enum):
    # 小学
    DONE = "DONE"
    ERROR = "ERROR"
    NOT_DONE = "NOT_DONE"
