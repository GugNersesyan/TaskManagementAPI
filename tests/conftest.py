import os
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing")

import pytest
from unittest.mock import MagicMock, patch
import fakeredis
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.models.user import User
from app.models.task import Task, TaskStatus, TaskPriority
from app.core.security import Role, hash_password, create_access_token
from app.db.base_class import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture(scope="function")
def test_engine():
    engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
    
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(test_engine, mock_redis):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    with patch("app.core.cache.redis_client", mock_redis):
        with patch("app.services.task_service.asyncio") as mock_asyncio:
            mock_asyncio.create_task = MagicMock()
            app.dependency_overrides[get_db] = override_get_db
            yield TestClient(app)
            app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(test_engine, mock_redis):
    """Async HTTPX client for testing async endpoints."""
    from httpx import ASGITransport, AsyncClient
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    with patch("app.core.cache.redis_client", mock_redis):
        with patch("app.services.task_service.asyncio") as mock_asyncio:
            mock_asyncio.create_task = MagicMock()
            app.dependency_overrides[get_db] = override_get_db
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                yield ac
            
            app.dependency_overrides.clear()


@pytest.fixture
def test_user_db(test_db):
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=hash_password("password123"),
        role="user"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_admin_db(test_db):
    admin = User(
        username="adminuser",
        email="admin@example.com",
        hashed_password=hash_password("adminpass123"),
        role=Role.ADMIN
    )
    test_db.add(admin)
    test_db.commit()
    test_db.refresh(admin)
    return admin


@pytest.fixture
def test_user2_db(test_db):
    user = User(
        username="testuser2",
        email="test2@example.com",
        hashed_password=hash_password("password123"),
        role="user"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def user_token(test_user_db):
    return create_access_token(str(test_user_db.id), test_user_db.role)


@pytest.fixture
def user2_token(test_user2_db):
    return create_access_token(str(test_user2_db.id), test_user2_db.role)


@pytest.fixture
def admin_token(test_admin_db):
    return create_access_token(str(test_admin_db.id), test_admin_db.role)


@pytest.fixture
def mock_redis():
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    return db


@pytest.fixture
def test_user():
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.hashed_password = "hashed_password"
    user.role = "user"
    user.created_at = None
    return user


@pytest.fixture
def test_admin_user():
    user = MagicMock(spec=User)
    user.id = 2
    user.username = "adminuser"
    user.email = "admin@example.com"
    user.hashed_password = "hashed_admin_password"
    user.role = Role.ADMIN
    user.created_at = None
    return user


@pytest.fixture
def test_task(test_user):
    task = MagicMock(spec=Task)
    task.id = 1
    task.title = "Test Task"
    task.description = "Test Description"
    task.status = TaskStatus.pending
    task.priority = TaskPriority.medium
    task.created_by = test_user.id
    task.assigned_to = None
    task.created_at = None
    task.updated_at = None
    return task


@pytest.fixture
def test_completed_task(test_user):
    task = MagicMock(spec=Task)
    task.id = 2
    task.title = "Completed Task"
    task.description = "Completed Description"
    task.status = TaskStatus.completed
    task.priority = TaskPriority.high
    task.created_by = test_user.id
    task.assigned_to = None
    task.created_at = None
    task.updated_at = None
    return task


@pytest.fixture
def mock_redis_client(mock_redis):
    with patch("app.core.cache.redis_client", mock_redis):
        yield mock_redis


@pytest.fixture
def mock_asyncio():
    with patch("app.services.task_service.asyncio") as mock:
        mock.create_task = MagicMock()
        yield mock
