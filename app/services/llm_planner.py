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
    def __init__(self):
        self.host = getattr(settings, 'OLLAMA_HOST', "http://127.0.0.1:11434")
        self.model = getattr(settings, 'OLLAMA_MODEL', "deepseek-r1:8b")
        self.temperature = 0.7
        self.enabled = True
        
        # Verificar conexión inicial (opcional, no bloqueante)
        try:
             requests.get(f"{self.host}/api/tags", timeout=1.0)
        except Exception:
            logger.warning("Ollama no parece estar accesible. Se usará fallback.")

    def _safe_json_extract(self, text: str) -> Optional[str]:
        """Intenta extraer un bloque JSON válido de un texto."""
        if not text: return None
        try:
            json.loads(text)
            return text
        except:
            pass
            
        start = min([i for i in [text.find("{"), text.find("[")] if i != -1], default=-1)
        if start == -1: return None
        
        stack = []
        for i in range(start, len(text)):
            ch = text[i]
            if ch in "{[":
                stack.append(ch)
            elif ch in "}]":
                if not stack: continue
                stack.pop()
                if not stack:
                    cand = text[start:i+1]
                    try:
                        json.loads(cand)
                        return cand
                    except:
                        return None
        return None

    def propose_patches(self, user_prompt: str, base_sp: Dict[str, Any], brand_ctx: str, n: int) -> List[Dict[str, Any]]:
        """
        Genera N variaciones (patches) del prompt base usando el LLM.
        """
        system = (
            "You are a World-Class Art Director and Expert Photographer. "
            "Your goal is to take a simple product and create STUNNING, AWARD-WINNING visual concepts for it. "
            "Do NOT just describe the product. Build a WORLD around it. "
            "Use technical photography terms (Lighting, Lens, Angle, Film Stock) from the provided context. "
            "\n\n"
            "Output ONLY valid JSON. Return an array of exactly N patch objects. "
            "Each patch is a partial JSON dict to merge into the base structured_prompt. "
            "Refine 'background_prompt', 'lighting_prompt', 'style_prompt', 'camera_prompt' fields aggressively. "
            "\n\n"
            "RULES:"
            "1. Transform the scene completely. If prompt is 'perfume', don't just put it on a table. Put it on a floating rock in space, or inside a melting glacier."
            "2. Use specific lighting: 'Volumetric god rays', 'Neon rim lighting', 'Soft diffused window light'."
            "3. Use specific composition: 'Low angle hero shot', 'Macro detail with bokeh'."
            "4. Keep the product identity (logo/text) intact, but EVERYTHING around it must change."
            "5. Make it look EXPENSIVE and CINEMATIC."
        ).replace("N", str(n))

        # RAG Context injection logic should be here or handled
        rag_text = brand_ctx if brand_ctx else "No specific brand guidelines."

        # Simplify payload structure for clarity
        user_msg = (
            f"Product/Prompt: {user_prompt}\n"
            f"Context/Guidelines: {rag_text}\n\n"
            f"Create {n} DISTINCT and DRAMATIC variations."
            f"Base SP: {json.dumps(base_sp)}"
        )
        
        model_payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg}
            ],
            "stream": False,
            "options": {"temperature": 0.9} # High creativity
        }

        try:
            # Intentar llamar a Ollama
            resp = requests.post(f"{self.host}/api/chat", json=model_payload, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("message", {}).get("content", "")
                extracted = self._safe_json_extract(content)
                
                if extracted:
                    patches = json.loads(extracted)
                    if isinstance(patches, list):
                        # Asegurar que tenemos N parches
                        patches = patches[:n]
                        while len(patches) < n:
                            patches.append({})
                        return [p if isinstance(p, dict) else {} for p in patches]
        except Exception as e:
            logger.warning(f"Error llamando a LLM: {e}. Usando fallback.")

        return self._fallback(n)

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
