from pydantic import BaseModel, Field
from typing import List, Optional, Literal

# Estructuras Internas del JSON de Bria v2

class BriaObject(BaseModel):
    description: str
    location: str
    relationship: Optional[str] = None
    relative_size: Optional[str] = None
    shape_and_color: Optional[str] = None
    texture: Optional[str] = None
    appearance_details: Optional[str] = None
    number_of_objects: Optional[int] = 1
    orientation: Optional[str] = None

class BriaLighting(BaseModel):
    conditions: str = Field(..., description="e.g., Bright, natural light, studio")
    direction: str = Field(..., description="e.g., Soft, diffused light from above")
    shadows: str = Field(..., description="e.g., Soft, subtle shadows")

class BriaAesthetics(BaseModel):
    composition: str
    color_scheme: str
    mood_atmosphere: str
    preference_score: str = "very high"
    aesthetic_score: str = "very high"

class BriaPhotoCharacteristics(BaseModel):
    depth_of_field: str
    focus: str
    camera_angle: str = Field(..., description="e.g., Eye-level, low_angle, birds_eye")
    lens_focal_length: str = Field(..., description="e.g., 50mm, 35mm, macro")

# EL OBJETO PRINCIPAL (Structured Prompt)
class BriaStructuredPrompt(BaseModel):
    """Esta es la estructura exacta que espera Bria v2"""
    short_description: str = Field(..., description="Resumen fotorealista detallado de la imagen completa")
    objects: List[BriaObject]
    background_setting: str
    lighting: BriaLighting
    aesthetics: BriaAesthetics
    photographic_characteristics: BriaPhotoCharacteristics
    style_medium: str = "photograph"
    context: Optional[str] = None
    artistic_style: str = "realistic, detailed"

# Wrappers para tu API
class AgentOutput(BaseModel):
    """Lo que devuelve el Agente (una lista de opciones)"""
    variations: List[BriaStructuredPrompt]

# Modelos de base de datos (usando lo que ya tenías, ajustado)
from beanie import Document
from datetime import datetime

class Plan(Document):
    campaign_id: str
    product_id: str
    # Guardamos la lista de prompts estructurados
    proposed_variations: List[BriaStructuredPrompt] 
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "plans"

class BrandGuidelines(BaseModel):
    mood: str
    style_preferences: List[str] = Field(default_factory=list)
    colors: List[str] = Field(default_factory=list)

class CampaignCreate(BaseModel):
    name: str
    brand_guidelines: BrandGuidelines

class Campaign(Document):
    name: str
    brand_guidelines: BrandGuidelines
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

class PlanRequest(BaseModel):
    product_id: str
    variations_count: int = 3

class ExecuteRequest(BaseModel):
    plan_id: str
    selected_variations: List[int]