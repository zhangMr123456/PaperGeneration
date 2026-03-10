from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from core.llm.qwen import llm
from core.prompts.outline import OUTLINE_PROMPT

from core.prompts.textbook import TEXTBOOK_PROMPT
from models.agent.textbook import DocumentMetadata, Outlines

"""
课本信息的解析
"""
document_parser = PydanticOutputParser(pydantic_object=DocumentMetadata)
textbook_prompt = ChatPromptTemplate.from_template(TEXTBOOK_PROMPT)
textbook_info_chain = textbook_prompt | llm | document_parser  # 组合Prompt+LLM+输出解析

"""
课本大纲的解析
"""
outline_parser = PydanticOutputParser(pydantic_object=Outlines)
outline_prompt = ChatPromptTemplate.from_template(OUTLINE_PROMPT)
textbook_outline_chain = outline_prompt | llm | outline_parser  # 组合Prompt+LLM+输出解析

if __name__ == '__main__':
    textbook_info_chain.invoke({"input_text": "test"})  # 输出完整故事文本
