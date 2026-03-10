from typing import List, Dict, Any, Optional
import torch
from langchain_core.documents import Document
from langchain_community.vectorstores import Milvus
import logging

from langchain_core.runnables import RunnableConfig

from core.embedding.bge import BGEConfig
from core.embedding.bge.embedding import BGEEmbeddings
from core.embedding.bge.rerank import BGEReranker
from core.embedding.bge.retriever import BGEHybridRetriever

# 配置日志
logger = logging.getLogger(__name__)


class BGERAGFactory:
    """BGE RAG工厂类 - 集中管理组件创建"""

    @staticmethod
    def create_embeddings(config: Optional[BGEConfig] = None) -> BGEEmbeddings:
        """创建Embeddings"""
        if config is None:
            config = BGEConfig()
        return BGEEmbeddings(config)

    @staticmethod
    def create_reranker(config: Optional[BGEConfig] = None) -> BGEReranker:
        """创建Reranker"""
        if config is None:
            config = BGEConfig()
        return BGEReranker(config)

    @staticmethod
    def create_vector_store(
            embeddings: BGEEmbeddings,
            collection_name: str = "bge_rag",
            connection_args: Optional[Dict[str, Any]] = None
    ) -> Milvus:
        """创建Milvus向量存储"""
        if connection_args is None:
            connection_args = {
                "host": "localhost",
                "port": "19530"
            }

        return Milvus(
            embedding_function=embeddings,
            collection_name=collection_name,
            connection_args=connection_args,
            # 优化索引参数
            index_params={
                "metric_type": "IP",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            },
            search_params={
                "metric_type": "IP",
                "params": {"nprobe": 10}
            }
        )

    @staticmethod
    def create_retriever(
            vector_store: Milvus,
            reranker: BGEReranker,
            vector_top_k: int = 20,
            rerank_top_k: int = 5
    ) -> BGEHybridRetriever:
        """创建混合检索器"""
        return BGEHybridRetriever(
            vector_store=vector_store,
            reranker=reranker,
            vector_top_k=vector_top_k,
            rerank_top_k=rerank_top_k
        )


class BGERAGPipeline:
    """完整的BGE RAG流水线"""

    def __init__(
            self,
            embeddings: BGEEmbeddings,
            retriever: BGEHybridRetriever,
            llm: Any = None,  # LangChain LLM接口
            config: Optional[BGEConfig] = None
    ):
        self.embeddings = embeddings
        self.retriever = retriever
        self.llm = llm
        self.config = config or BGEConfig()

    def add_documents(self, documents: List[Document]) -> None:
        """添加文档到向量数据库"""
        try:
            # 直接使用vector_store的add_documents方法
            if hasattr(self.retriever.vector_store, 'add_documents'):
                self.retriever.vector_store.add_documents(documents)
                logger.info(f"Added {len(documents)} documents to vector store")
            else:
                # 备用方案：手动处理
                texts = [doc.page_content for doc in documents]
                metadatas = [doc.metadata for doc in documents]
                self.retriever.vector_store.add_texts(texts, metadatas)
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise

    def del_documents(self, ids) -> None:
        try:
            # 直接使用vector_store的add_documents方法
            self.retriever.vector_store.delete(ids=ids)
        except Exception as e:
            logger.error(f"Failed to del documents: {e}")
            raise

    def retrieve(self, query: str, config: RunnableConfig = None, **kwargs) -> List[Document]:
        """检索文档"""
        # return self.retriever.get_relevant_documents(query)
        return self.retriever.invoke(query, config, **kwargs)

    def rag_chain(self, query: str) -> Dict[str, Any]:
        """执行完整的RAG流程"""
        # 1. 检索
        retrieved_docs = self.retrieve(query)

        # 2. 构建上下文
        context = "\n\n".join([
            f"[文档 {i + 1}]: {doc.page_content}"
            for i, doc in enumerate(retrieved_docs)
        ])

        # 3. 生成提示
        prompt = f"""基于以下上下文，请回答问题：

        上下文：
        {context}

        问题：{query}

        请基于上下文提供准确、简洁的回答。如果上下文不包含相关信息，请说明无法回答。"""

        # 4. 调用LLM（如果配置了LLM）
        if self.llm:
            try:
                response = self.llm.invoke(prompt)
                answer = response.content if hasattr(response, 'content') else str(response)
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
                answer = "抱歉，生成回答时出现错误。"
        else:
            answer = "LLM未配置，仅返回检索结果。"

        # 5. 返回结果
        return {
            "query": query,
            "retrieved_documents": retrieved_docs,
            "context": context,
            "answer": answer
        }


# 使用示例
def create_bge_rag_system(
        llm: Any = None,
        collection_name: str = "bge_rag",
        connection_args: Optional[Dict[str, Any]] = None,
        config: Optional[BGEConfig] = None
) -> BGERAGPipeline:
    """创建BGE RAG系统的工厂函数"""

    # 1. 创建配置
    if config is None:
        config = BGEConfig()

    # 2. 创建组件
    embeddings = BGERAGFactory.create_embeddings(config)
    reranker = BGERAGFactory.create_reranker(config)
    vector_store = BGERAGFactory.create_vector_store(
        embeddings=embeddings,
        collection_name=collection_name,
        connection_args=connection_args
    )
    retriever = BGERAGFactory.create_retriever(
        vector_store=vector_store,
        reranker=reranker
    )

    # 3. 创建流水线
    pipeline = BGERAGPipeline(
        embeddings=embeddings,
        retriever=retriever,
        llm=llm,
        config=config
    )

    return pipeline


# 集成到LangChain RAG Chain的示例
def create_langchain_rag_chain(
        pipeline: BGERAGPipeline,
        llm: Any,
        prompt_template: Optional[str] = None
) -> Any:
    """创建标准的LangChain RAG Chain"""
    from langchain.chains import RetrievalQA
    from langchain.prompts import PromptTemplate

    if prompt_template is None:
        prompt_template = """使用以下上下文来回答最后的问题。如果你不知道答案，就说你不知道，不要试图编造答案。

        上下文：
        {context}

        问题：{question}
        回答："""

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )

    # 创建RetrievalQA链
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=pipeline.retriever,
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True
    )

    return qa_chain


# 错误处理装饰器
def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """重试装饰器"""
    import time
    from functools import wraps

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                    else:
                        raise

        return wrapper

    return decorator


# 配置验证
def validate_bge_config(config: Dict[str, Any]) -> BGEConfig:
    """验证并创建配置"""
    valid_models = {
        "embedding": ["BAAI/bge-large-zh-v1.5", "BAAI/bge-base-zh-v1.5"],
        "reranker": ["BAAI/bge-reranker-v2-m3", "BAAI/bge-reranker-base"]
    }

    embedding_model = config.get("embedding_model", "BAAI/bge-large-zh-v1.5")
    reranker_model = config.get("reranker_model", "BAAI/bge-reranker-v2-m3")

    if embedding_model not in valid_models["embedding"]:
        logger.warning(f"Unsupported embedding model: {embedding_model}")

    if reranker_model not in valid_models["reranker"]:
        logger.warning(f"Unsupported reranker model: {reranker_model}")

    return BGEConfig(**config)
