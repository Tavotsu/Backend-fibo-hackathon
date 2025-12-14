from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import List
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
import uuid
import logging
from app.api import deps
from fastapi import Depends

router = APIRouter()
logger = logging.getLogger(__name__)

# 1. Gestión de Campañas
@router.post("/campaigns", response_model=Campaign)
async def create_campaign(
    campaign_in: CampaignCreate,
    current_user: deps.AuthUser = Depends(deps.get_current_user)
):
    """Crea una nueva campaña con brand guidelines"""
    new_campaign = Campaign(
        name=campaign_in.name,
        brand_guidelines=campaign_in.brand_guidelines,
        user_id=current_user.id
    )
    await new_campaign.insert()
    logger.info(f"Campaña creada: {new_campaign.id}")
    return new_campaign

# 2. Ingesta de Producto
@router.post("/campaigns/{campaign_id}/upload-product")
async def upload_product(
    campaign_id: str, 
    file: UploadFile = File(...),
    current_user: deps.AuthUser = Depends(deps.get_current_user)
):
    """Sube imagen de producto a Supabase"""
    
    # Check if campaign exists and belongs to user
    campaign = await Campaign.get(campaign_id)
    if not campaign or campaign.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Campaña no encontrada")
    
    public_url = await upload_image_to_supabase(file, user_id=current_user.id)
    if not public_url:
        raise HTTPException(status_code=500, detail="Error subiendo imagen")
    
    new_product = Product(
        campaign_id=str(campaign.id),
        image_url=public_url,
        original_filename=file.filename or "unknown",
        user_id=current_user.id
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
async def generate_plan(
    campaign_id: str, 
    request: PlanRequest,
    current_user: deps.AuthUser = Depends(deps.get_current_user)
):
    """
    Genera plan de variaciones usando AI Agent
    El agente LLM convierte brand guidelines en variaciones creativas con parámetros FIBO
    """
    
    # Verificar campaña y producto
    campaign = await Campaign.get(campaign_id)
    if not campaign or campaign.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Campaña no encontrada")
    
    product = await Product.get(request.product_id)
    if not product or product.user_id != current_user.id:
        raise HTTPException(404, "Producto no encontrado")

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
        status="pending",
        user_id=current_user.id
    )
    await new_plan.insert()

    logger.info(f"Plan generado con {len(variations)} variaciones: {new_plan.id}")
    
    return new_plan

# Execute Plan con FIBO
@router.post("/campaigns/{campaign_id}/execute")
async def execute_plan(
    campaign_id: str, 
    request: ExecuteRequest,
    background_tasks: BackgroundTasks,
    current_user: deps.AuthUser = Depends(deps.get_current_user)
):
    """
    Ejecuta plan generando imágenes con FIBO
    Soporta generación batch de múltiples variaciones
    """
    plan = await Plan.get(request.plan_id)
    if not plan or plan.user_id != current_user.id:
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
async def get_plan(
    plan_id: str,
    current_user: deps.AuthUser = Depends(deps.get_current_user)
):
    """Obtiene un plan con sus variaciones y resultados"""
    plan = await Plan.get(plan_id)
    if not plan or plan.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    return plan

# List User Plans (History)
@router.get("/plans", response_model=List[Plan])
async def list_plans(current_user: deps.AuthUser = Depends(deps.get_current_user)):
    """Lista todos los planes (historial) del usuario, ordenados por fecha"""
    return await Plan.find(Plan.user_id == current_user.id).sort("-created_at").to_list()

# List Campaigns
@router.get("/campaigns", response_model=List[Campaign])
async def list_campaigns(current_user: deps.AuthUser = Depends(deps.get_current_user)):
    """Lista todas las campañas"""
    campaigns = await Campaign.find(Campaign.user_id == current_user.id).to_list()
    return campaigns

# -------------------------------------------------------------------------
# NEW: Async Generation Endpoints (Playground / Direct)
# -------------------------------------------------------------------------

from fastapi import Form
from app.services import jobs
from app.schemas.fibo import BriaParameters

