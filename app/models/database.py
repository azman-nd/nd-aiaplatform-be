from sqlalchemy import Column, String, Float, DateTime, JSON, Text, Integer, ForeignKey, Boolean, Enum, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, text
from sqlalchemy.orm import relationship
from app.core.database import Base
from uuid import uuid4
from datetime import datetime
import os

IS_SQLITE = os.environ.get("TESTING", "0") == "1" or os.environ.get("SQLALCHEMY_DATABASE_URL", "").startswith("sqlite")

class AgentDB(Base):
    __tablename__ = "agents"
    __table_args__ = {"schema": "aiaplatform"} if not IS_SQLITE else None

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False, unique=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    version = Column(String(20), nullable=False)
    image_url = Column(String(255))
    image_data = Column(LargeBinary, nullable=True)
    features = Column(Text)  # Newline-separated features
    status = Column(String(20), nullable=False, default="active")
    pricing_model = Column(String(20), nullable=False)
    price = Column(Float)
    display_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    provider = Column(String(100), nullable=False)
    language_support = Column(JSON, nullable=False, default=["en"])
    tags = Column(JSON, nullable=False, default=[])
    demo_url = Column(String, nullable=True)
    prod_url = Column(String, nullable=True)

    purchases = relationship("UserAgentPurchaseDB", back_populates="agent")

class UserAgentPurchaseDB(Base):
    __tablename__ = "user_agent_purchases"
    __table_args__ = {"schema": "aiaplatform"} if not IS_SQLITE else None

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String(100), nullable=False)
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey(("aiaplatform.agents.id" if not IS_SQLITE else "agents.id")),
        nullable=False
    )
    purchase_modality = Column(String, nullable=True)
    purchase_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    expiry_date = Column(DateTime, nullable=True)
    ownership_status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    agent = relationship("AgentDB", back_populates="purchases") 