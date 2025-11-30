from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from app.schemas.fibo import (
    Campaign, CampaignCreate, 
    Product, 
    Plan, PlanRequest, 
    BriaStructuredPrompt,
    ExecuteRequest
)
from app.services.storage import upload_image_to_supabase
from app.services.agent import analyze_and_plan
from app.services.bria import generate_image_bria
import uuid

router = APIRouter()

# 1. Gestión de Campañas
@router.post("/campaigns", response_model=Campaign)
async def create_campaign(campaign_in: CampaignCreate):
    new_campaign = Campaign(
        name=campaign_in.name,
        brand_guidelines=campaign_in.brand_guidelines
    )
    await new_campaign.insert()
    return new_campaign

# 2. Ingesta de Producto
@router.post("/campaigns/{campaign_id}/upload-product")
async def upload_product(campaign_id: str, file: UploadFile = File(...)):
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
    
    return {"product_id": str(new_product.id), "url": public_url}

# 3. El Cerebro (Generate Plan)
@router.post("/campaigns/{campaign_id}/generate-plan", response_model=Plan)
async def generate_plan(campaign_id: str, request: PlanRequest):
    # 1. Validar datos
    product = await Product.get(request.product_id)
    if not product:
        raise HTTPException(404, "Producto no encontrado")
        
    campaign = await Campaign.get(campaign_id)
    if not campaign:
         raise HTTPException(404, "Campaña no encontrada")

    # 2. Llamada al Agente (GPT-4o)
    print(f"Agente pensando para: {product.image_url}...")
    
    # Aquí obtenemos la lista de JSONs complejos (BriaStructuredPrompt)
    generated_variations = await analyze_and_plan(
        image_url=product.image_url,
        mood=campaign.brand_guidelines.mood,
        count=request.variations_count
    )
    
    if not generated_variations:
        raise HTTPException(500, "El agente no pudo generar variaciones válidas")
    
    # 3. Guardar Plan
    new_plan = Plan(
        campaign_id=campaign_id,
        product_id=str(product.id),
        proposed_variations=generated_variations # Guardamos la lista compleja
    )
    await new_plan.insert()

    return new_plan

# 4. Ejecución (Enviar a Bria)
@router.post("/campaigns/{campaign_id}/execute")
async def execute_plan(campaign_id: str, request: ExecuteRequest, background_tasks: BackgroundTasks):
    plan = await Plan.get(request.plan_id)
    if not plan:
        raise HTTPException(404, "Plan no encontrado")
        
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    
    async def run_generation_task(plan_doc, selected_indices):
        print(f"Job {job_id}: Iniciando generación...")
        
        for index in selected_indices:
            # CORRECCIÓN AQUÍ:
            # Antes accedíamos a .bria_parameters. Ahora 'variation' YA ES el objeto de parámetros.
            if index >= len(plan_doc.proposed_variations):
                print(f"Índice {index} fuera de rango")
                continue

            variation = plan_doc.proposed_variations[index] # Esto es un BriaStructuredPrompt
            
            # Pasamos el objeto completo al servicio de Bria
            image_url = await generate_image_bria(variation)
            
            if image_url:
                print(f"Generado: {image_url}")
                # (Opcional) Aquí podrías guardar el resultado en Mongo
            else:
                print("Falló una generación")

    background_tasks.add_task(
        run_generation_task, 
        plan, 
        request.selected_variations
    )
    
    return {"job_id": job_id, "status": "processing", "message": "Generando imágenes..."}