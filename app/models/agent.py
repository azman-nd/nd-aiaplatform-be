from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from enum import Enum
from datetime import datetime
from uuid import UUID, uuid4

class AgentCategory(str, Enum):
    TRAVEL_PLANNER = "travel_planner"
    ITINERARY_SPECIALIST = "itinerary_specialist"
    LOCAL_EXPERT = "local_expert"
    BOOKING_ASSISTANT = "booking_assistant"
    CUSTOMER_SUPPORT = "customer_support"

class AgentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"

class PricingModel(str, Enum):
    FREE = "free"
    PAID = "paid"
    SUBSCRIPTION = "subscription"

class AgentCapability(BaseModel):
    name: str
    description: str
    parameters: Optional[dict] = None

class Agent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10)
    version: str = Field(..., pattern="^\\d+\\.\\d+\\.\\d+$")  # Semantic versioning
    category: AgentCategory
    imageUrl: Optional[HttpUrl] = None
    capabilities: List[AgentCapability]
    status: AgentStatus = AgentStatus.ACTIVE
    pricing_model: PricingModel
    price: Optional[float] = None
    icon_url: Optional[HttpUrl] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    rating: Optional[float] = Field(None, ge=0, le=5)
    total_reviews: int = 0
    provider: str
    language_support: List[str] = ["en"]
    tags: List[str] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Travel Pro Max",
                "description": "Advanced travel planning assistant with expertise in luxury travel and custom itineraries",
                "version": "1.0.0",
                "category": "travel_planner",
                "imageUrl":"https://nebuladigital.ai/agents/img/service-desk.png",
                "capabilities": [
                    {
                        "name": "itinerary_planning",
                        "description": "Creates detailed travel itineraries",
                        "parameters": {
                            "max_days": 30,
                            "destinations_limit": 10
                        }
                    }
                ],
                "status": "active",
                "pricing_model": "paid",
                "price": 9.99,
                "provider": "OpenAI",
                "language_support": ["en", "es"],
                "tags": ["luxury", "custom", "international"]
            }
        }
