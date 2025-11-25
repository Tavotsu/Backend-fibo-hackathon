from fastapi import APIRouter, UploadFile, File, HTTPException, Form, BackgroundTasks
from typing import List
from app.schemas.fibo import (
    Campaign, CampaignCreate, 
    Product, 
    Plan, PlanRequest, ProposedVariation, BriaParameters,
    ExecuteRequest
)
from app.services.storage import upload_image_to_supabase
import uuid

router = APIRouter()

# Campaign Creation
@router.post("/campaigns", response_model=Campaign)
async def create_campaign(campaign_in: CampaignCreate):
    # Instance a new Campaign
    new_campaign = Campaign(
        name=campaign_in.name,
        brand_guidelines=campaign_in.brand_guidelines
    )
    # Saving it to mongoDB with Beanie
    await new_campaign.insert()
    return new_campaign

# Product Upload
@router.post("/campaigns/{campaign_id}/upload-product")
async def upload_product(campaign_id: str, file: UploadFile = File(...)):
    
    # Check if campaign exists
    campaign = await Campaign.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaña no encontrada")

    # Uploading to Supabase
    public_url = await upload_image_to_supabase(file)
    if not public_url:
        raise HTTPException(status_code=500, detail="Error subiendo imagen a Supabase")

    # Saving product info in MongoDB
    new_product = Product(
        campaign_id=str(campaign.id),
        image_url=public_url,
        original_filename=file.filename or "unknown_file"
    )
    await new_product.insert()
    
    return {
        "product_id": str(new_product.id),
        "url": public_url,
        "message": "Imagen guardada en Supabase y MongoDB"
    }

# Generate Plan 
@router.post("/campaigns/{campaign_id}/generate-plan", response_model=Plan)
async def generate_plan(campaign_id: str, request: PlanRequest):
    
    # Check campaign exists
    product = await Product.get(request.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # MOCK LOGIC (here should be the AI logic to generate variations)
    mock_variations = [
        ProposedVariation(
            concept_name="Ejemplo Mongo + S3",
            bria_parameters=BriaParameters(
                prompt="Test prompt",
                camera_angle="eye_level",
                lighting_mode="studio"
            )
        )
    ]
    
    # Save the plan on MongoDB
    new_plan = Plan(
        campaign_id=campaign_id,
        product_id=str(product.id),
        proposed_variations=mock_variations
    )
    await new_plan.insert()

    return new_plan

# Execute Plan
@router.post("/campaigns/{campaign_id}/execute")
async def execute_plan(campaign_id: str, request: ExecuteRequest):
    plan = await Plan.get(request.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
        
    # Execute logic
    return {"status": "processing", "message": f"Procesando plan {plan.id} con datos reales"}