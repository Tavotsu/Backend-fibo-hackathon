from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
from pathlib import Path
import uuid
import logging
import shutil

from app.schemas.fibo import (
    Campaign, CampaignCreate, 
    Product, 
    Plan, PlanRequest, 
    BriaStructuredPrompt,
    ExecuteRequest
)
from app.services.storage import upload_image_to_supabase
from app.services.agent import brand_guidelines_to_variations
from app.services.bria import generate_with_fibo, batch_generate, BriaAPIError
from app.services.jobs import (
    create_job, get_job_status, get_job, Job
)
from app.services.orchestrator import get_orchestrator
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# NUEVOS ENDPOINTS PARA GENERACIÓN ASYNC (compatibles con frontend)
# ============================================================================

@router.post("/generate-async")
async def generate_async(
    background_tasks: BackgroundTasks,
    image: Optional[UploadFile] = File(None),
    prompt: str = Form(...),
    brand_guidelines: str = Form(""),
    variations: int = Form(4),
    aspect_ratio: str = Form("1:1")
):
    """
    Inicia un job de generación asíncrono
    Compatible con el frontend de Marketech
    
    Args:
        image: Imagen de referencia (opcional)
        prompt: Prompt de generación
        brand_guidelines: Guías de marca
        variations: Número de variaciones a generar
        aspect_ratio: Proporción de las imágenes
    
    Returns:
        job_id para consultar el estado
    """
    logger.info(f"Iniciando generación async: prompt='{prompt[:50]}...', variations={variations}")
    
    # Guardar imagen si se proporcionó
    image_path = None
    if image:
        try:
            data_dir = Path(settings.DATA_DIR)
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Generar nombre único
            ext = Path(image.filename or "image.png").suffix or ".png"
            image_filename = f"{uuid.uuid4()}{ext}"
            image_path = str(data_dir / image_filename)
            
            # Guardar archivo
            with open(image_path, "wb") as f:
                shutil.copyfileobj(image.file, f)
            
            logger.info(f"Imagen guardada: {image_path}")
        except Exception as e:
            logger.error(f"Error guardando imagen: {e}")
    
    # Crear job
    job = create_job(
        prompt=prompt,
        brand_guidelines=brand_guidelines,
        variations=variations,
        aspect_ratio=aspect_ratio,
        image_path=image_path
    )
    
    # Ejecutar pipeline en background
    orchestrator = get_orchestrator()
    background_tasks.add_task(orchestrator.run_pipeline, job)
    
    return {"job_id": job.job_id}


@router.get("/jobs/{job_id}")
async def get_job_status_endpoint(job_id: str):
    """
    Obtiene el estado de un job de generación
    
    Args:
        job_id: ID del job
    
    Returns:
        Estado actual del job con progreso y eventos
    """
    status = get_job_status(job_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    return status


# ============================================================================
# ENDPOINTS LEGACY (campañas, productos, planes)
# ============================================================================

# 1. Gestión de Campañas
@router.post("/campaigns", response_model=Campaign)
async def create_campaign(campaign_in: CampaignCreate):
    """Crea una nueva campaña con brand guidelines"""
    new_campaign = Campaign(
        name=campaign_in.name,
        brand_guidelines=campaign_in.brand_guidelines
    )
    await new_campaign.insert()
    logger.info(f"Campaña creada: {new_campaign.id}")
    return new_campaign


# 2. Ingesta de Producto
@router.post("/campaigns/{campaign_id}/upload-product")
async def upload_product(campaign_id: str, file: UploadFile = File(...)):
    """Sube imagen de producto a Supabase"""
    
    # Check if campaign exists
    campaign = await Campaign.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaña no encontrada")
    
    public_url = await upload_image_to_supabase(file)
    if not public_url:
        raise HTTPException(status_code=500, detail="Error subiendo imagen")
    
    new_product = Product(
        campaign_id=str(campaign.id),
        image_url=public_url,
        original_filename=file.filename or "unknown"
    )
    await new_product.insert()
    
    logger.info(f"Producto subido: {new_product.id}")
    
    return {
        "product_id": str(new_product.id),
        "url": public_url,
        "message": "Imagen guardada en Supabase y MongoDB"
    }


# Generate Plan con AI Agent
@router.post("/campaigns/{campaign_id}/generate-plan", response_model=Plan)
async def generate_plan(campaign_id: str, request: PlanRequest):
    """
    Genera plan de variaciones usando AI Agent
    El agente LLM convierte brand guidelines en variaciones creativas con parámetros FIBO
    """
    
    # Verificar campaña y producto
    campaign = await Campaign.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaña no encontrada")
    
    product = await Product.get(request.product_id)
    if not product:
        raise HTTPException(404, "Producto no encontrado")
        
    campaign = await Campaign.get(campaign_id)
    if not campaign:
         raise HTTPException(404, "Campaña no encontrada")

    # USAR AGENTE LLM para generar variaciones
    try:
        variations = await brand_guidelines_to_variations(
            brand_guidelines=campaign.brand_guidelines,
            product_description=f"Producto: {product.original_filename}",
            variations_count=request.variations_count
        )
    except Exception as e:
        logger.error(f"Error generando variaciones: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generando variaciones: {str(e)}")
    
    # Guardar plan en MongoDB
    new_plan = Plan(
        campaign_id=campaign_id,
        product_id=str(product.id),
        proposed_variations=variations,
        status="pending"
    )
    await new_plan.insert()

    logger.info(f"Plan generado con {len(variations)} variaciones: {new_plan.id}")
    
    return new_plan


# Execute Plan con FIBO
@router.post("/campaigns/{campaign_id}/execute")
async def execute_plan(
    campaign_id: str, 
    request: ExecuteRequest,
    background_tasks: BackgroundTasks
):
    """
    Ejecuta plan generando imágenes con FIBO
    Soporta generación batch de múltiples variaciones
    """
    plan = await Plan.get(request.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    # Filtrar variaciones seleccionadas
    selected_variations = [
        plan.proposed_variations[i] 
        for i in request.selected_variations 
        if i < len(plan.proposed_variations)
    ]
    
    if not selected_variations:
        raise HTTPException(status_code=400, detail="No hay variaciones válidas seleccionadas")
    
    logger.info(f"Ejecutando {len(selected_variations)} variaciones con FIBO")
    
    # Generar imágenes con FIBO en modo batch
    try:
        results = await batch_generate(
            [v.bria_parameters for v in selected_variations],
            mode="generate"
        )
    except BriaAPIError as e:
        logger.error(f"Error en FIBO API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generando con FIBO: {str(e)}")
    
    # Actualizar plan con resultados
    for i, result in enumerate(results):
        idx = request.selected_variations[i]
        if "error" not in result:
            plan.proposed_variations[idx].generated_image_url = result.get("image_url")
            plan.proposed_variations[idx].json_prompt = result.get("structured_prompt")
    
    plan.status = "completed"
    await plan.save()
    
    logger.info(f"Plan ejecutado exitosamente: {plan.id}")
    
    return {
        "status": "completed",
        "plan_id": str(plan.id),
        "generated_count": len([r for r in results if "error" not in r]),
        "results": results
    }


# Get Plan (útil para ver resultados)
@router.get("/plans/{plan_id}", response_model=Plan)
async def get_plan(plan_id: str):
    """Obtiene un plan con sus variaciones y resultados"""
    plan = await Plan.get(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    return plan


# List Campaigns
@router.get("/campaigns", response_model=List[Campaign])
async def list_campaigns():
    """Lista todas las campañas"""
    campaigns = await Campaign.find_all().to_list()
    return campaigns

