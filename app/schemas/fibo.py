from pydantic import BaseModel, Field
from typing import List, Literal, Optional

# Strict options for camera angles and lighting modes so the model don't allucinate
CameraAngle = Literal["eye_level", "low_angle", "high_angle", "birds_eye"]
LightingMode = Literal["studio", "natural", "cinematic", "neon"]

class FiboParameters(BaseModel):
    """Estructura estricta para controlar Bria"""
    prompt: str = Field(..., description="Detailed visual description for image generation")
    negative_prompt: Optional[str] = "ugly, blurry, low quality"
    camera_angle: CameraAngle = "eye_level"
    lighting_mode: LightingMode = "studio"
    color_palette: List[str] = Field(default=[], description="List of Hex codes: ['#FFFFFF']")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Luxury perfume bottle on a marble table",
                "camera_angle": "low_angle",
                "lighting_mode": "cinematic",
                "color_palette": ["#FFD700", "#000000"]
            }
        }

class CampaignRequest(BaseModel):
    """Frontend data"""
    product_name: str
    brand_mood: str
    num_variations: int = 3