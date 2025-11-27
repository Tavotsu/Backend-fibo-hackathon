import httpx
import os
import json
from app.schemas.fibo import BriaStructuredPrompt
from typing import Optional

# Usamos el endpoint síncrono para la hackatón (más fácil de manejar)
# Si prefieres async, cambia sync=False y maneja el status_url.
BRIA_ENDPOINT = "https://engine.prod.bria-api.com/v2/image/generate"
BRIA_API_TOKEN = os.getenv("BRIA_API_TOKEN")

async def generate_image_bria(structured_data: BriaStructuredPrompt) -> Optional[str]:
    """
    Envía el JSON estructurado a Bria v2 para generar la imagen.
    """
    if not BRIA_API_TOKEN:
        print("⚠️ Error: Falta BRIA_API_TOKEN en .env")
        return None

    # Convertimos el objeto Pydantic a un string JSON válido
    # Bria espera el campo 'structured_prompt' como un string, no un objeto anidado.
    structured_prompt_string = structured_data.model_dump_json()

    payload = {
        "structured_prompt": structured_prompt_string,
        "model_version": "FIBO", # Forzamos el uso del modelo FIBO
        "sync": True,            # Esperamos la respuesta (timeout alto necesario)
        "num_results": 1,
        "aspect_ratio": "1:1"    # Puedes parametrizar esto también
    }

    headers = {
        "api_token": BRIA_API_TOKEN,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=120.0) as client: 
        try:
            print("🎨 Enviando JSON Estructurado a Bria FIBO...")
            response = await client.post(BRIA_ENDPOINT, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                # La respuesta exitosa v2 suele tener la imagen en data['result']['image_url']
                # Ojo: revisa la respuesta exacta si falla, a veces cambia la estructura.
                image_url = data.get("result", {}).get("image_url")
                if image_url:
                    return image_url
                else:
                    print(f"⚠️ Respuesta Bria inesperada: {data}")
                    return None
            else:
                print(f"❌ Error Bria API ({response.status_code}): {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error de conexión con Bria: {e}")
            return None