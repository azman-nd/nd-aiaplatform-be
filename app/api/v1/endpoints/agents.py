from fastapi import APIRouter, HTTPException, Path, Query
from typing import List, Optional
from uuid import UUID

from app.models.agent import Agent, AgentCategory, AgentStatus, PricingModel
from app.models.agent_store import AgentStore

router = APIRouter(prefix="/agents", tags=["agents"])
agent_store = AgentStore()

@router.get("/", response_model=List[Agent])
async def list_agents(
    category: Optional[AgentCategory] = None,
    status: Optional[AgentStatus] = None,
    pricing_model: Optional[PricingModel] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100)
):
    """
    Retrieve all agents with optional filtering.
    """
    agents = agent_store.get_all_agents()
    
    # Apply filters if provided
    if category:
        agents = [a for a in agents if a.category == category]
    if status:
        agents = [a for a in agents if a.status == status]
    if pricing_model:
        agents = [a for a in agents if a.pricing_model == pricing_model]
    
    # Apply pagination
    return agents[skip:skip + limit]

@router.get("/{agent_id}", response_model=Agent)
async def get_agent(
    agent_id: UUID = Path(..., title="The ID of the agent to get")
):
    """
    Retrieve a specific agent by ID.
    """
    agent = agent_store.get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.post("/", response_model=Agent, status_code=201)
async def create_agent(agent: Agent):
    """
    Create a new agent.
    """
    # Check if an agent with the same name already exists
    existing_agents = agent_store.get_all_agents()
    if any(a.name == agent.name for a in existing_agents):
        raise HTTPException(
            status_code=400,
            detail="An agent with this name already exists"
        )
    
    return agent_store.add_agent(agent)

@router.put("/{agent_id}", response_model=Agent)
async def update_agent(
    agent_id: UUID = Path(..., title="The ID of the agent to update"),
    agent_update: Agent = None
):
    """
    Update an existing agent.
    """
    existing_agent = agent_store.get_agent_by_id(agent_id)
    if not existing_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    updated_agent = agent_store.update_agent(agent_id, agent_update.model_dump())
    if not updated_agent:
        raise HTTPException(status_code=500, detail="Failed to update agent")
    
    return updated_agent

@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: UUID = Path(..., title="The ID of the agent to delete")
):
    """
    Delete an agent.
    """
    if not agent_store.get_agent_by_id(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    
    success = agent_store.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete agent")
    
    return None

@router.get("/category/{category}", response_model=List[Agent])
async def get_agents_by_category(
    category: AgentCategory,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100)
):
    """
    Retrieve agents by category.
    """
    agents = [a for a in agent_store.get_all_agents() if a.category == category]
    return agents[skip:skip + limit]

@router.get("/search/", response_model=List[Agent])
async def search_agents(
    query: str = Query(..., min_length=1),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100)
):
    """
    Search agents by name or description.
    """
    agents = agent_store.get_all_agents()
    query = query.lower()
    
    filtered_agents = [
        agent for agent in agents
        if query in agent.name.lower() or query in agent.description.lower()
    ]
    
    return filtered_agents[skip:skip + limit] 