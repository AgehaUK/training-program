"""
Slice 2: FailureReportRepository のテスト
"""
from datetime import date

import pytest

from app.repositories.failure_mode_repository import FailureModeRepository
from app.repositories.failure_report_repository import FailureReportRepository


class TestFailureReportRepository:
    def test_create_returns_report_with_id(self, db_session):
        mode_repo = FailureModeRepository(db_session)
        mode = mode_repo.find_or_create_by_name("電気系統故障")

        repo = FailureReportRepository(db_session)
        report = repo.create(
            original_text="テスト故障報告",
            occurred_at=date(2025, 3, 15),
            equipment_name="設備A",
            symptom="停止",
            failure_mode_id=mode.id,
        )
        assert report.id is not None
        assert report.equipment_name == "設備A"
        assert report.source == "manual"

    def test_create_with_optional_fields(self, db_session):
        repo = FailureReportRepository(db_session)
        report = repo.create(
            original_text="テスト",
            occurred_at=date(2025, 1, 1),
            equipment_name="設備B",
            symptom="異音",
            cause="ベアリング摩耗",
            action_taken="ベアリング交換",
            cost=50000,
            downtime_hours=3.0,
        )
        assert report.cause == "ベアリング摩耗"
        assert report.cost == 50000
        assert report.downtime_hours == 3.0

    def test_create_with_sample_source(self, db_session):
        repo = FailureReportRepository(db_session)
        report = repo.create(
            original_text="サンプル",
            occurred_at=date(2025, 6, 1),
            equipment_name="設備C",
            symptom="停止",
            source="sample",
        )
        assert report.source == "sample"

    def test_find_by_id_returns_report(self, db_session):
        repo = FailureReportRepository(db_session)
        created = repo.create(
            original_text="テスト",
            occurred_at=date(2025, 1, 1),
            equipment_name="設備A",
            symptom="停止",
        )
        found = repo.find_by_id(created.id)
        assert found is not None
        assert found.id == created.id

    def test_find_by_id_returns_none_for_missing(self, db_session):
        repo = FailureReportRepository(db_session)
        assert repo.find_by_id(99999) is None