@router.post("/generate-async")
async def generate_async(
    background_tasks: BackgroundTasks,
    prompt: str = Form(...),
    image: UploadFile = File(None),
    brand_guidelines: str = Form(None),
    variations: int = Form(1),
    aspect_ratio: str = Form("1:1"),
    current_user: deps.AuthUser = Depends(deps.get_current_user)
):
    """
    Endpoint asíncrono para generar imágenes (Playground Flow).
    Sube imagen (si existe), crea Job y procesa en background.
    """
    # 1. Upload Image if present
    public_url = None
    if image:
        # Check file size/type if needed
        public_url = await upload_image_to_supabase(image, user_id=current_user.id)
        if not public_url:
            raise HTTPException(500, "Failed to upload input image to storage.")
    
    # Validate Variations
    if variations < 1 or variations > 8:
        raise HTTPException(status_code=400, detail="Variations must be between 1 and 8")

    # 2. Create Job
    job = jobs.create_job(prompt, brand_guidelines, variations, aspect_ratio, public_url, user_id=current_user.id)
    
    # 3. Start Background Task
    background_tasks.add_task(
        process_generation_job, 
        job.job_id, 
        prompt, 
        public_url, 
        variations, 
        brand_guidelines,
        current_user.id  # PASS USER ID
    )
    
    return {"job_id": job.job_id, "status": "queued"}

# Redefine process_generation_job to include persistence
async def process_generation_job(
    job_id: str, 
    prompt: str, 
    image_url: str = None, 
    variations: int = 4, 
    brand_guidelines: str = None,
    user_id: str = None # Now accepts user_id
):
    try:
        jobs.update_job(job_id, stage=jobs.JobStage.STARTED, progress=10)
        
        # Use Orchestrator if available for smarter generation, or fallback to loop
        # For simplicity and robust persistence, we use the loop but save to DB.
        
        from app.services import bria
        from app.schemas.fibo import Plan, ProposedVariation, BriaParameters
        
        results = []
        proposed_vars = [] # To save in Plan
        
        for i in range(variations):
            progress_step = 10 + int((i / variations) * 80)
            jobs.update_job(job_id, progress=progress_step)
            jobs.add_event(job_id, f"Generating variation {i+1}/{variations}...")
            
            mode = "inspire" if image_url else "generate"
            
            params = BriaParameters(
                prompt=prompt,
                reference_image_url=image_url,
                camera_angle="eye_level",
                seed=None
            )
            
            try:
                # Use Smart Agent if integrated? 
                # For now, stick to direct bria call which is working.
                res = await bria.generate_with_fibo(params, mode=mode)
                
                if res.get("image_url"):
                    img_url = res["image_url"]
                    jobs.add_result(job_id, img_url)
                    results.append(img_url)
                    
                    # Handle SP format
                    sp = res.get("structured_prompt", {})
                    if isinstance(sp, str):
                        try:
                            import json
                            sp = json.loads(sp)
                        except json.JSONDecodeError:
                            sp = {}
                            
                    # Add to proposed vars for persistence
                    proposed_vars.append(ProposedVariation(
                        concept_name=f"Quick Gen {i+1}",
                        bria_parameters=params,
                        generated_image_url=img_url,
                        json_prompt=sp
                    ))
                    
            except Exception as e:
                logger.error(f"Error generating variation {i}: {e}")
                jobs.add_event(job_id, f"Error on var {i+1}: {str(e)}")
        
        if not results:
             raise Exception("No images could be generated.")

        jobs.complete_job(job_id, results)
        
        # PERSIST TO MONGODB (PLAN HISTORY)
        if user_id and proposed_vars:
            try:
                # Ensure imports again just in case scope issue
                from app.schemas.fibo import Plan
                
                new_plan = Plan(
                    campaign_id="playground",  # Generic campaign
                    product_id="direct_upload",
                    proposed_variations=proposed_vars,
                    status="completed",
                    user_id=user_id
                )
                await new_plan.insert()
                logger.info(f"Persisted job {job_id} as Plan {new_plan.id} for user {user_id}")
            except Exception as db_e:
                logger.exception(f"Failed to persist plan to MongoDB: {db_e}")
                
    except Exception as e:
        logger.error(f"Job failed: {e}")
        jobs.fail_job(job_id, str(e))

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str, current_user: deps.AuthUser = Depends(deps.get_current_user)):
    """Obtiene el estado de un trabajo de generación en segundo plano"""
    status = jobs.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
        
    # Security: Enforce Ownership
    if status.get("user_id") and status.get("user_id") != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return status
