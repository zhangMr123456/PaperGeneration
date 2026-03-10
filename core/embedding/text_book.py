# 示例用法
import json
import logging

import torch
from langchain_core.documents import Document

from conf.settings import MILVUS_URI
from core.embedding.bge import BGEConfig
from core.embedding.bge.util import create_bge_rag_system
from models.agent.knowledge_point import PoliticsKnowledgePoint

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 创建配置
config = BGEConfig(
    device="cuda" if torch.cuda.is_available() else "cpu"
)
# 创建RAG系统
pipeline = create_bge_rag_system(
    collection_name="knowledge",
    config=config,
    connection_args={
        "uri": MILVUS_URI
    },
)

logger.info("BGE RAG system initialized successfully")


def knowledge_point2embedding(knowledge_point: PoliticsKnowledgePoint):
    content = f"""
    【知识点】{knowledge_point.name}
    【层级】{knowledge_point.level}
    【学科代码】{knowledge_point.code}

    【核心内容】
    {knowledge_point.content}

    【四用摘要】
    - 教学应用：{knowledge_point.teaching_for_lecture.concept}
    - 复习要点：{knowledge_point.review_for_memorization.core_statement}
    - 考查方向：{knowledge_point.assessment_for_questions.question_types}
    - 评分标准：{knowledge_point.scoring_for_grading.key_scoring_points}

    【证据句】
    {'; '.join(knowledge_point.evidence_sentences)}
    """
    metadata = knowledge_point.dict()
    metadata["evidence_sentences"] = json.dumps(metadata["evidence_sentences"])
    return Document(
        page_content=content,
        metadata=metadata,
        id=knowledge_point.id,
    )


if __name__ == "__main__":
    # 示例用法
    import sys

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建配置
    config = BGEConfig(
        device="cuda" if torch.cuda.is_available() else "cpu"
    )

    try:
        # 创建RAG系统
        pipeline = create_bge_rag_system(
            collection_name="test_rag",
            config=config
        )

        logger.info("BGE RAG system initialized successfully")

        # 示例文档
        documents = [
            Document(
                page_content="机器学习是人工智能的一个分支",
                metadata={"source": "wiki"},
                id="1",
            ),
            Document(
                page_content="深度学习是机器学习的一个子领域",
                metadata={"source": "wiki1"},
                id="2",
            )
        ]

        # 添加文档
        pipeline.add_documents(documents)

        # 查询
        query = "什么是机器学习？"
        # result = pipeline.retrieve("", expr='source == "wiki1"')
        result = pipeline.retrieve("", expr='pk == "3"')

        pipeline.del_documents(["1", "2"])

        print(f"查询: {query}")
        print(f"检索到 {len(result)} 个文档")
        for i, doc in enumerate(result):
            print(f"\n文档 {i + 1}:")
            print(f"内容: {doc.page_content[:100]}...")
            print(f"元数据: {doc.metadata}")

    except Exception as e:
        raise
