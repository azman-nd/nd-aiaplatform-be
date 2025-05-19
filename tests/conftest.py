import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import app.core.database as app_db

# Create test database engine using SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Patch the app's engine and SessionLocal to use the test engine/session
app_db.engine = test_engine
app_db.SessionLocal = TestingSessionLocal

# Use the app's Base
Base = app_db.Base

# Patch AgentDB table schema for SQLite (no schema support)
from app.models.database import AgentDB
AgentDB.__table__.schema = None

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def client(db_session):
    from app.main import app
    from app.core.database import get_db
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def sample_agent_data():
    return {
        "name": "Test Agent",
        "title": "Test Agent Title",
        "description": "This is a test agent description",
        "version": "1.0.0",
        "imageUrl": "https://example.com/image.png",
        "features": "Feature 1\nFeature 2\nFeature 3",
        "status": "active",
        "pricing_model": "paid",
        "price": 9.99,
        "provider": "Test Provider",
        "language_support": ["en"],
        "tags": ["test", "sample"],
        "display_order": 1
    } 