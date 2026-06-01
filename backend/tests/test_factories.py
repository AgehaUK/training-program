"""
ファクトリーのテスト
"""
import pytest

from tests.factories import create_failure_mode, create_failure_report, create_failure_reports


class TestFailureModeFactory:
    def test_create_failure_mode(self, db_session):
        mode = create_failure_mode(db_session, name="電気系統故障")
        assert mode.id is not None
        assert mode.name == "電気系統故障"

    def test_create_failure_mode_random_name(self, db_session):
        mode = create_failure_mode(db_session)
        assert mode.id is not None
        assert mode.name is not None


class TestFailureReportFactory:
    def test_create_failure_report(self, db_session):
        mode = create_failure_mode(db_session, name="劣化")
        report = create_failure_report(db_session, failure_mode_id=mode.id)
        assert report.id is not None
        assert report.equipment_name is not None

    def test_create_failure_reports_count(self, db_session):
        reports = create_failure_reports(db_session, count=3)
        assert len(reports) == 3

    def test_create_failure_reports_all_have_source_manual(self, db_session):
        reports = create_failure_reports(db_session, count=2)
        assert all(r.source == "manual" for r in reports)
