from pydantic import BaseModel, Field
from typing import List, Optional
from beanie import Document 
from datetime import datetime

# Component Models
class BriaParameters(BaseModel):
    prompt: str
    camera_angle: str
    lighting_mode: str
    color_grading: Optional[str] = "neutral"
    focus_point: Optional[str] = "center"
    num_inference_steps: Optional[int] = 50

class BrandGuidelines(BaseModel):
    primary_color: str
    mood: str

class ProposedVariation(BaseModel):
    concept_name: str
    bria_parameters: BriaParameters

# MongoDB Document Models
class Campaign(Document):
    name: str
    brand_guidelines: BrandGuidelines
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "campaigns"

class Product(Document):
    campaign_id: str
    image_url: str
    original_filename: str
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "products"

class Plan(Document):
    campaign_id: str
    product_id: str
    proposed_variations: List[ProposedVariation]
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "plans"

# Request/Response Models
class CampaignCreate(BaseModel):
    name: str
    brand_guidelines: BrandGuidelines

class PlanRequest(BaseModel):
    product_id: str
    variations_count: int = 5

class ExecuteRequest(BaseModel):
    plan_id: str
    selected_variations: List[int]