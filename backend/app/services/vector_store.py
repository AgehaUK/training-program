"""
FAISS ベクトル検索サービス

sentence-transformers でテキストをベクトル化し、
FAISS インデックスで類似度検索を行う。
"""
import json
import os
from pathlib import Path
from typing import List, Tuple

import numpy as np

INDEX_DIR = Path(__file__).parent.parent.parent / "data"
INDEX_PATH = INDEX_DIR / "faiss.index"
IDS_PATH = INDEX_DIR / "faiss_ids.json"

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


class VectorStore:
    def __init__(self) -> None:
        self._model = None
        self._index = None
        self._ids: List[int] = []
        self._loaded = False

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(MODEL_NAME)
        return self._model

    def _encode(self, texts: List[str]) -> np.ndarray:
        model = self._get_model()
        embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.astype("float32")

    def load(self) -> None:
        """インデックスをファイルから読み込む"""
        import faiss
        if INDEX_PATH.exists() and IDS_PATH.exists():
            self._index = faiss.read_index(str(INDEX_PATH))
            with open(IDS_PATH, "r") as f:
                self._ids = json.load(f)
        else:
            dim = 384  # MiniLM の次元数
            self._index = faiss.IndexFlatIP(dim)
            self._ids = []
        self._loaded = True

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def save(self) -> None:
        import faiss
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(INDEX_PATH))
        with open(IDS_PATH, "w") as f:
            json.dump(self._ids, f)

    def add(self, report_id: int, text: str) -> None:
        """レポートをインデックスに追加する"""
        self._ensure_loaded()
        if report_id in self._ids:
            return
        vec = self._encode([text])
        self._index.add(vec)
        self._ids.append(report_id)
        self.save()

    def add_bulk(self, reports: List[Tuple[int, str]]) -> None:
        """複数レポートをまとめてインデックスに追加し、最後に1回だけ保存する"""
        self._ensure_loaded()
        new_reports = [(rid, text) for rid, text in reports if rid not in self._ids]
        if not new_reports:
            return
        ids, texts = zip(*new_reports)
        vecs = self._encode(list(texts))
        self._index.add(vecs)
        self._ids.extend(ids)
        self.save()

    def build(self, reports: List[Tuple[int, str]]) -> None:
        """既存レポート一覧からインデックスを再構築する"""
        import faiss
        dim = 384
        self._index = faiss.IndexFlatIP(dim)
        self._ids = []

        if not reports:
            self.save()
            return

        ids, texts = zip(*reports)
        vecs = self._encode(list(texts))
        self._index.add(vecs)
        self._ids = list(ids)
        self._loaded = True
        self.save()

    def search(self, query: str, top_k: int = 50) -> List[int]:
        """クエリに類似するレポートIDリストを返す（類似度順）"""
        self._ensure_loaded()
        if self._index.ntotal == 0:
            return []
        vec = self._encode([query])
        k = min(top_k, self._index.ntotal)
        _scores, indices = self._index.search(vec, k)
        result = []
        for idx in indices[0]:
            if 0 <= idx < len(self._ids):
                result.append(self._ids[idx])
        return result


vector_store = VectorStore()
