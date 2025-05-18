import pytest
from uuid import UUID
from fastapi import status
from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.core.database import Base, get_db
from app.main import app
from fastapi.testclient import TestClient
from typing import Generator

# Database session fixture
@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    # Create a new database session for each test
    session = next(get_db())
    try:
        yield session
    finally:
        session.close()

# Client fixture with database session
@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
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
        "features": "Feature 1\nFeature 2\nFeature 3",
        "status": "active",
        "pricing_model": "paid",
        "price": 9.99,
        "provider": "Test Provider",
        "language_support": ["en"],
        "tags": ["test", "sample"]
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

def test_create_agent(client, sample_agent_data):
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
    assert UUID(data["id"])  # Verify UUID format

def test_create_agent_duplicate_name(client, sample_agent_data):
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

def test_get_agent(client, sample_agent_data):
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

def test_update_agent(client, sample_agent_data):
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

    response = client.put(f"/api/v1/agents/{agent_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == agent_id
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]

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

def test_delete_agent(client, sample_agent_data):
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