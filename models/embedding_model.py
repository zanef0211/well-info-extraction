"""
文本嵌入模型 - 生成文本向量表示
"""
import logging
from typing import List, Dict, Any
import json
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from utils.logger import get_logger
from utils.exceptions import ModelError

logger = get_logger(__name__)


class EmbeddingModel:
    """文本嵌入模型 - 使用sentence-transformers生成文本向量"""

    # 推荐的中文Embedding模型
    DEFAULT_MODEL = "BAAI/bge-large-zh-v1.5"
    ALTERNATIVE_MODELS = [
        "shibing624/text2vec-base-chinese",
        "moka-ai/m3e-base",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    ]

    def __init__(
        self,
        model_name: str = None,
        device: str = "cpu",
        cache_dir: str = None,
    ):
        """
        初始化嵌入模型

        Args:
            model_name: 模型名称,默认使用BGE-large-zh
            device: 运行设备 (cpu/cuda)
            cache_dir: 模型缓存目录
        """
        if SentenceTransformer is None:
            raise ModelError("sentence-transformers未安装,请先安装: pip install sentence-transformers")

        self.model_name = model_name or self.DEFAULT_MODEL
        self.device = device
        self.cache_dir = cache_dir

        try:
            logger.info(f"加载嵌入模型: {self.model_name}")
            self.model = SentenceTransformer(
                self.model_name,
                device=device,
                cache_folder=cache_dir,
            )
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"嵌入模型加载成功,向量维度: {self.embedding_dim}")
        except Exception as e:
            logger.error(f"嵌入模型加载失败: {e}", exc_info=True)
            raise ModelError(f"嵌入模型加载失败: {str(e)}") from e

    def encode(
        self,
        texts: str | List[str],
        normalize: bool = True,
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> List[List[float]]:
        """
        将文本编码为向量

        Args:
            texts: 单个文本或文本列表
            normalize: 是否归一化向量
            batch_size: 批处理大小
            show_progress: 是否显示进度条

        Returns:
            向量列表,每个向量是float列表
        """
        try:
            # 统一转换为列表
            if isinstance(texts, str):
                texts = [texts]
                single_input = True
            else:
                single_input = False

            logger.debug(f"编码文本数量: {len(texts)}")

            # 编码
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=normalize,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
            )

            # 转换为Python列表
            embeddings = embeddings.tolist()

            if single_input:
                return embeddings[0]

            return embeddings

        except Exception as e:
            logger.error(f"文本编码失败: {e}", exc_info=True)
            raise ModelError(f"文本编码失败: {str(e)}") from e

    def encode_with_cache(
        self,
        texts: List[str],
        cache_path: str = None,
        normalize: bool = True,
    ) -> List[List[float]]:
        """
        带缓存的文本编码,避免重复计算

        Args:
            texts: 文本列表
            cache_path: 缓存文件路径(JSON格式)
            normalize: 是否归一化

        Returns:
            向量列表
        """
        if cache_path:
            cache_path = Path(cache_path)
            cache = {}

            # 尝试加载缓存
            if cache_path.exists():
                try:
                    with open(cache_path, "r", encoding="utf-8") as f:
                        cache = json.load(f)
                    logger.info(f"加载缓存: {len(cache)} 条记录")
                except Exception as e:
                    logger.warning(f"缓存加载失败: {e}")

        # 找出需要编码的文本
        uncached_texts = []
        uncached_indices = []
        if cache_path:
            for idx, text in enumerate(texts):
                if text not in cache:
                    uncached_texts.append(text)
                    uncached_indices.append(idx)
        else:
            uncached_texts = texts
            uncached_indices = list(range(len(texts)))

        # 编码未缓存的文本
        embeddings = [None] * len(texts)
        if uncached_texts:
            logger.info(f"编码 {len(uncached_texts)} 个新文本")
            new_embeddings = self.encode(uncached_texts, normalize=normalize)

            # 填充结果
            for idx, emb in zip(uncached_indices, new_embeddings):
                embeddings[idx] = emb

                # 更新缓存
                if cache_path:
                    cache[texts[idx]] = emb

        # 使用缓存的嵌入
        if cache_path:
            for idx in range(len(texts)):
                if embeddings[idx] is None:
                    embeddings[idx] = cache[texts[idx]]

        # 保存缓存
        if cache_path and uncached_texts:
            try:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(cache, f, ensure_ascii=False, indent=2)
                logger.info(f"缓存已保存: {cache_path}")
            except Exception as e:
                logger.warning(f"缓存保存失败: {e}")

        return embeddings

    def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float],
    ) -> float:
        """
        计算两个向量之间的余弦相似度

        Args:
            embedding1: 向量1
            embedding2: 向量2

        Returns:
            相似度 (0-1之间)
        """
        import numpy as np

        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # 余弦相似度
        similarity = np.dot(vec1, vec2) / (
            np.linalg.norm(vec1) * np.linalg.norm(vec2) + 1e-8
        )

        return float(similarity)

    def find_most_similar(
        self,
        query: str,
        candidates: List[str],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        在候选文本中找到最相似的文本

        Args:
            query: 查询文本
            candidates: 候选文本列表
            top_k: 返回前k个最相似的结果

        Returns:
            相似度结果列表,包含text和similarity
        """
        # 编码查询和候选文本
        query_emb = self.encode(query)
        candidate_embs = self.encode(candidates)

        # 计算相似度
        similarities = [
            self.compute_similarity(query_emb, cand_emb)
            for cand_emb in candidate_embs
        ]

        # 排序
        results = [
            {"text": text, "similarity": sim}
            for text, sim in zip(candidates, similarities)
        ]
        results.sort(key=lambda x: x["similarity"], reverse=True)

        return results[:top_k]
