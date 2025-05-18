from fastapi import APIRouter, HTTPException, Path, Query, Depends
from typing import List, Optional
from uuid import UUID
from clerk_backend_api import Clerk
from clerk_backend_api.models import ClerkErrors, SDKError
from sqlalchemy.orm import Session

from app.models.agent import Agent, AgentStatus, PricingModel
from app.services.agent_service import AgentService
from app.core.database import get_db

router = APIRouter(prefix="/agents", tags=["agents"])

@router.get("/", response_model=List[Agent])
async def list_agents(
    status: Optional[AgentStatus] = None,
    pricing_model: Optional[PricingModel] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Retrieve all agents with optional filtering.
    """
    agent_service = AgentService(db)
    return agent_service.get_all_agents(status, pricing_model, skip, limit)

@router.get("/{agent_id}", response_model=Agent)
async def get_agent(
    agent_id: UUID = Path(..., title="The ID of the agent to get"),
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific agent by ID.
    """
    agent_service = AgentService(db)
    agent = agent_service.get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.post("/", response_model=Agent, status_code=201)
async def create_agent(
    agent: Agent,
    db: Session = Depends(get_db)
):
    """
    Create a new agent.
    """
    agent_service = AgentService(db)
    # Check if an agent with the same name already exists
    existing_agents = agent_service.get_all_agents()
    if any(a.name == agent.name for a in existing_agents):
        raise HTTPException(
            status_code=400,
            detail="An agent with this name already exists"
        )
    
    return agent_service.create_agent(agent)

@router.put("/{agent_id}", response_model=Agent)
async def update_agent(
    agent_id: UUID = Path(..., title="The ID of the agent to update"),
    agent_update: Agent = None,
    db: Session = Depends(get_db)
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
    if any(a.name == agent_update.name and str(a.id) != str(agent_id) for a in all_agents):
        raise HTTPException(
            status_code=400,
            detail="An agent with this name already exists"
        )

    updated_agent = agent_service.update_agent(agent_id, agent_update.model_dump())
    if not updated_agent:
        raise HTTPException(status_code=500, detail="Failed to update agent")
    
    return updated_agent

@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: UUID = Path(..., title="The ID of the agent to delete"),
    db: Session = Depends(get_db)
):
    """
    Delete an agent.
    """
    agent_service = AgentService(db)
    if not agent_service.get_agent_by_id(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    
    success = agent_service.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete agent")
    
    return None

@router.get("/search/", response_model=List[Agent])
async def search_agents(
    query: str = Query(..., min_length=1),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db)
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