"""
pytest フィクスチャ: テスト用インメモリ SQLite DB + 認証
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db.database import Base, get_db
import app.models as _models  # noqa: F401
from app.main import app as fastapi_app
from app.core.auth import create_access_token, get_password_hash
from app.models.user import User
from app.models.failure_mode import FailureMode

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session():
    """関数スコープのインメモリ SQLite セッション（全テーブル作成済み）"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def api_client(db_session):
    """テスト用 FastAPI クライアント。
    - db_session と同じ DB を使用（テストでシードしたデータが API から見える）
    - admin / user1 を自動作成
    """
    # テスト用ユーザーを DB に投入
    admin = User(username="admin", hashed_password=get_password_hash("admin1234"), role="admin")
    user = User(username="user1", hashed_password=get_password_hash("user1234"), role="user")
    db_session.add_all([admin, user])
    db_session.commit()

    def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    client = TestClient(fastapi_app)
    yield client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def admin_headers():
    """管理者用 Authorization ヘッダー"""
    token = create_access_token({"sub": "admin", "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def user_headers():
    """一般ユーザー用 Authorization ヘッダー"""
    token = create_access_token({"sub": "user1", "role": "user"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def failure_mode(db_session):
    """テスト用故障モードマスタ（摩耗）"""
    mode = FailureMode(name="摩耗")
    db_session.add(mode)
    db_session.commit()
    db_session.refresh(mode)
    return mode
