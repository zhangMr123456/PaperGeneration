from typing import List
import torch
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer
import logging
from functools import lru_cache

from core.embedding.bge import BGEConfig
logger = logging.getLogger(__name__)


class BGEEmbeddings(Embeddings):
    """BGE Embeddings适配器 - LangChain兼容"""

    def __init__(self, config: BGEConfig):
        self.config = config
        self.device = config.device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._init_model()

    def _init_model(self):
        """初始化模型"""
        logger.info(f"Loading BGE embedding model: {self.config.embedding_model}")
        self.model = SentenceTransformer(
            self.config.embedding_model,
            device=self.device
        )
        self.model.eval()
        logger.info(f"Embedding model loaded on {self.device}")

    @lru_cache(maxsize=1000)
    def embed_query(self, text: str) -> List[float]:
        """嵌入查询文本"""
        with torch.no_grad():
            embedding = self.model.encode(
                text,
                normalize_embeddings=self.config.normalize_embeddings,
                show_progress_bar=False
            )
        return embedding.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入文档"""
        # 为文档添加指令前缀
        instruction_texts = [
            self.config.embedding_instruction + text
            for text in texts
        ]

        embeddings = []
        for i in range(0, len(instruction_texts), self.config.batch_size):
            batch = instruction_texts[i:i + self.config.batch_size]
            with torch.no_grad():
                batch_embeddings = self.model.encode(
                    batch,
                    normalize_embeddings=self.config.normalize_embeddings,
                    show_progress_bar=False
                )
            embeddings.extend(batch_embeddings.tolist())

        return embeddings

    @property
    def model_dimension(self) -> int:
        """获取模型维度"""
        # BGE-large-zh-v1.5固定为1024维
        return 1024
