from typing import List
import torch
from langchain_core.documents import Document
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import logging

from core.embedding.bge import BGEConfig

logger = logging.getLogger(__name__)


class BGEReranker:
    """BGE Reranker模型 - 独立模块"""

    def __init__(self, config: BGEConfig):
        self.config = config
        self.device = config.device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._init_model()

    def _init_model(self):
        """初始化reranker模型"""
        logger.info(f"Loading BGE reranker model: {self.config.reranker_model}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.config.reranker_model)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.config.reranker_model
        )
        self.model.to(self.device)
        self.model.eval()
        logger.info(f"Reranker model loaded on {self.device}")

    def compute_scores(
            self,
            query: str,
            documents: List[str]
    ) -> List[float]:
        """计算相关性分数"""
        scores = []

        with torch.no_grad():
            for doc in documents:
                inputs = self.tokenizer.encode_plus(
                    query,
                    doc,
                    max_length=self.config.max_length,
                    padding=True,
                    truncation=True,
                    return_tensors='pt'
                )

                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                outputs = self.model(**inputs)
                score = torch.sigmoid(outputs.logits).item()
                scores.append(score)

        return scores

    def rerank(
            self,
            query: str,
            documents: List[Document],
            top_k: int = 5
    ) -> List[Document]:
        """对文档进行重排序"""
        if not documents:
            return []

        # 提取文档内容
        doc_texts = [doc.page_content for doc in documents]
        scores = self.compute_scores(query, doc_texts)

        # 为文档添加分数元数据
        scored_docs = []
        for doc, score in zip(documents, scores):
            new_doc = Document(
                page_content=doc.page_content,
                metadata={**doc.metadata, "rerank_score": score}
            )
            scored_docs.append(new_doc)

        # 按分数排序
        scored_docs.sort(key=lambda x: x.metadata.get("rerank_score", 0), reverse=True)

        return scored_docs[:top_k]
