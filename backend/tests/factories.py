"""
テスト用ファクトリー（Faker ベース）
"""
from datetime import date, timedelta
import random

from app.models.failure_mode import FailureMode
from app.models.failure_report import FailureReport


FAILURE_MODE_NAMES = ["劣化", "破損", "動作不良", "漏れ", "過熱", "腐食", "摩耗", "電気系統故障", "その他"]
EQUIPMENT_NAMES = ["設備A", "設備B", "コンプレッサーC", "ポンプD", "センサーE"]
SYMPTOMS = ["停止", "異音", "漏れ", "過熱", "エラー発生"]


def create_failure_mode(db_session, name: str = None) -> FailureMode:
    name = name or random.choice(FAILURE_MODE_NAMES)
    mode = FailureMode(name=name)
    db_session.add(mode)
    db_session.commit()
    db_session.refresh(mode)
    return mode


def create_failure_report(
    db_session,
    failure_mode_id: int = None,
    occurred_at: date = None,
    equipment_name: str = None,
    symptom: str = None,
    cost: int = None,
    downtime_hours: float = None,
    source: str = "manual",
) -> FailureReport:
    report = FailureReport(
        original_text="テスト用故障報告テキスト",
        occurred_at=occurred_at or date.today() - timedelta(days=random.randint(0, 365)),
        equipment_name=equipment_name or random.choice(EQUIPMENT_NAMES),
        symptom=symptom or random.choice(SYMPTOMS),
        cost=cost if cost is not None else random.choice([10000, 50000, 100000, None]),
        downtime_hours=downtime_hours if downtime_hours is not None else random.choice([1.0, 2.0, 4.0, None]),
        failure_mode_id=failure_mode_id,
        source=source,
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)
    return report


def create_failure_reports(db_session, count: int = 5) -> list:
    mode = create_failure_mode(db_session, "電気系統故障")
    return [create_failure_report(db_session, failure_mode_id=mode.id) for _ in range(count)]
