from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.database import UserAgentPurchaseDB, AgentDB
from app.models.schemas import AgentSubscriptionCreate, AgentSubscriptionUpdate, AgentSubscriptionInDB, UserSubscriptionResponse

class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db

    def get_subscription_by_id(self, subscription_id: UUID) -> Optional[UserAgentPurchaseDB]:
        return self.db.query(UserAgentPurchaseDB).filter(
            UserAgentPurchaseDB.id == subscription_id
        ).first()

    def get_subscription(self, user_id: str, agent_id: UUID) -> Optional[UserAgentPurchaseDB]:
        return self.db.query(UserAgentPurchaseDB).filter(
            UserAgentPurchaseDB.user_id == user_id,
            UserAgentPurchaseDB.agent_id == agent_id,
        ).first()

    def get_active_subscription(self, user_id: str, agent_id: UUID) -> Optional[UserAgentPurchaseDB]:
        return self.db.query(UserAgentPurchaseDB).filter(
            UserAgentPurchaseDB.user_id == user_id,
            UserAgentPurchaseDB.agent_id == agent_id,
            UserAgentPurchaseDB.ownership_status == "active"
        ).first()

    def create_subscription(self, subscription: AgentSubscriptionCreate) -> UserAgentPurchaseDB:
        db_subscription = UserAgentPurchaseDB(
            user_id=subscription.user_id,
            agent_id=subscription.agent_id,
            purchase_modality=subscription.purchase_modality or "default",  # Set a default value if None
            purchase_date=subscription.purchase_date or datetime.utcnow(),
            expiry_date=subscription.expiry_date,
            ownership_status=subscription.ownership_status
        )
        
        self.db.add(db_subscription)
        self.db.commit()
        self.db.refresh(db_subscription)
        return db_subscription

    def update_subscription(
        self,
        user_id: str,
        agent_id: UUID,
        update_data: AgentSubscriptionUpdate
    ) -> Optional[UserAgentPurchaseDB]:
        subscription = self.get_active_subscription(user_id, agent_id)
        if not subscription:
            return None

        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(subscription, field, value)

        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def unsubscribe(self, user_id: str, agent_id: UUID) -> Optional[UserAgentPurchaseDB]:
        update_data = AgentSubscriptionUpdate(
            ownership_status="unsubscribed",
            expiry_date=datetime.utcnow()
        )
        return self.update_subscription(user_id, agent_id, update_data)

    def _db_to_model(self, db_subscription: UserAgentPurchaseDB) -> AgentSubscriptionInDB:
        return AgentSubscriptionInDB(
            id=db_subscription.id,
            user_id=db_subscription.user_id,
            agent_id=db_subscription.agent_id,
            purchase_modality=db_subscription.purchase_modality,
            purchase_date=db_subscription.purchase_date,
            expiry_date=db_subscription.expiry_date,
            ownership_status=db_subscription.ownership_status,
            created_at=db_subscription.created_at,
            updated_at=db_subscription.updated_at
        )

    def get_user_subscriptions(self, user_id: str) -> List[UserSubscriptionResponse]:
        """
        Get all subscriptions for a user with agent details.
        Returns a list of subscriptions with agent information.
        """
        subscriptions = self.db.query(
            UserAgentPurchaseDB,
            AgentDB
        ).join(
            AgentDB,
            UserAgentPurchaseDB.agent_id == AgentDB.id
        ).filter(
            UserAgentPurchaseDB.user_id == user_id,
            UserAgentPurchaseDB.ownership_status == "active"
        ).all()

        return [
            UserSubscriptionResponse(
                id=sub.UserAgentPurchaseDB.id,
                agent_id=sub.AgentDB.id,
                agent_name=sub.AgentDB.name,
                agent_title=sub.AgentDB.title,
                agent_description=sub.AgentDB.description,
                agent_image_url=sub.AgentDB.image_url,
                purchase_modality=sub.UserAgentPurchaseDB.purchase_modality,
                purchase_date=sub.UserAgentPurchaseDB.purchase_date,
                expiry_date=sub.UserAgentPurchaseDB.expiry_date,
                ownership_status=sub.UserAgentPurchaseDB.ownership_status,
                created_at=sub.UserAgentPurchaseDB.created_at,
                updated_at=sub.UserAgentPurchaseDB.updated_at
            )
            for sub in subscriptions
        ] 