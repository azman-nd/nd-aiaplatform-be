from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from typing import List, Optional, Literal, Union
from datetime import datetime
from uuid import UUID, uuid4

# Define valid values as type aliases
AgentStatus = Literal["active", "inactive", "maintenance", "deprecated", "pending"]
PricingModel = Literal["free", "paid", "subscription"]

class AgentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10)
    version: str = Field(..., pattern="^\\d+\\.\\d+\\.\\d+$")  # Semantic versioning
    image_url: Optional[HttpUrl] = None
    image_data: Optional[bytes] = None
    features: str  # Newline-separated string of features
    status: AgentStatus = "active"
    pricing_model: PricingModel
    price: Optional[float] = None
    display_order: int = Field(default=0)
    provider: str
    language_support: List[str] = ["en"]
    tags: List[str] = []
    demo_url: Optional[str] = None
    prod_url: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Job Description Writer",
                "title": "AI Job Description Generator",
                "description": "Create professional job descriptions with AI assistant that knows your industry and company",
                "version": "1.0.0",
                "image_url": "https://nebuladigital.ai/agents/img/jd-writer.png",
                "features": "Input few words, get polished JD\nIndustry & Company context\nConversational & In-Place editing",
                "status": "active",
                "pricing_model": "paid",
                "price": 9.99,
                "provider": "Nebula Digital",
                "language_support": ["en"],
                "tags": ["hr", "recruitment", "job-description"],
                "display_order": 1,
                "demo_url": "https://demo.example.com",
                "prod_url": "https://prod.example.com"
            }
        }
    )

class AgentCreate(AgentBase):
    pass

class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=10)
    version: Optional[str] = Field(None, pattern="^\\d+\\.\\d+\\.\\d+$")
    image_url: Optional[HttpUrl] = None
    image_data: Optional[bytes] = None
    features: Optional[str] = None
    status: Optional[AgentStatus] = None
    pricing_model: Optional[PricingModel] = None
    price: Optional[float] = None
    display_order: Optional[int] = None
    provider: Optional[str] = None
    language_support: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    demo_url: Optional[str] = None
    prod_url: Optional[str] = None

class Agent(AgentBase):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict(from_attributes=True)
    demo_url: Optional[str] = None
    prod_url: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "example-agent",
                "title": "Example Agent",
                "description": "This is an example agent that demonstrates the required fields and their formats.",
                "version": "1.0.0",
                "image_url": "https://example.com/image.png",
                "features": "Feature 1\nFeature 2\nFeature 3",
                "status": "active",
                "pricing_model": "paid",
                "price": 9.99,
                "display_order": 1,
                "created_at": "2024-03-14T12:00:00Z",
                "updated_at": "2024-03-14T12:00:00Z",
                "provider": "Example Provider",
                "language_support": ["en"],
                "tags": ["example", "test"],
                "demo_url": "https://demo.example.com",
                "prod_url": "https://prod.example.com"
            }
        }
    )

class AgentSubscriptionBase(BaseModel):
    user_id: Optional[str] = None
    agent_id: UUID
    purchase_modality: Optional[str] = None
    purchase_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    ownership_status: Optional[str] = "active"

class AgentSubscriptionCreate(AgentSubscriptionBase):
    pass

class AgentSubscriptionUpdate(BaseModel):
    ownership_status: str
    expiry_date: Optional[datetime] = None

class AgentSubscriptionInDB(AgentSubscriptionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserSubscriptionResponse(BaseModel):
    """Schema for user's subscription response"""
    id: UUID
    agent_id: UUID
    agent_name: str
    agent_title: str
    agent_description: str
    agent_image_url: Optional[str]
    purchase_modality: str
    purchase_date: datetime
    expiry_date: Optional[datetime]
    ownership_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) 