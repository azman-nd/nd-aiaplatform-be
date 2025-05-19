from fastapi import APIRouter, HTTPException, Path, Query, Depends
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.schemas import Agent, AgentStatus, PricingModel, AgentCreate, AgentUpdate
from app.services.agent_service import AgentService
from app.core.database import get_db
from app.core.auth import get_current_user

router = APIRouter(prefix="/agents", tags=["agents"])

@router.get("/", response_model=List[Agent])
async def get_agents(
    status: Optional[str] = None,
    pricing_model: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Retrieve all agents with optional filtering.
    Results are ordered by display_order.
    """
    agent_service = AgentService(db)
    return agent_service.get_all_agents(status, pricing_model, skip, limit)

@router.get("/{agent_id}", response_model=Agent)
async def get_agent(
    agent_id: UUID = Path(..., title="The ID of the agent to retrieve"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Retrieve a specific agent by ID.
    """
    agent_service = AgentService(db)
    agent = agent_service.get_agent_by_id(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.post("/", response_model=Agent, status_code=201)
async def create_agent(
    agent: AgentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create a new agent.
    
    - **name**: Unique name for the agent
    - **title**: Display title for the agent
    - **description**: Detailed description of the agent
    - **version**: Semantic version (e.g., "1.0.0")
    - **image_url**: Optional URL to agent's image
    - **features**: Newline-separated list of features
    - **status**: Agent status (active/inactive/maintenance/deprecated)
    - **pricing_model**: Pricing model (free/paid/subscription)
    - **price**: Price for paid agents
    - **display_order**: Order in which to display the agent
    - **provider**: Name of the agent provider
    - **language_support**: List of supported languages
    - **tags**: List of tags for the agent
    - **demo_url**: Optional URL to demo environment
    - **prod_url**: Optional URL to production environment
    """
    agent_service = AgentService(db)
    if agent_service.get_agent_by_name(agent.name):
        raise HTTPException(status_code=400, detail="An agent with this name already exists")
    return agent_service.create_agent(agent)

@router.put("/{agent_id}", response_model=Agent)
async def update_agent(
    agent_id: UUID = Path(..., title="The ID of the agent to update"),
    agent_update: AgentUpdate = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Update an existing agent.
    """
    agent_service = AgentService(db)
    existing_agent = agent_service.get_agent_by_id(agent_id)
    if not existing_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    # Duplicate name check
    all_agents = agent_service.get_all_agents()
    if agent_update and any(a.name == agent_update.name and str(a.id) != str(agent_id) for a in all_agents):
        raise HTTPException(status_code=400, detail="An agent with this name already exists")
    updated_agent = agent_service.update_agent(agent_id, agent_update)
    if not updated_agent:
        raise HTTPException(status_code=500, detail="Failed to update agent")
    return updated_agent

@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: UUID = Path(..., title="The ID of the agent to delete"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Delete an agent.
    """
    agent_service = AgentService(db)
    success = agent_service.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"message": "Agent deleted successfully"}

@router.get("/search/", response_model=List[Agent])
async def search_agents(
    query: str = Query(..., min_length=1),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Search agents by name, title, or description.
    """
    agent_service = AgentService(db)
    agents = agent_service.get_all_agents()
    query = query.lower()
    
    filtered_agents = [
        agent for agent in agents
        if query in agent.name.lower() or 
           query in agent.title.lower() or 
           query in agent.description.lower()
    ]
    
    return filtered_agents[skip:skip + limit] 