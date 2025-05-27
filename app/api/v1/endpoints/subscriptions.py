from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.services.subscription_service import SubscriptionService
from app.models.schemas import AgentSubscriptionCreate, AgentSubscriptionInDB, UserSubscriptionResponse
from app.models.database import AgentDB

router = APIRouter(tags=["subscriptions"])

@router.post("/subscribe", response_model=AgentSubscriptionInDB, status_code=201)
async def subscribe_agent(
    request: Request,
    subscription: AgentSubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """
    Subscribe to an agent.
    """
    # Set the user_id from the current user
    subscription.user_id = current_user["id"]
    
    # Check if agent exists
    agent = db.query(AgentDB).filter(AgentDB.id == subscription.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    subscription_service = SubscriptionService(db)
    # Check if subscription already exists
    existing_subscription = subscription_service.get_active_subscription(
        subscription.user_id,
        subscription.agent_id
    )
    if existing_subscription:
        raise HTTPException(
            status_code=400,
            detail="User already has an active subscription for this agent"
        )
    # Create new subscription
    db_subscription = subscription_service.create_subscription(subscription)
    return subscription_service._db_to_model(db_subscription)

@router.post("/unsubscribe/{subscription_id}", response_model=AgentSubscriptionInDB)
def unsubscribe_agent(
    subscription_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """
    Unsubscribe from an agent.
    """
    subscription_service = SubscriptionService(db)
    
    # Get subscription
    subscription = subscription_service.get_subscription_by_id(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=404,
            detail="Subscription not found"
        )
    
    # Verify if the user is trying to unsubscribe for themselves
    if subscription.user_id != current_user["id"]:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to unsubscribe for another user"
        )
    
    # Unsubscribe and get updated subscription
    updated_subscription = subscription_service.unsubscribe(subscription.user_id, subscription.agent_id)
    
    if not updated_subscription:
        raise HTTPException(
            status_code=404,
            detail="Subscription not found"
        )
    
    return subscription_service._db_to_model(updated_subscription)

@router.get("/user-subscriptions", response_model=List[UserSubscriptionResponse])
async def get_user_subscriptions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """
    Get all subscriptions for the current user.
    Returns a list of subscriptions with agent details.
    """
    subscription_service = SubscriptionService(db)
    return subscription_service.get_user_subscriptions(current_user["id"]) 