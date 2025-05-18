from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.database import AgentDB
from app.models.agent import Agent, AgentStatus, PricingModel

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
            
        query = query.offset(skip).limit(limit)
        db_agents = self.db.execute(query).scalars().all()
        
        return [self._db_to_model(agent) for agent in db_agents]

    def get_agent_by_id(self, agent_id: UUID) -> Optional[Agent]:
        query = select(AgentDB).where(AgentDB.id == agent_id)
        db_agent = self.db.execute(query).scalar_one_or_none()
        return self._db_to_model(db_agent) if db_agent else None

    def create_agent(self, agent: Agent) -> Agent:
        db_agent = AgentDB(
            name=agent.name,
            title=agent.title,
            description=agent.description,
            version=agent.version,
            image_url=str(agent.imageUrl) if agent.imageUrl else None,
            features=agent.features,
            status=agent.status,
            pricing_model=agent.pricing_model,
            price=agent.price,
            provider=agent.provider,
            language_support=agent.language_support,
            tags=agent.tags
        )
        self.db.add(db_agent)
        self.db.commit()
        self.db.refresh(db_agent)
        return self._db_to_model(db_agent)

    def update_agent(self, agent_id: UUID, agent_data: dict) -> Optional[Agent]:
        query = select(AgentDB).where(AgentDB.id == agent_id)
        db_agent = self.db.execute(query).scalar_one_or_none()
        
        if not db_agent:
            return None
        
        for key, value in agent_data.items():
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
            created_at=db_agent.created_at,
            updated_at=db_agent.updated_at,
            provider=db_agent.provider,
            language_support=db_agent.language_support,
            tags=db_agent.tags
        ) 