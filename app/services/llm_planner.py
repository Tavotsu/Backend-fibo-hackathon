import json
import os
from typing import List, Dict, Any, Optional
import requests
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class LLMPlanner:
    """
    Planificador que usa LLM (Ollama) para crear variaciones de prompts.
    Incluye fallback si Ollama no está disponible.
    """
    def __init__(self) -> None:
        # Configuración "Agnóstica" (OpenAI, Groq, DeepSeek)
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL
        self.model = settings.LLM_MODEL_NAME
        
        self.client = None
        if self.api_key:
            from openai import OpenAI  # sync client for simplicity in this flow, or Async if method is async
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            logger.warning("OPENAI_API_KEY no encontrada. Se usará fallback dummy.")

    def propose_patches(self, user_prompt: str, base_sp: Dict[str, Any], brand_ctx: str, n: int) -> List[Dict[str, Any]]:
        """
        Genera N variaciones (patches) usando el LLM configurado (Groq/OpenAI).
        """
        if not self.client:
            return self._fallback(n)
            
        system = (
            "Eres un AI Art Director de clase mundial y Trend Forecaster. "
            "Tu objetivo es generar conceptos visuales de ALTO IMPACTO para e-commerce. "
            "\n\n"
            "FASE 1: ANÁLISIS ESTRATÉGICO\n"
            "Analiza internamente: Categoría (Moda, Tech, Comida), Visual Trends 2024/2025, y Reglas de Nicho.\n"
            "\n"
            "FASE 2: GENERACIÓN DE VARIACIONES (Chain of Thought applied)\n"
            "Genera variaciones que apliquen estas tendencias. "
            "Usa el parámetro 'creativity_level' para variar desde 'Seguro' hasta 'Disruptivo'. "
            "Para opciones 'Disruptivas', usa ángulos extremos (worms_eye) y colores contrastantes.\n"
            "\n"
            "Output ONLY valid JSON. Return an array of exactly N patch objects.\n"
            "Each patch is a partial JSON dict to merge into the base structured_prompt.\n"
            "Format: [ { patch_1 }, { patch_2 }, ... ]\n"
        )
        
        user_msg = (
            f"Product/Prompt: {user_prompt}\n"
            f"Context/Guidelines: {brand_ctx}\n\n"
            f"Create {n} DISTINCT and DRAMATIC variations based on Analysis."
            f"Base SP: {json.dumps(base_sp)}"
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_msg}
                ],
                # response_format={"type": "json_object"}, # Groq supports this usually
                temperature=0.8
            )
            
            content = response.choices[0].message.content
            extracted = self._safe_json_extract(content)
            
            if extracted:
                patches = json.loads(extracted)
                if isinstance(patches, dict) and "variations" in patches:
                    patches = patches["variations"] # Handle if model wraps in key
                
                if isinstance(patches, list):
                    # Ensure N items
                    return patches[:n] + [{}] * (n - len(patches))
                    
        except Exception as e:
            logger.exception(f"Error LLM ({self.model}): {e}")
            
        return self._fallback(n)

    @staticmethod
    def _safe_json_extract(text: str) -> Optional[str]:
        """Extrae el primer bloque JSON válido de un string (hacky robustez)."""
        if not text:
            return None
        text = text.strip()
        # Remove markdown fences
        if text.startswith("```"):
            text = text.strip("`")
            # drop lang
            if "\n" in text:
                text = text.split("\n", 1)[1]
        
        text = text.strip()
        
        # Find start
        start_candidates = [i for i in (text.find("{"), text.find("[")) if i != -1]
        if not start_candidates:
            return None
            
        start = min(start_candidates)
        return text[start:]

    def _fallback(self, n: int) -> List[Dict[str, Any]]:
        """Presets de fallback si falla el LLM."""
        presets = [
            {"lighting":{"conditions":"studio softbox"},"photographic_characteristics":{"camera_angle":"eye-level","depth_of_field":"shallow"},
             "background_setting":"clean premium studio background","aesthetics":{"mood_atmosphere":"premium minimal","color_scheme":"brand-aligned"}},
            {"lighting":{"conditions":"golden hour"},"photographic_characteristics":{"camera_angle":"three-quarter","depth_of_field":"medium"},
             "background_setting":"subtle lifestyle scene (out-of-focus)","aesthetics":{"mood_atmosphere":"warm aspirational","color_scheme":"warm + brand accent"}},
            {"lighting":{"conditions":"dramatic rim light"},"photographic_characteristics":{"camera_angle":"low angle","depth_of_field":"shallow"},
             "background_setting":"dark premium backdrop","aesthetics":{"mood_atmosphere":"bold luxury","color_scheme":"dark + brand accent"}},
            {"lighting":{"conditions":"top light diffused"},"photographic_characteristics":{"camera_angle":"top-down flat lay","depth_of_field":"deep"},
             "background_setting":"flat lay surface (stone/wood) minimal props","aesthetics":{"mood_atmosphere":"editorial clean","color_scheme":"neutral + brand accent"}},
        ]
        out = presets[:n]
        while len(out) < n:
            out.append({})
        return out
