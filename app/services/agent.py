"""
Servicio de Agente LLM
Convierte brand guidelines en variaciones creativas usando FIBO
"""

from openai import AsyncOpenAI
from app.core.config import settings
from app.schemas.fibo import BrandGuidelines, BriaParameters, ProposedVariation
from typing import List
import json
import logging

logger = logging.getLogger(__name__)

# Cliente OpenAI (inicializado solo si hay API key)
_openai_client = None

def get_openai_client():
    global _openai_client
    if _openai_client is None and settings.OPENAI_API_KEY:
        _openai_client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )
    return _openai_client





async def brand_guidelines_to_variations(
    brand_guidelines: BrandGuidelines,
    product_description: str,
    variations_count: int = 5
) -> List[ProposedVariation]:
    """
    Usa LLM para generar variaciones creativas basadas en brand guidelines
    
    Args:
        brand_guidelines: Guías de marca (colores, mood, etc.)
        product_description: Descripción del producto
        variations_count: Número de variaciones a generar
    
    Returns:
        Lista de ProposedVariation con parámetros FIBO
    """
    
    client = get_openai_client()
    
    if not client:
        logger.warning("OpenAI API key no configurada, usando variaciones mock")
        return _generate_mock_variations(brand_guidelines, product_description, variations_count)
    
    system_prompt = """
Eres un AI Art Director de clase mundial y Trend Forecaster.
Tu objetivo es generar conceptos visuales de ALTO IMPACTO para e-commerce.

FASE 1: ANÁLISIS ESTRATÉGICO
Antes de generar nada, analiza internamente:
1. Categoría del Producto: ¿Es Moda, Tech, Comida, Belleza?
2. Visual Trends 2024/2025: ¿Qué estilos están de moda para esta categoría? (e.g. 'Cyberpunk', 'Cottagecore', 'Minimalist Luxury').
3. Reglas de Nicho:
   - Comida -> Appetite appeal, warm lighting, macro details.
   - Moda -> Dynamic poses, editorial lighting, texture focus.
   - Tech -> Sleek, neon/cool lighting, floating compositions.

FASE 2: GENERACIÓN DE VARIACIONES (Chain of Thought applied)
Genera variaciones que apliquen estas tendencias.
- Usa el parámetro 'creativity_level' para variar desde "Seguro/Comercial" hasta "Disruptivo/Viral".
- Para opciones "Disruptivas", usa ángulos extremos (worms_eye) y colores contrastantes.

FIBO PARAMETERS REFERENCE:
- camera_angle: "eye_level", "high_angle", "low_angle", "birds_eye", "worms_eye"
- lighting_mode: "studio", "natural", "backlit", "dramatic", "golden_hour", "soft_diffused"
- color_grading: "neutral", "warm", "cool", "cinematic", "vibrant", "muted"
- focus_point: "center", "rule_of_thirds", "left", "right"
- aspect_ratio: "1:1", "16:9", "9:16", "4:5", "3:2"

Responde SOLO con el JSON final:
{
  "analysis": {
    "detected_category": "Sneakers",
    "top_trends": ["Y2K Retro", "Futuristic Chrome", "Deconstructed"]
  },
  "variations": [
    {
      "concept_name": "Y2K Retro Vibe",
      "rationale": "Uses 2000s aesthetics which is trending for Gen-Z audiences.",
      "prompt": "Professional product photography, [product], fish-eye lens effect, vibrant nostalgic colors, street style background",
      "camera_angle": "low_angle",
      "lighting_mode": "dramatic",
      "color_grading": "vibrant",
      "focus_point": "center",
      "aspect_ratio": "4:5"
    }
  ]
}
"""
    
    user_prompt = f"""
BRAND GUIDELINES:
- Primary Color: {brand_guidelines.primary_color}
- Mood: {brand_guidelines.mood}
- Target Audience: {brand_guidelines.target_audience or "General"}
- Style Preferences: {', '.join(brand_guidelines.style_preferences) if brand_guidelines.style_preferences else "None specified"}

PRODUCTO: {product_description}

Genera {variations_count} variaciones creativas y profesionales.
Cada variación debe tener un propósito diferente (e.g., hero image, lifestyle shot, detail shot, etc.)
"""
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Modelo más económico y rápido
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.8  # Más creatividad
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Respuesta vacía del LLM")
        
        variations_data = json.loads(content)
        
        # Convertir a ProposedVariation
        variations = []
        for var in variations_data.get("variations", []):
            variations.append(
                ProposedVariation(
                    concept_name=var["concept_name"],
                    bria_parameters=BriaParameters(
                        prompt=var["prompt"],
                        camera_angle=var.get("camera_angle", "eye_level"),
                        lighting_mode=var.get("lighting_mode", "studio"),
                        color_grading=var.get("color_grading", "neutral"),
                        focus_point=var.get("focus_point", "center"),
                        aspect_ratio=var.get("aspect_ratio", "1:1")
                    )
                )
            )
        
        logger.info(f"Generadas {len(variations)} variaciones con LLM")
        return variations
        
    except Exception as e:
        logger.error(f"Error generando variaciones con LLM: {str(e)}")
        # Fallback a variaciones mock
        return _generate_mock_variations(brand_guidelines, product_description, variations_count)


def _generate_mock_variations(
    brand_guidelines: BrandGuidelines,
    product_description: str,
    count: int
) -> List[ProposedVariation]:
    """
    Genera variaciones mock cuando no hay LLM disponible
    Útil para desarrollo y testing
    """
    
    base_prompt = f"{product_description}, professional product photography, {brand_guidelines.mood} mood"
    
    mock_variations = [
        ProposedVariation(
            concept_name="Hero Product Shot",
            bria_parameters=BriaParameters(
                prompt=f"{base_prompt}, clean white background, studio lighting, centered composition",
                camera_angle="eye_level",
                lighting_mode="studio",
                color_grading="neutral",
                focus_point="center",
                aspect_ratio="1:1"
            )
        ),
        ProposedVariation(
            concept_name="Lifestyle Context",
            bria_parameters=BriaParameters(
                prompt=f"{base_prompt}, natural environment, lifestyle photography, soft natural light",
                camera_angle="high_angle",
                lighting_mode="natural",
                color_grading="warm",
                focus_point="rule_of_thirds",
                aspect_ratio="16:9"
            )
        ),
        ProposedVariation(
            concept_name="Dramatic Angle",
            bria_parameters=BriaParameters(
                prompt=f"{base_prompt}, dynamic composition, dramatic lighting, bold shadows",
                camera_angle="low_angle",
                lighting_mode="dramatic",
                color_grading="cinematic",
                focus_point="center",
                aspect_ratio="4:5"
            )
        ),
        ProposedVariation(
            concept_name="Detail Close-up",
            bria_parameters=BriaParameters(
                prompt=f"{base_prompt}, macro photography, detailed texture, soft focus background",
                camera_angle="eye_level",
                lighting_mode="soft_diffused",
                color_grading="vibrant",
                focus_point="center",
                aspect_ratio="1:1"
            )
        ),
        ProposedVariation(
            concept_name="Golden Hour Aesthetic",
            bria_parameters=BriaParameters(
                prompt=f"{base_prompt}, golden hour lighting, warm tones, outdoor setting",
                camera_angle="eye_level",
                lighting_mode="golden_hour",
                color_grading="warm",
                focus_point="rule_of_thirds",
                aspect_ratio="16:9"
            )
        )
    ]
    
    return mock_variations[:count]
