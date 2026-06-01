"""
Slice 5: VectorStore のテスト
"""
import pytest
from app.services.vector_store import VectorStore


@pytest.fixture()
def store(tmp_path, monkeypatch):
    """一時ディレクトリを使う独立した VectorStore インスタンス"""
    monkeypatch.setattr("app.services.vector_store.INDEX_DIR", tmp_path)
    monkeypatch.setattr("app.services.vector_store.INDEX_PATH", tmp_path / "faiss.index")
    monkeypatch.setattr("app.services.vector_store.IDS_PATH", tmp_path / "faiss_ids.json")
    v = VectorStore()
    v.load()
    return v


class TestVectorStore:
    def test_empty_store_returns_no_results(self, store):
        assert store.search("ポンプ故障") == []

    def test_add_and_search_returns_id(self, store):
        store.add(1, "ポンプが停止 流量低下 インペラー摩耗")
        results = store.search("ポンプ停止")
        assert 1 in results

    def test_search_returns_similar_not_exact(self, store):
        """表記揺れでもヒットする"""
        store.add(10, "油圧シリンダーからオイル漏れ発生")
        store.add(20, "コンプレッサー圧力低下 警報発報")
        results = store.search("油漏れ")
        assert 10 in results

    def test_add_same_id_twice_not_duplicated(self, store):
        store.add(5, "設備A停止")
        store.add(5, "設備A停止")
        assert store._ids.count(5) == 1

    def test_build_indexes_all_reports(self, store):
        reports = [
            (1, "ポンプ 流量低下 摩耗"),
            (2, "モーター 異音 ベアリング"),
            (3, "バルブ 漏れ パッキン劣化"),
        ]
        store.build(reports)
        assert store._index.ntotal == 3
        assert set(store._ids) == {1, 2, 3}

    def test_add_bulk_adds_multiple(self, store):
        store.add_bulk([(1, "ポンプ摩耗"), (2, "モーター異音"), (3, "バルブ漏れ")])
        assert store._index.ntotal == 3

    def test_add_bulk_skips_existing_ids(self, store):
        store.add(1, "既存レポート")
        store.add_bulk([(1, "重複"), (2, "新規レポート")])
        assert store._ids.count(1) == 1
        assert store._index.ntotal == 2

    def test_search_top_k_limits_results(self, store):
        for i in range(10):
            store.add(i, f"設備{i} 故障 停止")
        results = store.search("設備故障", top_k=3)
        assert len(results) <= 3

    def test_index_persisted_and_reloaded(self, store, tmp_path, monkeypatch):
        """保存→再ロードしても検索できる"""
        store.add(42, "コンベア チェーン切断 過負荷")
        store.save()

        store2 = VectorStore()
        monkeypatch.setattr("app.services.vector_store.INDEX_PATH", tmp_path / "faiss.index")
        monkeypatch.setattr("app.services.vector_store.IDS_PATH", tmp_path / "faiss_ids.json")
        store2.load()
        assert 42 in store2._ids
