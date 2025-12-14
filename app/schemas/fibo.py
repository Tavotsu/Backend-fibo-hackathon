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
from beanie import Document, Indexed
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

class Campaign(Document):
    name: str
    brand_guidelines: BrandGuidelines
    user_id: Indexed(str) # type: ignore
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "campaigns"

class Product(Document):
    campaign_id: str
    image_url: str
    original_filename: str
    user_id: Indexed(str) # type: ignore
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "products"

class Plan(Document):
    campaign_id: str
    product_id: str
    proposed_variations: List[ProposedVariation]
    status: str = "pending"  # pending, executing, completed
    user_id: Indexed(str) # type: ignore
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "plans"

# Request/Response Models
class CampaignCreate(BaseModel):
    name: str
    brand_guidelines: BrandGuidelines

class PlanRequest(BaseModel):
    product_id: str
    variations_count: int = 3

class ExecuteRequest(BaseModel):
    plan_id: str
    selected_variations: List[int]  # Índices de variaciones a ejecutar