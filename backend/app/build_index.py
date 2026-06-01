"""
既存の故障レポートから FAISS インデックスを構築するスクリプト

実行: python3 -m app.build_index
"""
from app.db.database import SessionLocal
from app.models.failure_report import FailureReport
from app.services.vector_store import vector_store


def build():
    db = SessionLocal()
    try:
        reports = db.query(FailureReport).all()
        data = []
        for r in reports:
            parts = [r.equipment_name or "", r.symptom or "", r.cause or "", r.action_taken or ""]
            text = " ".join(p for p in parts if p)
            data.append((r.id, text))
        print(f"{len(data)} 件のレポートをインデックス化中...")
        vector_store.build(data)
        print("完了しました。")
    finally:
        db.close()


if __name__ == "__main__":
    build()
