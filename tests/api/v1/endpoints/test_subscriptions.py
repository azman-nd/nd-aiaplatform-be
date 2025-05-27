import pytest
from uuid import UUID
from fastapi import status
from sqlalchemy.orm import Session
from app.core.database import Base, get_db
from app.main import app
from fastapi.testclient import TestClient
from typing import Generator
from app.models.database import AgentDB
from app.models.schemas import AgentSubscriptionCreate, AgentSubscriptionInDB
from app.core.auth import get_current_user
import jwt
from unittest.mock import patch
from datetime import datetime, timezone

def override_get_current_user():
    return {
        "id": "test-user",
        "email": "test@example.com",
        "o": {
            "rol": "admin",
            "per": "manage"
        },
        "fea": "o:all_content"
    }

# Database session fixture
@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    session = next(get_db())
    try:
        yield session
    finally:
        session.close()

# Client fixture with database session and mocked authentication
@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Mock JWT verification
    def mock_jwt_decode(*args, **kwargs):
        return {
            "sub": "1234567890",
            "name": "Test User",
            "iat": 1516239022,
            "fea": "o:all_content",
            "o": {
                "rol": "admin",
                "per": "manage"
            }
        }

    with patch('jwt.decode', side_effect=mock_jwt_decode):
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user
        with TestClient(app) as test_client:
            # Add Authorization header with a mock JWT token
            test_client.headers = {
                "Authorization": "Bearer mock_token"
            }
            yield test_client
        app.dependency_overrides.clear()

