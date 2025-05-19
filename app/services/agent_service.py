from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.database import AgentDB
from app.models.schemas import Agent, AgentStatus, PricingModel, AgentCreate, AgentUpdate

class AgentService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_agents(
        self,
        status: Optional[AgentStatus] = None,
        pricing_model: Optional[PricingModel] = None,
        skip: int = 0,
        limit: int = 10
    ) -> List[Agent]:
        query = select(AgentDB)
        
        if status:
            query = query.where(AgentDB.status == status)
        if pricing_model:
            query = query.where(AgentDB.pricing_model == pricing_model)
            
        query = query.order_by(AgentDB.display_order.asc()).offset(skip).limit(limit)
        db_agents = self.db.execute(query).scalars().all()
        
        return [self._db_to_model(agent) for agent in db_agents]

    def get_agent_by_id(self, agent_id: UUID) -> Optional[Agent]:
        query = select(AgentDB).where(AgentDB.id == agent_id)
        db_agent = self.db.execute(query).scalar_one_or_none()
        return self._db_to_model(db_agent) if db_agent else None

    def create_agent(self, agent: AgentCreate) -> Agent:
        db_agent = AgentDB(**agent.model_dump())
        self.db.add(db_agent)
        self.db.commit()
        self.db.refresh(db_agent)
        return self._db_to_model(db_agent)

    def update_agent(self, agent_id: UUID, agent: AgentUpdate) -> Optional[Agent]:
        query = select(AgentDB).where(AgentDB.id == agent_id)
        db_agent = self.db.execute(query).scalar_one_or_none()
        
        if not db_agent:
            return None
        
        update_data = agent.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == "id":
                continue
            if hasattr(db_agent, key):
                setattr(db_agent, key, value)
        
        self.db.commit()
        self.db.refresh(db_agent)
        return self._db_to_model(db_agent)

    def delete_agent(self, agent_id: UUID) -> bool:
        query = select(AgentDB).where(AgentDB.id == agent_id)
        db_agent = self.db.execute(query).scalar_one_or_none()
        
        if not db_agent:
            return False
            
        self.db.delete(db_agent)
        self.db.commit()
        return True

    def _db_to_model(self, db_agent: AgentDB) -> Agent:
        return Agent(
            id=db_agent.id,
            name=db_agent.name,
            title=db_agent.title,
            description=db_agent.description,
            version=db_agent.version,
            imageUrl=db_agent.image_url,
            features=db_agent.features,
            status=db_agent.status,
            pricing_model=db_agent.pricing_model,
            price=db_agent.price,
            display_order=db_agent.display_order,
            created_at=db_agent.created_at,
            updated_at=db_agent.updated_at,
            provider=db_agent.provider,
            language_support=db_agent.language_support,
            tags=db_agent.tags
        ) 