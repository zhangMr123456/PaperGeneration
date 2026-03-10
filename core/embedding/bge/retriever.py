from typing import List, Optional, Dict, Any
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_community.vectorstores import Milvus
import logging

from core.embedding.bge.rerank import BGEReranker

logger = logging.getLogger(__name__)


class BGEHybridRetriever(BaseRetriever):
    """BGE混合检索器 - LangChain兼容"""
    vector_store: Milvus
    reranker: BGEReranker
    vector_top_k: int
    rerank_top_k: int

    # def __init__(
    #         self,
    #         vector_store: Milvus,
    #         reranker: BGEReranker,
    #         vector_top_k: int = 20,
    #         rerank_top_k: int = 5
    # ):
    #     super().__init__()
    #     self.vector_store = vector_store
    #     self.reranker = reranker
    #     self.vector_top_k = vector_top_k
    #     self.rerank_top_k = rerank_top_k

    def _get_relevant_documents(
            self,
            query: str,
            *,
            run_manager: CallbackManagerForRetrieverRun,
            expr: str = None,
    ) -> List[Document]:
        """核心检索方法"""
        # 第一步：向量检索
        print("expr: ", expr)
        try:
            vector_docs = self.vector_store.similarity_search(
                query=query,
                k=self.vector_top_k,
                expr=expr
            )
            logger.info(f"Vector search retrieved {len(vector_docs)} documents")
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

        # 第二步：重排序
        if vector_docs and self.rerank_top_k > 0:
            try:
                reranked_docs = self.reranker.rerank(
                    query=query,
                    documents=vector_docs,
                    top_k=self.rerank_top_k
                )
                logger.info(f"Reranker returned {len(reranked_docs)} documents")
                return reranked_docs
            except Exception as e:
                logger.error(f"Reranking failed: {e}, returning vector results")
                return vector_docs[:self.rerank_top_k]

        return vector_docs[:self.rerank_top_k]

    async def _aget_relevant_documents(
            self,
            query: str,
            *,
            run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """异步检索方法"""
        # 简化的异步实现，实际生产环境需要完整异步支持
        return self._get_relevant_documents(query, run_manager=run_manager)
