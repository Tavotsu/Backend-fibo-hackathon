from pydantic import BaseModel, Field
from typing import List, Optional
from beanie import Document 
from datetime import datetime

# Component Models
class BriaParameters(BaseModel):
    """
    Parámetros para generación de imágenes con FIBO
    Soporta los tres modos: Generate, Refine, Inspire
    """
    prompt: str
    camera_angle: str = "eye_level"  # eye_level, high_angle, low_angle, birds_eye, worms_eye
    lighting_mode: str = "studio"    # studio, natural, backlit, dramatic, golden_hour, soft_diffused
    color_grading: Optional[str] = "neutral"  # neutral, warm, cool, cinematic, vibrant, muted
    focus_point: Optional[str] = "center"     # center, rule_of_thirds, left, right
    aspect_ratio: Optional[str] = "1:1"       # 1:1, 16:9, 9:16, 4:5, 3:2
    seed: Optional[int] = None
    
    # Para modo Refine: structured_prompt previo
    structured_prompt: Optional[dict] = None
    
    # Para modo Inspire: URL de imagen de referencia
    reference_image_url: Optional[str] = None

class BrandGuidelines(BaseModel):
    """Guías de marca para generación de variaciones"""
    primary_color: str
    mood: str
    target_audience: Optional[str] = None
    style_preferences: Optional[List[str]] = []

class ProposedVariation(BaseModel):
    """Variación propuesta con parámetros FIBO"""
    concept_name: str
    bria_parameters: BriaParameters
    generated_image_url: Optional[str] = None  # URL después de generar con FIBO
    json_prompt: Optional[dict] = None         # JSON estructurado de FIBO

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
    status: str = "pending"  # pending, executing, completed
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
    selected_variations: List[int]  # Índices de variaciones a ejecutar