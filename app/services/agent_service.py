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

    def get_agent_by_id(self, agent_id: UUID) -> Optional[AgentDB]:
        return self.db.query(AgentDB).filter(AgentDB.id == agent_id).first()

    def get_agent_by_name(self, name: str) -> Optional[AgentDB]:
        return self.db.query(AgentDB).filter(AgentDB.name == name).first()

    def create_agent(self, agent: AgentCreate) -> AgentDB:
        db_agent = AgentDB(
            name=agent.name,
            title=agent.title,
            description=agent.description,
            version=agent.version,
            image_url=str(agent.image_url) if agent.image_url else None,
            features=agent.features,
            status=agent.status,
            pricing_model=agent.pricing_model,
            price=agent.price,
            display_order=agent.display_order,
            provider=agent.provider,
            language_support=agent.language_support,
            tags=agent.tags,
            demo_url=agent.demo_url,
            prod_url=agent.prod_url
        )
        self.db.add(db_agent)
        self.db.commit()
        self.db.refresh(db_agent)
        return db_agent

    def update_agent(self, agent_id: UUID, agent: AgentUpdate) -> Optional[AgentDB]:
        db_agent = self.get_agent_by_id(agent_id)
        if not db_agent:
            return None

        update_data = agent.model_dump(exclude_unset=True)
        if "image_url" in update_data and update_data["image_url"]:
            update_data["image_url"] = str(update_data["image_url"])

        for key, value in update_data.items():
            setattr(db_agent, key, value)

        self.db.commit()
        self.db.refresh(db_agent)
        return db_agent

    def delete_agent(self, agent_id: UUID) -> bool:
        db_agent = self.get_agent_by_id(agent_id)
        if not db_agent:
            return False
        self.db.delete(db_agent)
        self.db.commit()
        return True

    def list_agents(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        pricing_model: Optional[str] = None
    ) -> List[AgentDB]:
        query = self.db.query(AgentDB)
        
        if status:
            query = query.filter(AgentDB.status == status)
        if pricing_model:
            query = query.filter(AgentDB.pricing_model == pricing_model)
            
        return query.order_by(AgentDB.display_order).offset(skip).limit(limit).all()

    def _db_to_model(self, db_agent: AgentDB) -> Agent:
        return Agent(
            id=db_agent.id,
            name=db_agent.name,
            title=db_agent.title,
            description=db_agent.description,
            version=db_agent.version,
            image_url=db_agent.image_url,
            features=db_agent.features,
            status=db_agent.status,
            pricing_model=db_agent.pricing_model,
            price=db_agent.price,
            display_order=db_agent.display_order,
            created_at=db_agent.created_at,
            updated_at=db_agent.updated_at,
            provider=db_agent.provider,
            language_support=db_agent.language_support,
            tags=db_agent.tags,
            demo_url=db_agent.demo_url,
            prod_url=db_agent.prod_url
        ) 