# Sample agent fixture
@pytest.fixture
def sample_agent(db_session: Session):
    agent = AgentDB(
        name="Test Agent",
        title="Test Title",
        description="Test Description",
        version="1.0.0",
        image_url="https://example.com/image.png",
        features="Feature 1\nFeature 2",
        status="active",
        pricing_model="paid",
        price=9.99,
        provider="Test Provider",
        language_support=["en"],
        tags=["test"],
        display_order=1
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    return agent

# Sample subscription data fixture
@pytest.fixture
def sample_subscription_data():
    return {
        "user_id": "test-user",
        "agent_id": None,  # Will be set in tests
        "purchase_modality": "monthly",
        "purchase_date": datetime.now(timezone.utc).isoformat(),
        "ownership_status": "active"
    }

# Cleanup database before each test
@pytest.fixture(autouse=True)
def setup_database(db_session: Session):
    Base.metadata.create_all(bind=db_session.get_bind())
    yield
    Base.metadata.drop_all(bind=db_session.get_bind())

def test_subscribe_agent(client, db_session, sample_agent, sample_subscription_data):
    """
    Test Case: Subscribe to an agent
    - Verifies successful subscription creation
    - Validates all fields are correctly saved
    - Ensures UUID is generated
    - Checks correct status code (201 Created)
    """
    sample_subscription_data["agent_id"] = str(sample_agent.id)
    response = client.post("/api/v1/subscriptions/subscribe", json=sample_subscription_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["user_id"] == sample_subscription_data["user_id"]
    assert data["agent_id"] == sample_subscription_data["agent_id"]
    assert data["purchase_modality"] == sample_subscription_data["purchase_modality"]
    assert data["ownership_status"] == sample_subscription_data["ownership_status"]
    assert UUID(data["id"])  # Verify UUID format

def test_subscribe_agent_duplicate(client, db_session, sample_agent, sample_subscription_data):
    """
    Test Case: Attempt to subscribe to an agent twice
    - Verifies unique subscription constraint
    - Ensures first subscription succeeds
    - Validates second subscription fails
    - Checks correct error message
    """
    sample_subscription_data["agent_id"] = str(sample_agent.id)
    
    # Create first subscription
    response = client.post("/api/v1/subscriptions/subscribe", json=sample_subscription_data)
    assert response.status_code == status.HTTP_201_CREATED

    # Try to create second subscription
    response = client.post("/api/v1/subscriptions/subscribe", json=sample_subscription_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "User already has an active subscription for this agent"

def test_subscribe_agent_not_found(client, sample_subscription_data):
    """
    Test Case: Attempt to subscribe to non-existent agent
    - Verifies proper handling of non-existent agent ID
    - Ensures correct error message
    - Checks correct status code (404 Not Found)
    """
    sample_subscription_data["agent_id"] = "00000000-0000-0000-0000-000000000000"
    response = client.post("/api/v1/subscriptions/subscribe", json=sample_subscription_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Agent not found"

def test_unsubscribe_agent(client, db_session, sample_agent, sample_subscription_data):
    """
    Test Case: Unsubscribe from an agent
    - Verifies successful subscription update
    - Validates ownership status is updated
    - Ensures original ID is preserved
    - Checks correct status code (200 OK)
    """
    # Create subscription
    sample_subscription_data["agent_id"] = str(sample_agent.id)
    create_response = client.post("/api/v1/subscriptions/subscribe", json=sample_subscription_data)
    subscription_id = create_response.json()["id"]

    # Unsubscribe
    response = client.post(f"/api/v1/subscriptions/unsubscribe/{subscription_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == subscription_id
    assert data["ownership_status"] == "unsubscribed"

def test_unsubscribe_agent_not_found(client):
    """
    Test Case: Attempt to unsubscribe from non-existent subscription
    - Verifies proper handling of non-existent subscription ID
    - Ensures correct error message
    - Checks correct status code (404 Not Found)
    """
    response = client.post("/api/v1/subscriptions/unsubscribe/00000000-0000-0000-0000-000000000000")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Subscription not found"

def test_subscribe_agent_invalid_input(client, sample_agent):
    """
    Test Case: Attempt to subscribe with invalid input
    - Verifies validation of required fields
    - Ensures proper error messages
    - Checks correct status code (422 Unprocessable Entity)
    """
    invalid_data = {
        "user_id": "test-user",
        # Missing required field: agent_id
    }
    response = client.post("/api/v1/subscriptions/subscribe", json=invalid_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_subscribe_agent_with_missing_token(client, db_session, sample_agent, sample_subscription_data):
    """
    Test Case: Attempt to subscribe without authentication token
    - Verifies authentication check
    - Ensures proper error message
    - Checks correct status code (403 Forbidden)
    """
    # Remove the dependency override for get_current_user
    app.dependency_overrides.pop(get_current_user, None)
    
    client.headers = {}  # Remove Authorization header
    sample_subscription_data["agent_id"] = str(sample_agent.id)
    response = client.post("/api/v1/subscriptions/subscribe", json=sample_subscription_data)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authenticated"
    
    # Restore the dependency override
    app.dependency_overrides[get_current_user] = override_get_current_user 

def test_get_user_subscriptions(client, db_session, sample_agent, sample_subscription_data):
    """
    Test Case: Get user's subscriptions
    - Verifies successful retrieval of user's subscriptions
    - Validates all fields are correctly returned
    - Checks correct status code (200 OK)
    """
    # Create a subscription first
    sample_subscription_data["agent_id"] = str(sample_agent.id)
    create_response = client.post("/api/v1/subscriptions/subscribe", json=sample_subscription_data)
    assert create_response.status_code == status.HTTP_201_CREATED

    # Get user's subscriptions
    response = client.get("/api/v1/subscriptions/user-subscriptions")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify response structure
    assert len(data) == 1
    subscription = data[0]
    assert subscription["agent_id"] == str(sample_agent.id)
    assert subscription["agent_name"] == sample_agent.name
    assert subscription["agent_title"] == sample_agent.title
    assert subscription["agent_description"] == sample_agent.description
    assert subscription["purchase_modality"] == sample_subscription_data["purchase_modality"]
    assert subscription["ownership_status"] == sample_subscription_data["ownership_status"]

def test_get_user_subscriptions_empty(client):
    """
    Test Case: Get user's subscriptions when user has none
    - Verifies empty list is returned for user with no subscriptions
    - Checks correct status code (200 OK)
    """
    response = client.get("/api/v1/subscriptions/user-subscriptions")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [] 