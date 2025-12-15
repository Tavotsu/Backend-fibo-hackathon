import uuid
import time
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from app.schemas.fibo import Job

logger = logging.getLogger(__name__)

class JobStage(str, Enum):
    QUEUED = "QUEUED"
    STARTED = "STARTED"
    
    # Etapas Bria v2 Pipeline
    BRIA_SP_REQUEST = "BRIA_SP_REQUEST"
    BRIA_SP_POLL = "BRIA_SP_POLL"
    RAG_CONTEXT = "RAG_CONTEXT"
    LLM_PATCHES = "LLM_PATCHES"
    PLAN_SAVED = "PLAN_SAVED"
    
    # Etapas Generación Imagen
    IMAGE_SUBMIT = "IMAGE_SUBMIT"
    IMAGE_POLL = "IMAGE_POLL"
    IMAGE_DONE = "IMAGE_DONE"
    IMAGE_ERROR = "IMAGE_ERROR"
    
    DONE = "DONE"
    ERROR = "ERROR"

async def create_job(
    prompt: str,
    brand_guidelines: str = "",
    variations: int = 4,
    aspect_ratio: str = "1:1",
    image_path: Optional[str] = None,
    user_id: Optional[str] = None
) -> Job:
    job_id = f"job_{uuid.uuid4().hex[:10]}"
    job = Job(
        job_id=job_id,
        prompt=prompt,
        variations=variations,
        user_id=user_id,
        brand_guidelines=brand_guidelines,
        aspect_ratio=aspect_ratio,
        image_path=image_path,
        created_at=time.time(),
        updated_at=time.time()
    )
    await job.insert()
    return job

async def get_job(job_id: str) -> Optional[Job]:
    return await Job.find_one(Job.job_id == job_id)

async def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    job = await get_job(job_id)
    if job:
        # Pydantic/Beanie model to dict
        return job.model_dump()
    return None

async def update_job(job_id: str, **kwargs):
    job = await get_job(job_id)
    if not job:
        return
    
    for k, v in kwargs.items():
        if hasattr(job, k):
            setattr(job, k, v)
    job.updated_at = time.time()
    await job.save()

async def add_event(job_id: str, message: str):
    job = await get_job(job_id)
    if not job:
        return
    
    job.events.append({
        "t": time.time(),
        "msg": message
    })
    # Keep only last 250 events
    if len(job.events) > 250:
        job.events = job.events[-250:]
    job.updated_at = time.time()
    await job.save()

async def add_result(job_id: str, result_url: str):
    job = await get_job(job_id)
    if not job:
        return
    if result_url not in job.results:
        job.results.append(result_url)
    job.updated_at = time.time()
    await job.save()

async def add_partial_result(job_id: str, partial: Dict[str, Any]):
    job = await get_job(job_id)
    if not job:
        return
    job.partial_results.append(partial)
    job.updated_at = time.time()
    await job.save()

async def complete_job(job_id: str, results: List[str]):
    await update_job(job_id, stage=JobStage.DONE, progress=100, results=results)
    await add_event(job_id, "Job completed successfully")

async def fail_job(job_id: str, error_msg: str, trace: str = ""):
    await update_job(job_id, stage=JobStage.ERROR, progress=100, error=error_msg, trace=trace)
    await add_event(job_id, f"Job failed: {error_msg}")
