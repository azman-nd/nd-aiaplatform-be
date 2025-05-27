from fastapi import APIRouter, HTTPException, Path, Query, Depends, Request, File, UploadFile, Body
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
import base64
import json

from app.models.schemas import Agent, AgentStatus, PricingModel, AgentCreate, AgentUpdate
from app.services.agent_service import AgentService
from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.permissions import check_role_and_permission

# Constants
MAX_IMAGE_SIZE = 50 * 1024  # 50KB in bytes

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
    agent_id: UUID = Path(..., title="The ID of the agent to get"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get a specific agent by ID.
    """
    agent_service = AgentService(db)
    agent = agent_service.get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.post("/", response_model=Agent, status_code=201)
async def create_agent(
    request: Request,
    agent_data: AgentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create a new agent.
    Requires admin role and org:all_content:manage permission.
    """
    await check_role_and_permission(request, current_user, "admin", "o:all_content:manage")

    agent_service = AgentService(db)
    if agent_service.get_agent_by_name(agent_data.name):
        raise HTTPException(status_code=400, detail="An agent with this name already exists")

    if agent_data.image_data:
        try:
            raw_bytes = base64.b64decode(agent_data.image_data)
            if len(raw_bytes) > MAX_IMAGE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail="Image file size exceeds the maximum limit of 50KB."
                )
            agent_data.image_data = raw_bytes
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error decoding image: {str(e)}")

    return agent_service.create_agent(agent_data)

@router.put("/{agent_id}", response_model=Agent)
async def update_agent(
    request: Request,
    agent_id: UUID = Path(..., title="The ID of the agent to update"),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Update an agent.
    """
    try:
        body = await request.json()
        agent_update = AgentUpdate(**body)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    agent_service = AgentService(db)
    existing_agent = agent_service.get_agent_by_id(agent_id)

    if not existing_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Duplicate name check
    all_agents = agent_service.get_all_agents()
    if any(a.name == agent_update.name and str(a.id) != str(agent_id) for a in all_agents):
        raise HTTPException(status_code=400, detail="An agent with this name already exists")

    # Handle image upload if provided
    if image:
        try:
            image_data = await image.read()
            agent_update.image_data = image_data
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")

    updated_agent = agent_service.update_agent(agent_id, agent_update)

    if not updated_agent:
        raise HTTPException(status_code=500, detail="Failed to update agent")
    
    return updated_agent

@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: UUID = Path(..., title="The ID of the agent to delete"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Delete an agent.
    """
    agent_service = AgentService(db)
    if not agent_service.delete_agent(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")

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