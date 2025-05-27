import pytest
from uuid import UUID
from fastapi import status
from sqlalchemy.orm import Session
from app.core.database import Base, get_db
from app.main import app
from fastapi.testclient import TestClient
from typing import Generator
from app.models.database import AgentDB
from app.models.schemas import Agent, AgentStatus, PricingModel, AgentCreate, AgentUpdate
from app.core.auth import get_current_user
import jwt
from unittest.mock import patch
from app.core.permissions import check_role_and_permission

# Database session fixture
@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    # Create a new database session for each test
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

    def override_get_current_user():
        return {
            "id": "test-user",
            "email": "test@example.com",
            "o": {
                "rol": "admin",
                "per": "manage"
            },
            "fea": "all_content"
        }

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

# Sample agent data fixture
@pytest.fixture
def sample_agent_data():
    return {
        "name": "Test Agent",
        "title": "Test Title",
        "description": "This is a test description that is long enough to meet the minimum length requirement",
        "version": "1.0.0",
        "image_url": "https://example.com/image.png",
        "features": "Feature 1\nFeature 2\nFeature 3",
        "status": "active",
        "pricing_model": "paid",
        "price": 9.99,
        "provider": "Test Provider",
        "language_support": ["en"],
        "tags": ["test", "sample"],
        "display_order": 1,
        "demo_url": "https://demo.test.com",
        "prod_url": "https://prod.test.com"
    }

# Cleanup database before each test
@pytest.fixture(autouse=True)
def setup_database(db_session: Session):
    # Create tables
    Base.metadata.create_all(bind=db_session.get_bind())
    yield
    # Drop tables after test
    Base.metadata.drop_all(bind=db_session.get_bind())

