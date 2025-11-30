"""
Servicio de integración con Bria AI FIBO
Maneja la generación de imágenes usando la API de Bria
"""

import httpx
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.schemas.fibo import BriaParameters
import logging

logger = logging.getLogger(__name__)


class BriaAPIError(Exception):
    """Excepción personalizada para errores de la API de Bria"""
    pass


async def generate_with_fibo(
    bria_params: BriaParameters,
    mode: str = "generate"
) -> Dict[str, Any]:
    """
    Genera imagen usando FIBO de Bria AI
    
    Args:
        bria_params: Parámetros de generación
        mode: Modo de operación ("generate", "refine", "inspire")
    
    Returns:
        Dict con image_url y structured_prompt
    
    Raises:
        BriaAPIError: Si hay error en la API
    """
    
    if not settings.BRIA_API_KEY:
        raise BriaAPIError("BRIA_API_KEY no está configurada")
    
    headers = {
        "api_token": settings.BRIA_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Construir payload según el modo
    payload = _build_payload(bria_params, mode)
    
    url = f"{settings.BRIA_API_URL}{settings.BRIA_IMAGE_GENERATE_ENDPOINT}"
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Imagen generada exitosamente: {result.get('result_url')}")
                return {
                    "image_url": result.get("result_url"),
                    "structured_prompt": result.get("structured_prompt"),
                    "status": result.get("status")
                }
            else:
                error_msg = f"Error FIBO API: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise BriaAPIError(error_msg)
                
    except httpx.TimeoutException:
        raise BriaAPIError("Timeout al conectar con Bria API")
    except httpx.RequestError as e:
        raise BriaAPIError(f"Error de conexión: {str(e)}")


def _build_payload(bria_params: BriaParameters, mode: str) -> Dict[str, Any]:
    """
    Construye el payload JSON para la API de Bria según el modo
    
    FIBO acepta diferentes combinaciones de inputs:
    - prompt: Genera desde texto
    - images: Genera inspirado en imagen
    - images + prompt: Imagen + guía de texto
    - structured_prompt: Recrea imagen exacta
    - structured_prompt + prompt: Refina imagen existente
    """
    
    payload: Dict[str, Any] = {
        "num_results": 1,
        "sync": True  # Esperar resultado síncrono
    }
    
    # Agregar seed si está especificado
    if bria_params.seed is not None:
        payload["seed"] = bria_params.seed
    
    # Agregar aspect_ratio si está especificado
    if bria_params.aspect_ratio:
        payload["aspect_ratio"] = bria_params.aspect_ratio
    
    if mode == "generate":
        # Modo Generate: Solo prompt
        payload["prompt"] = bria_params.prompt
        
    elif mode == "refine":
        # Modo Refine: structured_prompt + nuevo prompt
        if not bria_params.structured_prompt:
            raise BriaAPIError("structured_prompt es requerido para modo 'refine'")
        
        payload["structured_prompt"] = bria_params.structured_prompt
        payload["prompt"] = bria_params.prompt
        
    elif mode == "inspire":
        # Modo Inspire: imagen + prompt opcional
        if not bria_params.reference_image_url:
            raise BriaAPIError("reference_image_url es requerido para modo 'inspire'")
        
        payload["images"] = [bria_params.reference_image_url]
        if bria_params.prompt:
            payload["prompt"] = bria_params.prompt
    
    return payload


async def batch_generate(
    variations: List[BriaParameters],
    mode: str = "generate"
) -> List[Dict[str, Any]]:
    """
    Genera múltiples imágenes en batch
    
    Args:
        variations: Lista de parámetros para cada variación
        mode: Modo de generación
    
    Returns:
        Lista de resultados con image_url y structured_prompt
    """
    results = []
    
    for i, params in enumerate(variations):
        try:
            logger.info(f"Generando variación {i+1}/{len(variations)}")
            result = await generate_with_fibo(params, mode=mode)
            results.append(result)
        except BriaAPIError as e:
            logger.error(f"Error generando variación {i+1}: {str(e)}")
            results.append({
                "error": str(e),
                "image_url": None,
                "structured_prompt": None
            })
    
    return results


async def generate_structured_prompt(prompt: str) -> Dict[str, Any]:
    """
    Genera solo el structured_prompt sin generar la imagen
    Útil para preview o refinamiento posterior
    
    Args:
        prompt: Texto descriptivo
    
    Returns:
        Dict con structured_prompt JSON
    """
    
    if not settings.BRIA_API_KEY:
        raise BriaAPIError("BRIA_API_KEY no está configurada")
    
    headers = {
        "api_token": settings.BRIA_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": prompt
    }
    
    url = f"{settings.BRIA_API_URL}{settings.BRIA_STRUCTURED_PROMPT_ENDPOINT}"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                raise BriaAPIError(f"Error generando structured_prompt: {response.text}")
                
    except httpx.RequestError as e:
        raise BriaAPIError(f"Error de conexión: {str(e)}")
