import time
import requests
from typing import Dict, Any, Optional, List
from fastapi import HTTPException
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class BriaV2Client:
    """
    Cliente para la API v2 de Bria.
    Maneja structured prompts y generación de imágenes.
    """
    def __init__(self):
        self.base_url = "https://engine.prod.bria-api.com/v2"  # Hardcoded default or from settings
        self.api_token = settings.BRIA_API_KEY
        self.timeout_sec = float(getattr(settings, 'DEFAULT_TIMEOUT_SEC', 300))
        self.poll_every_sec = float(getattr(settings, 'DEFAULT_POLL_EVERY_SEC', 2))
        
        self.session = requests.Session()
        self.session.headers.update({"api_token": self.api_token})

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = self.base_url.rstrip("/") + "/" + path.lstrip("/")
        try:
            r = self.session.post(url, json=payload, timeout=self.timeout_sec)
            if r.status_code not in (200, 202):
                logger.error(f"Bria API Error ({r.status_code}): {r.text}")
                raise HTTPException(status_code=r.status_code, detail=r.text)
            return r.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Bria Request Failed: {e}")
            raise HTTPException(status_code=503, detail=f"Bria API connection failed: {str(e)}")

    def _get(self, url: str) -> Dict[str, Any]:
        try:
            r = self.session.get(url, timeout=self.timeout_sec)
            if r.status_code != 200:
                logger.error(f"Bria API Error ({r.status_code}): {r.text}")
                raise HTTPException(status_code=r.status_code, detail=r.text)
            return r.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Bria Request Failed: {e}")
            raise HTTPException(status_code=503, detail=f"Bria API connection failed: {str(e)}")

    def structured_prompt_generate(self, prompt: str, image_b64: str) -> Dict[str, Any]:
        """Genera un structured prompt a partir de un texto y una imagen."""
        payload = {
            "prompt": prompt, 
            "images": [image_b64], 
            "sync": False
        }
        return self._post("/structured_prompt/generate", payload)

    def image_generate(self, structured_prompt: str, seed: Optional[int], aspect_ratio: str) -> Dict[str, Any]:
        """Genera una imagen usando un structured prompt."""
        body: Dict[str, Any] = {
            "structured_prompt": structured_prompt,
            "aspect_ratio": aspect_ratio,
            "sync": False,
            "num_results": 1,
            "model_version": "FIBO",
        }
        if seed is not None:
            body["seed"] = int(seed)
        return self._post("/image/generate", body)

    def poll_until_done(self, status_url: str) -> Dict[str, Any]:
        """Hacer polling a un job asíncrono hasta que termine."""
        t0 = time.time()
        while True:
            if time.time() - t0 > self.timeout_sec:
                raise HTTPException(status_code=504, detail="Timeout esperando Bria status.")
            
            data = self._get(status_url)
            st = (data.get("status") or "").upper()
            
            if st in ("COMPLETED", "ERROR", "UNKNOWN", "FAILED"):
                return data
            
            # Si responde con error explícito
            if st == "FAILED":
                 raise HTTPException(status_code=502, detail=f"Bria job failed: {data}")

            time.sleep(self.poll_every_sec)
