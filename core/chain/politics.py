from langchain_core.prompts import ChatPromptTemplate
from core.llm.qwen import llm
from core.parser.format_json import CleanPydanticOutputParser

from core.prompts.politics import KNOWLEDGE_POINTS_PROMPT, MAINLINE_ALIGNMENT_PROMPT, KNOWLEDGE_NETWORK_PROMPT
from models.agent.knowledge_point import PoliticsKnowledgePointPackage
from models.agent.politics import MainlineRelation, KnowledgeNetwork


"""
提取知识点
"""
knowledge_points_parser = CleanPydanticOutputParser(pydantic_object=PoliticsKnowledgePointPackage)
knowledge_points_prompt = ChatPromptTemplate.from_template(KNOWLEDGE_POINTS_PROMPT)
knowledge_points_chain = knowledge_points_prompt | llm | knowledge_points_parser  # 组合Prompt+LLM+输出解析


"""
主线关联提取
"""
mainline_parser = CleanPydanticOutputParser(pydantic_object=MainlineRelation)
mainline_prompt = ChatPromptTemplate.from_template(MAINLINE_ALIGNMENT_PROMPT)
mainline_chain = mainline_prompt | llm | mainline_parser  # 组合Prompt+LLM+输出解析

"""
知识点关联提取
"""

knowledge_network_parser = CleanPydanticOutputParser(pydantic_object=KnowledgeNetwork)
knowledge_network_prompt = ChatPromptTemplate.from_template(KNOWLEDGE_NETWORK_PROMPT)
knowledge_network_chain = knowledge_network_prompt | llm | knowledge_network_parser  # 组合Prompt+LLM+输出解析

