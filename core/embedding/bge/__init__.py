from typing import Optional

from pydantic import BaseModel


class BGEConfig(BaseModel):
    """BGE模型配置"""
    embedding_model: str = r"D:\models\BAAI\bge-large-zh-v1.5"
    reranker_model: str = r"D:\models\BAAI\bge-reranker-v2-m3"
    device: Optional[str] = None
    normalize_embeddings: bool = True
    embedding_instruction: str = "为这个句子生成表示用于语义检索："
    max_length: int = 1024
    batch_size: int = 32


