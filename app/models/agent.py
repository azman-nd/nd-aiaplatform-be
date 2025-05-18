from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from typing import List, Optional, Literal
from datetime import datetime
from uuid import UUID, uuid4

# Define valid values as type aliases
AgentStatus = Literal["active", "inactive", "maintenance", "deprecated"]
PricingModel = Literal["free", "paid", "subscription"]

class AgentCapability(BaseModel):
    name: str
    description: str
    parameters: Optional[dict] = None

class Agent(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Job Description Writer",
                "title": "AI Job Description Generator",
                "description": "Create professional job descriptions with AI assistant that knows your industry and company",
                "version": "1.0.0",
                "imageUrl": "https://nebuladigital.ai/agents/img/jd-writer.png",
                "features": "Input few words, get polished JD\nIndustry & Company context\nConversational & In-Place editing",
                "status": "active",
                "pricing_model": "paid",
                "price": 9.99,
                "provider": "Nebula Digital",
                "language_support": ["en"],
                "tags": ["hr", "recruitment", "job-description"]
            }
        }
    )

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10)
    version: str = Field(..., pattern="^\\d+\\.\\d+\\.\\d+$")  # Semantic versioning
    imageUrl: Optional[HttpUrl] = None
    features: str  # Newline-separated string of features
    status: AgentStatus = "active"
    pricing_model: PricingModel
    price: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    provider: str
    language_support: List[str] = ["en"]
    tags: List[str] = []
