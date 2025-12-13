import uuid
import time
import threading
from typing import Dict, Any, Optional, List
from enum import Enum
import logging

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

class Job:
    def __init__(self, job_id: str, prompt: str, variations: int = 4):
        self.job_id = job_id
        self.prompt = prompt
        self.variations = variations
        self.stage = JobStage.QUEUED
        self.progress = 0
        self.created_at = time.time()
        self.updated_at = time.time()
        
        # Events: [{"t": float, "msg": str}]
        self.events: List[Dict[str, Any]] = []
        
        # Final Results: ["url1", "url2"]
        self.results: List[str] = []
        
        # Partial Results for streaming: [{"index": 1, "image_url": "..."}]
        self.partial_results: List[Dict[str, Any]] = []
        
        self.error: Optional[str] = None
        self.trace: Optional[str] = None
        
        # Context fields
        self.image_path: Optional[str] = None
        self.brand_guidelines: Optional[str] = None
        self.aspect_ratio: Optional[str] = "1:1"
        self.plan_id: Optional[str] = None
        
        # Internal counters
        self.total: int = 0
        self.done: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "prompt": self.prompt,
            "stage": self.stage,
            "progress": self.progress,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "events": self.events,
            "results": self.results,
            "partial_results": self.partial_results,
            "error": self.error,
            "plan_id": self.plan_id
        }

# Global Job Store (In-Memory & Thread-Safe)
_jobs_lock = threading.Lock()
_jobs: Dict[str, Job] = {}

def create_job(
    prompt: str,
    brand_guidelines: str = "",
    variations: int = 4,
    aspect_ratio: str = "1:1",
    image_path: Optional[str] = None
) -> Job:
    job_id = f"job_{uuid.uuid4().hex[:10]}"
    job = Job(job_id, prompt, variations)
    # Set optional fields
    job.brand_guidelines = brand_guidelines
    job.aspect_ratio = aspect_ratio
    job.image_path = image_path
    
    with _jobs_lock:
        _jobs[job_id] = job
    return job

def get_job(job_id: str) -> Optional[Job]:
    with _jobs_lock:
        return _jobs.get(job_id)

def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    job = get_job(job_id)
    if job:
        return job.to_dict()
    return None

def update_job(job_id: str, **kwargs):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            return
        
        for k, v in kwargs.items():
            if hasattr(job, k):
                setattr(job, k, v)
        job.updated_at = time.time()

def add_event(job_id: str, message: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
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

def add_result(job_id: str, result_url: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            return
        if result_url not in job.results:
            job.results.append(result_url)
        job.updated_at = time.time()

def add_partial_result(job_id: str, partial: Dict[str, Any]):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            return
        job.partial_results.append(partial)
        job.updated_at = time.time()

def complete_job(job_id: str, results: List[str]):
    update_job(job_id, stage=JobStage.DONE, progress=100, results=results)
    add_event(job_id, "Job completed successfully")

def fail_job(job_id: str, error_msg: str, trace: str = ""):
    update_job(job_id, stage=JobStage.ERROR, progress=100, error=error_msg, trace=trace)
    add_event(job_id, f"Job failed: {error_msg}")