def test_list_agents_empty(client):
    """
    Test Case: List agents when database is empty
    - Verifies that GET /api/v1/agents/ returns empty list
    - Ensures proper handling of empty database state
    - Checks correct status code (200 OK)
    """
    response = client.get("/api/v1/agents/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

def test_create_agent(client, db_session, sample_agent_data):
    """
    Test Case: Create a new agent
    - Verifies successful agent creation
    - Validates all fields are correctly saved
    - Ensures UUID is generated
    - Checks correct status code (201 Created)
    """
    response = client.post("/api/v1/agents/", json=sample_agent_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == sample_agent_data["name"]
    assert data["title"] == sample_agent_data["title"]
    assert data["description"] == sample_agent_data["description"]
    assert data["image_url"] == sample_agent_data["image_url"]
    assert data["demo_url"] == sample_agent_data["demo_url"]
    assert data["prod_url"] == sample_agent_data["prod_url"]
    assert UUID(data["id"])  # Verify UUID format

def test_create_agent_duplicate_name(client, db_session, sample_agent_data):
    """
    Test Case: Attempt to create agent with duplicate name
    - Verifies unique name constraint
    - Ensures first agent creation succeeds
    - Validates second creation with same name fails
    - Checks correct error message
    """
    # Create first agent
    response = client.post("/api/v1/agents/", json=sample_agent_data)
    assert response.status_code == status.HTTP_201_CREATED

    # Try to create second agent with same name
    response = client.post("/api/v1/agents/", json=sample_agent_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "An agent with this name already exists"

def test_get_agent(client, db_session, sample_agent_data):
    """
    Test Case: Retrieve a specific agent
    - Verifies successful agent retrieval by ID
    - Validates all fields are correctly returned
    - Ensures correct agent is retrieved
    - Checks correct status code (200 OK)
    """
    # Create agent
    create_response = client.post("/api/v1/agents/", json=sample_agent_data)
    agent_id = create_response.json()["id"]

    # Get agent
    response = client.get(f"/api/v1/agents/{agent_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == agent_id
    assert data["name"] == sample_agent_data["name"]
    assert data["image_url"] == sample_agent_data["image_url"]
    assert data["demo_url"] == sample_agent_data["demo_url"]
    assert data["prod_url"] == sample_agent_data["prod_url"]

def test_get_agent_not_found(client):
    """
    Test Case: Attempt to retrieve non-existent agent
    - Verifies proper handling of non-existent agent ID
    - Ensures correct error message
    - Checks correct status code (404 Not Found)
    """
    response = client.get("/api/v1/agents/00000000-0000-0000-0000-000000000000")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Agent not found"

def test_update_agent(client, db_session, sample_agent_data):
    """
    Test Case: Update an existing agent
    - Verifies successful agent update
    - Validates all fields are correctly updated
    - Ensures original ID is preserved
    - Checks correct status code (200 OK)
    """
    # Create agent
    create_response = client.post("/api/v1/agents/", json=sample_agent_data)
    agent_id = create_response.json()["id"]

    # Update agent
    update_data = sample_agent_data.copy()
    update_data["name"] = "Updated Agent Name"
    update_data["description"] = "Updated description"
    update_data["image_url"] = "https://example.com/updated-image.png"
    update_data["demo_url"] = "https://demo.updated.com"
    update_data["prod_url"] = "https://prod.updated.com"

    response = client.put(f"/api/v1/agents/{agent_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == agent_id
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["image_url"] == update_data["image_url"]
    assert data["demo_url"] == update_data["demo_url"]
    assert data["prod_url"] == update_data["prod_url"]

def test_update_agent_not_found(client, sample_agent_data):
    """
    Test Case: Attempt to update non-existent agent
    - Verifies proper handling of non-existent agent ID
    - Ensures correct error message
    - Checks correct status code (404 Not Found)
    """
    response = client.put(
        "/api/v1/agents/00000000-0000-0000-0000-000000000000",
        json=sample_agent_data
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Agent not found"

def test_delete_agent(client, db_session, sample_agent_data):
    """
    Test Case: Delete an existing agent
    - Verifies successful agent deletion
    - Ensures agent is actually removed from database
    - Validates can't retrieve deleted agent
    - Checks correct status codes (204 No Content, 404 Not Found)
    """
    # Create agent
    create_response = client.post("/api/v1/agents/", json=sample_agent_data)
    agent_id = create_response.json()["id"]

    # Delete agent
    response = client.delete(f"/api/v1/agents/{agent_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify agent is deleted
    get_response = client.get(f"/api/v1/agents/{agent_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_agent_not_found(client):
    """
    Test Case: Attempt to delete non-existent agent
    - Verifies proper handling of non-existent agent ID
    - Ensures correct error message
    - Checks correct status code (404 Not Found)
    """
    response = client.delete("/api/v1/agents/00000000-0000-0000-0000-000000000000")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Agent not found"

def test_search_agents(client, sample_agent_data):
    """
    Test Case: Search for agents
    - Verifies search by name functionality
    - Validates search by description functionality
    - Ensures correct results are returned
    - Checks correct status code (200 OK)
    """
    # Create agent
    response = client.post("/api/v1/agents/", json=sample_agent_data)
    assert response.status_code == status.HTTP_201_CREATED

    # Search by name
    response = client.get("/api/v1/agents/search/?query=Test")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == sample_agent_data["name"]

    # Search by description
    response = client.get("/api/v1/agents/search/?query=description")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["description"] == sample_agent_data["description"]

def test_list_agents_with_filters(client, sample_agent_data):
    """
    Test Case: List agents with various filters
    - Verifies filtering by status
    - Validates filtering by pricing model
    - Tests pagination functionality
    - Ensures correct results for each filter
    """
    # Create agent
    response = client.post("/api/v1/agents/", json=sample_agent_data)
    assert response.status_code == status.HTTP_201_CREATED

    # Test status filter
    response = client.get("/api/v1/agents/?status=active")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "active"

    # Test pricing model filter
    response = client.get("/api/v1/agents/?pricing_model=paid")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["pricing_model"] == "paid"

    # Test pagination
    response = client.get("/api/v1/agents/?skip=0&limit=1")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1

def test_create_agent_invalid_input(client):
    """
    Test Case: Create agent with invalid input
    - Verifies handling of missing required fields
    - Validates invalid version format
    - Tests invalid status value
    - Ensures proper validation errors
    """
    # Test with missing required fields
    invalid_data = {
        "name": "Test Agent",
        # Missing title and description
        "version": "1.0.0",
        "status": "active",
        "pricing_model": "paid"
    }
    response = client.post("/api/v1/agents/", json=invalid_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test with invalid version format
    invalid_data = {
        "name": "Test Agent",
        "title": "Test Title",
        "description": "Test description",
        "version": "1.0",  # Invalid version format
        "status": "active",
        "pricing_model": "paid"
    }
    response = client.post("/api/v1/agents/", json=invalid_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test with invalid status
    invalid_data = {
        "name": "Test Agent",
        "title": "Test Title",
        "description": "Test description",
        "version": "1.0.0",
        "status": "invalid_status",  # Invalid status
        "pricing_model": "paid"
    }
    response = client.post("/api/v1/agents/", json=invalid_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_pagination_edge_cases(client, sample_agent_data):
    """
    Test Case: Pagination edge cases
    - Verifies handling of skip beyond available items
    - Tests invalid skip value
    - Validates invalid limit values
    - Ensures proper error handling
    """
    # Create multiple agents
    for i in range(3):
        agent_data = sample_agent_data.copy()
        agent_data["name"] = f"Test Agent {i}"
        response = client.post("/api/v1/agents/", json=agent_data)
        assert response.status_code == status.HTTP_201_CREATED

    # Test with skip beyond available items
    response = client.get("/api/v1/agents/?skip=10&limit=5")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 0

    # Test with invalid pagination parameters
    response = client.get("/api/v1/agents/?skip=-1&limit=5")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    response = client.get("/api/v1/agents/?skip=0&limit=0")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    response = client.get("/api/v1/agents/?skip=0&limit=101")  # Limit > 100
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_search_edge_cases(client, sample_agent_data):
    """
    Test Case: Search functionality edge cases
    - Verifies handling of empty search query
    - Tests search with no results
    - Validates search with special characters
    - Ensures proper error handling
    """
    # Create agent
    response = client.post("/api/v1/agents/", json=sample_agent_data)
    assert response.status_code == status.HTTP_201_CREATED

    # Test empty search query
    response = client.get("/api/v1/agents/search/?query=")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test search with no results
    response = client.get("/api/v1/agents/search/?query=nonexistent")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 0

    # Test search with special characters
    response = client.get("/api/v1/agents/search/?query=Test%20Agent")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1

def test_invalid_uuid_format(client):
    """
    Test Case: Invalid UUID format
    - Verifies handling of invalid UUID format
    - Ensures proper error message
    - Checks correct status code (422 Unprocessable Entity)
    """
    # Test with invalid UUID format
    response = client.get("/api/v1/agents/invalid-uuid")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_update_agent_duplicate_name(client, sample_agent_data):
    """
    Test Case: Update agent to have duplicate name
    - Verifies unique name constraint during update
    - Ensures first agent creation succeeds
    - Validates second agent creation succeeds
    - Tests update to duplicate name fails
    - Checks correct error message
    """
    # Create first agent
    response = client.post("/api/v1/agents/", json=sample_agent_data)
    assert response.status_code == status.HTTP_201_CREATED
    first_agent_id = response.json()["id"]

    # Create second agent with different name
    second_agent_data = sample_agent_data.copy()
    second_agent_data["name"] = "Second Test Agent"
    response = client.post("/api/v1/agents/", json=second_agent_data)
    assert response.status_code == status.HTTP_201_CREATED
    second_agent_id = response.json()["id"]

    # Try to update second agent with first agent's name
    update_data = second_agent_data.copy()
    update_data["name"] = sample_agent_data["name"]
    response = client.put(f"/api/v1/agents/{second_agent_id}", json=update_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "An agent with this name already exists"

def test_get_agents_ordered_by_display_order(client, db_session):
    """
    Test Case: Get agents ordered by display_order
    - Verifies that agents are returned in order of display_order
    - Tests multiple agents with different display_order values
    - Ensures correct ordering in response
    """
    # Create test agents with different display orders
    agent1 = AgentDB(
        name="Test Agent 1",
        title="Test Title 1",
        description="Test Description 1",
        version="1.0.0",
        features="Test Features 1",
        status="active",
        pricing_model="free",
        provider="Test Provider",
        display_order=2
    )
    agent2 = AgentDB(
        name="Test Agent 2",
        title="Test Title 2",
        description="Test Description 2",
        version="1.0.0",
        features="Test Features 2",
        status="active",
        pricing_model="free",
        provider="Test Provider",
        display_order=1
    )
    db_session.add(agent1)
    db_session.add(agent2)
    db_session.commit()

    response = client.get("/api/v1/agents/")
    assert response.status_code == 200
    agents = response.json()
    assert len(agents) == 2
    # Verify agents are ordered by display_order
    assert agents[0]["display_order"] == 1
    assert agents[1]["display_order"] == 2

def test_create_agent_with_display_order(client, db_session):
    """
    Test Case: Create agent with display_order
    - Verifies that display_order is correctly set during creation
    - Tests default display_order value
    - Ensures display_order is included in response
    """
    agent_data = {
        "name": "New Agent",
        "title": "New Title",
        "description": "New Description",
        "version": "1.0.0",
        "features": "New Features",
        "status": "active",
        "pricing_model": "free",
        "provider": "Test Provider",
        "display_order": 1
    }
    response = client.post("/api/v1/agents/", json=agent_data)
    assert response.status_code == 201
    created_agent = response.json()
    assert created_agent["name"] == agent_data["name"]
    assert created_agent["display_order"] == agent_data["display_order"]

def test_update_agent_display_order(client, db_session):
    """
    Test Case: Update agent display_order
    - Verifies that display_order can be updated
    - Tests partial update with only display_order
    - Ensures updated value is reflected in response
    """
    # Create a test agent
    agent = AgentDB(
        name="Test Agent",
        title="Test Title",
        description="Test Description",
        version="1.0.0",
        features="Test Features",
        status="active",
        pricing_model="free",
        provider="Test Provider",
        display_order=1
    )
    db_session.add(agent)
    db_session.commit()

    # Update the agent's display_order
    update_data = {
        "display_order": 2
    }
    response = client.put(f"/api/v1/agents/{agent.id}", json=update_data)
    assert response.status_code == 200
    updated_agent = response.json()
    assert updated_agent["display_order"] == 2

def test_get_agent_includes_display_order(client, db_session):
    """
    Test Case: Get agent includes display_order
    - Verifies that display_order is included in get response
    - Tests retrieval of agent with display_order
    - Ensures correct value is returned
    """
    # Create a test agent
    agent = AgentDB(
        name="Test Agent",
        title="Test Title",
        description="Test Description",
        version="1.0.0",
        features="Test Features",
        status="active",
        pricing_model="free",
        provider="Test Provider",
        display_order=1
    )
    db_session.add(agent)
    db_session.commit()

    response = client.get(f"/api/v1/agents/{agent.id}")
    assert response.status_code == 200
    retrieved_agent = response.json()
    assert retrieved_agent["display_order"] == 1

def test_create_agent_with_optional_urls(client, db_session):
    """
    Test Case: Create agent with optional URLs
    - Verifies that demo_url and prod_url are optional
    - Tests creation without URLs
    - Ensures proper handling of null values
    """
    agent_data = {
        "name": "Test Agent No URLs",
        "title": "Test Title",
        "description": "This is a test description that is long enough to meet the minimum length requirement",
        "version": "1.0.0",
        "features": "Feature 1\nFeature 2\nFeature 3",
        "status": "active",
        "pricing_model": "paid",
        "price": 9.99,
        "provider": "Test Provider",
        "language_support": ["en"],
        "tags": ["test", "sample"],
        "display_order": 1
    }
    response = client.post("/api/v1/agents/", json=agent_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["demo_url"] is None
    assert data["prod_url"] is None

def test_update_agent_urls_only(client, db_session, sample_agent_data):
    """
    Test Case: Update only the URLs of an agent
    - Verifies partial update of URLs
    - Tests updating only demo_url
    - Tests updating only prod_url
    - Ensures other fields remain unchanged
    """
    # Create agent
    create_response = client.post("/api/v1/agents/", json=sample_agent_data)
    agent_id = create_response.json()["id"]

    # Update only demo_url
    update_data = {
        "demo_url": "https://demo.updated.com"
    }
    response = client.put(f"/api/v1/agents/{agent_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["demo_url"] == update_data["demo_url"]
    assert data["prod_url"] == sample_agent_data["prod_url"]
    assert data["name"] == sample_agent_data["name"]  # Other fields unchanged

    # Update only prod_url
    update_data = {
        "prod_url": "https://prod.updated.com"
    }
    response = client.put(f"/api/v1/agents/{agent_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["prod_url"] == update_data["prod_url"]
    assert data["demo_url"] == "https://demo.updated.com"  # Previous update preserved
    assert data["name"] == sample_agent_data["name"]  # Other fields unchanged 

def test_create_agent_with_insufficient_permissions(client, db_session, sample_agent_data):
    """
    Test Case: Attempt to create agent with insufficient permissions
    - Verifies that non-admin users cannot create agents
    - Tests with incorrect role
    - Tests with incorrect permission
    - Ensures proper error messages
    """
    # Mock JWT with incorrect role
    def mock_jwt_decode_incorrect_role(*args, **kwargs):
        return {
            "sub": "1234567890",
            "name": "Test User",
            "iat": 1516239022,
            "fea": "o:all_content",
            "o": {
                "rol": "user",  # Incorrect role
                "per": "manage"
            }
        }

    with patch('jwt.decode', side_effect=mock_jwt_decode_incorrect_role):
        response = client.post("/api/v1/agents/", json=sample_agent_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Insufficient role" in response.json()["detail"]

    # Mock JWT with incorrect permission
    def mock_jwt_decode_incorrect_permission(*args, **kwargs):
        return {
            "sub": "1234567890",
            "name": "Test User",
            "iat": 1516239022,
            "fea": "o:all_content",
            "o": {
                "rol": "admin",
                "per": "view"  # Incorrect permission
            }
        }

    with patch('jwt.decode', side_effect=mock_jwt_decode_incorrect_permission):
        response = client.post("/api/v1/agents/", json=sample_agent_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Insufficient permissions" in response.json()["detail"]

def test_create_agent_with_missing_token(client, db_session, sample_agent_data):
    """
    Test Case: Attempt to create agent without authentication token
    - Verifies that requests without token are rejected
    - Tests with missing Authorization header
    - Tests with invalid token format
    - Ensures proper error messages
    """
    # Test with no Authorization header
    with TestClient(app) as test_client:
        response = test_client.post("/api/v1/agents/", json=sample_agent_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid authorization header" in response.json()["detail"]

    # Test with invalid token format
    with TestClient(app) as test_client:
        test_client.headers = {"Authorization": "InvalidFormat"}
        response = test_client.post("/api/v1/agents/", json=sample_agent_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid authorization header" in response.json()["detail"]

def test_create_agent_with_invalid_token(client, db_session, sample_agent_data):
    """
    Test Case: Attempt to create agent with invalid token
    - Verifies that invalid tokens are rejected
    - Tests with expired token
    - Tests with malformed token
    - Ensures proper error messages
    """
    # Mock expired token
    def mock_jwt_decode_expired(*args, **kwargs):
        raise jwt.ExpiredSignatureError("Token has expired")

    with patch('jwt.decode', side_effect=mock_jwt_decode_expired):
        response = client.post("/api/v1/agents/", json=sample_agent_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Token has expired" in response.json()["detail"]

    # Mock invalid token
    def mock_jwt_decode_invalid(*args, **kwargs):
        raise jwt.InvalidTokenError("Invalid token")

    with patch('jwt.decode', side_effect=mock_jwt_decode_invalid):
        response = client.post("/api/v1/agents/", json=sample_agent_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token" in response.json()["detail"] 

def test_create_agent_with_missing_org_data(client, db_session, sample_agent_data):
    """
    Test Case: Attempt to create agent with missing organization data
    - Verifies handling of missing org data in token
    - Tests token with no 'o' field
    - Ensures proper error message
    """
    def mock_jwt_decode_no_org(*args, **kwargs):
        return {
            "sub": "1234567890",
            "name": "Test User",
            "iat": 1516239022,
            "fea": "o:all_content"
            # Missing 'o' field
        }

    with patch('jwt.decode', side_effect=mock_jwt_decode_no_org):
        response = client.post("/api/v1/agents/", json=sample_agent_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "No organization data found in token" in response.json()["detail"]

def test_create_agent_with_missing_features(client, db_session, sample_agent_data):
    """
    Test Case: Attempt to create agent with missing features
    - Verifies handling of missing features in token
    - Tests token with no 'fea' field
    - Ensures proper error message
    """
    def mock_jwt_decode_no_features(*args, **kwargs):
        return {
            "sub": "1234567890",
            "name": "Test User",
            "iat": 1516239022,
            "o": {
                "rol": "admin",
                "per": "manage"
            }
            # Missing 'fea' field
        }

    with patch('jwt.decode', side_effect=mock_jwt_decode_no_features):
        response = client.post("/api/v1/agents/", json=sample_agent_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "No feature data found in token" in response.json()["detail"]

def test_create_agent_with_empty_features(client, db_session, sample_agent_data):
    """
    Test Case: Attempt to create agent with empty features
    - Verifies handling of empty features list
    - Tests token with empty 'fea' field
    - Ensures proper error message
    """
    def mock_jwt_decode_empty_features(*args, **kwargs):
        return {
            "sub": "1234567890",
            "name": "Test User",
            "iat": 1516239022,
            "fea": "",  # Empty features
            "o": {
                "rol": "admin",
                "per": "manage"
            }
        }

    with patch('jwt.decode', side_effect=mock_jwt_decode_empty_features):
        response = client.post("/api/v1/agents/", json=sample_agent_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "No feature data found in token" in response.json()["detail"]

def test_create_agent_with_empty_permissions(client, db_session, sample_agent_data):
    """
    Test Case: Attempt to create agent with empty permissions
    - Verifies handling of empty permissions list
    - Tests token with empty 'per' field
    - Ensures proper error message
    """
    def mock_jwt_decode_empty_permissions(*args, **kwargs):
        return {
            "sub": "1234567890",
            "name": "Test User",
            "iat": 1516239022,
            "fea": "o:all_content",
            "o": {
                "rol": "admin",
                "per": ""  # Empty permissions
            }
        }

    with patch('jwt.decode', side_effect=mock_jwt_decode_empty_permissions):
        response = client.post("/api/v1/agents/", json=sample_agent_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Insufficient permissions" in response.json()["detail"] 