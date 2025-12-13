import json
import uuid
import datetime
import traceback
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable
import base64

from app.core.config import settings
from app.services.jobs import (
    Job, JobStage, update_job, add_event, complete_job, 
    fail_job, add_partial_result
)
from app.services.bria_v2 import BriaV2Client
from app.services.rag import SimpleRAG
from app.services.llm_planner import LLMPlanner

logger = logging.getLogger(__name__)

def _deep_update(dst: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
    """Actualización recursiva de diccionarios."""
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _deep_update(dst[k], v)
        else:
            dst[k] = v
    return dst

class Orchestrator:
    """
    Orquestador principal del pipeline de generación (versión unificada).
    Workflow: Bria SP -> RAG -> LLM Patches -> Plan -> Execution (Bria Image).
    """
    
    def __init__(self):
        self.bria = BriaV2Client()
        self.rag = SimpleRAG()
        self.planner = LLMPlanner()
        self.data_dir = Path(settings.DATA_DIR)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _load_image_base64(self, image_path: str) -> Optional[str]:
        """Carga imagen desde disco y convierte a base64."""
        if not image_path:
            return None
        path = Path(image_path)
        if not path.exists():
            return None
        try:
            with open(path, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode("utf-8")
        except Exception as e:
            logger.error(f"Error cargando imagen {image_path}: {e}")
            return None

    def generate_plan(
        self,
        prompt: str,
        image_b64: str,
        brand_guidelines: Optional[str],
        variations: int,
        on_step: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Fase 1: Generación del Plan.
        Obtiene prompt base, aplica RAG y genera variaciones con LLM.
        """
        if on_step: on_step("BRIA_SP_REQUEST", {})
        
        # 1. Obtener Structured Prompt Base
        try:
            init = self.bria.structured_prompt_generate(prompt, image_b64)
            # Manejar status_url si es async o request_id si es sync simulado
            status_url = init.get("status_url")
            if not status_url and "request_id" in init:
                # Construir URL si solo tenemos ID y base_url conocida
                # (Asumiendo implementación de BriaV2Client maneja esto o devuelve resultado directo)
                pass 
            
            # Si Bria devuelve status_url, hacemos poll
            if status_url:
                if on_step: on_step("BRIA_SP_POLL", {"status_url": status_url})
                done = self.bria.poll_until_done(status_url)
            else:
                # Si es síncrono o ya tenemos resultado
                done = init

            result = done.get("result", {})
            sp_str = result.get("structured_prompt")
            seed = result.get("seed")

            if not sp_str:
                raise Exception(f"No se recibió structured_prompt válido: {done}")
            
            base_sp = json.loads(sp_str)

        except Exception as e:
            logger.error(f"Error obteniendo structured prompt: {e}")
            # Fallback crítico si falla Bria SP inicial? 
            # Por ahora relanzamos para que falle el job
            raise e

        # 2. RAG Context
        if on_step: on_step("RAG_CONTEXT", {})
        ctx = self.rag.load_context(brand_guidelines)

        # 3. LLM Patches
        if on_step: on_step("LLM_PATCHES", {"model": self.planner.model})
        patches = self.planner.propose_patches(prompt, base_sp, ctx, variations)

        # 4. Crear Variaciones
        sps = []
        for i, patch in enumerate(patches):
            sp = json.loads(json.dumps(base_sp)) # Deep copy
            if patch:
                _deep_update(sp, patch)
            
            # Variar seed ligeramente para diversidad extra si se desea, o mantener
            current_seed = (int(seed) + i * 123) if seed is not None else None
            sps.append({
                "index": i, 
                "seed": current_seed, 
                "structured_prompt": sp
            })

        # 5. Guardar Plan
        plan_id = "plan_" + uuid.uuid4().hex[:10]
        plan = {
            "plan_id": plan_id,
            "base_seed": seed,
            "prompt": prompt,
            "structured_prompts": sps,
            "created_at": str(datetime.datetime.now())
        }
        
        try:
            (self.data_dir / f"{plan_id}.json").write_text(
                json.dumps(plan, ensure_ascii=False, indent=2), 
                encoding="utf-8"
            )
        except Exception as e:
            logger.warning(f"No se pudo guardar archivo del plan: {e}")

        if on_step: on_step("PLAN_SAVED", {"plan_id": plan_id})
        return plan

    def execute_plan_stepwise(
        self, 
        plan: Dict[str, Any], 
        aspect_ratio: str, 
        on_step=None
    ) -> Dict[str, Any]:
        """
        Fase 2: Ejecución del Plan.
        Genera las imágenes una por una usando Bria.
        """
        results = []
        items = plan.get("structured_prompts", [])
        total = len(items)

        for k, item in enumerate(items, start=1):
            idx = item["index"]
            if on_step: on_step("IMAGE_SUBMIT", {"k": k, "total": total, "index": idx})

            try:
                sp_str = json.dumps(item["structured_prompt"], ensure_ascii=False)
                
                # Iniciar generación
                init = self.bria.image_generate(sp_str, item.get("seed"), aspect_ratio)
                status_url = init.get("status_url") 

                if status_url:
                    if on_step: on_step("IMAGE_POLL", {"k": k, "total": total, "index": idx, "status_url": status_url})
                    done = self.bria.poll_until_done(status_url)
                else:
                    done = init

                # Verificar resultado
                if (done.get("status") or "").upper() not in ["COMPLETED", "SUCCESS", "DONE"]:
                     # Intento de recuperar URL si viene directo aunque status no sea standard
                     res = done.get("result", {})
                     if not (res.get("image_url") or res.get("image_urls")):
                         raise Exception(f"Status not completed: {done.get('status')}")

                res = done.get("result") or {}
                # Bria v2 devuelve lista en image_urls usualmente
                image_urls = res.get("image_urls", [])
                image_url = image_urls[0] if image_urls else res.get("image_url")
                
                if not image_url:
                     raise Exception("No image_url in response")

                results.append(image_url)
                
                if on_step: on_step("IMAGE_DONE", {"k": k, "total": total, "index": idx, "image_url": image_url})

            except Exception as e:
                logger.error(f"Error generando imagen {k}: {e}")
                if on_step: on_step("IMAGE_ERROR", {"k": k, "total": total, "index": idx, "error": str(e)})

        plan["results"] = results
        return plan

    def run_pipeline(self, job: Job) -> None:
        """
        Ejecuta todo el pipeline para un job dado.
        Es seguro ejecutar esto en un threadpool (síncrono).
        """
        try:
            update_job(job.job_id, stage=JobStage.STARTED, progress=5)
            add_event(job.job_id, "Iniciando pipeline de generación...")

            # Cargar imagen
            image_b64 = self._load_image_base64(job.image_path)
            if not image_b64:
                 fail_job(job.job_id, "No se pudo cargar la imagen de referencia")
                 return

            # Callbacks para actualizar el Job
            def on_plan_step(stage_name, payload):
                if stage_name == "BRIA_SP_REQUEST":
                    update_job(job.job_id, stage=JobStage.BRIA_SP_REQUEST, progress=10)
                    add_event(job.job_id, "Solicitando análisis de imagen a Bria...")
                elif stage_name == "BRIA_SP_POLL":
                    add_event(job.job_id, "Esperando respuesta de Bria (Analysis)...")
                elif stage_name == "RAG_CONTEXT":
                    update_job(job.job_id, stage=JobStage.RAG_CONTEXT, progress=20)
                    add_event(job.job_id, "Cargando guías de marca y contexto...")
                elif stage_name == "LLM_PATCHES":
                    update_job(job.job_id, stage=JobStage.LLM_PATCHES, progress=30)
                    model = payload.get("model", "LLM")
                    add_event(job.job_id, f"Diseñando variaciones con {model}...")
                elif stage_name == "PLAN_SAVED":
                    update_job(job.job_id, stage=JobStage.PLAN_SAVED, progress=40, plan_id=payload.get("plan_id"))
                    add_event(job.job_id, "Plan de generación creado exitosamente.")

            # Generar Plan
            plan = self.generate_plan(
                job.prompt, 
                image_b64, 
                job.brand_guidelines, 
                job.variations, 
                on_step=on_plan_step
            )

            job_total = len(plan.get("structured_prompts", []))
            # Actualizamos total en job internal attributes si los tuviera, o inferimos en progreso
            
            def on_img_step(stage_name, payload):
                k = payload.get("k", 1)
                total = payload.get("total", 1)
                
                # Calcular progreso lineal entre 40% y 100%
                base_progress = 40
                remaining_percent = 60
                
                # Progreso por imagen
                step_val = remaining_percent / max(total, 1)
                current_base = base_progress + (step_val * (k - 1))
                
                if stage_name == "IMAGE_SUBMIT":
                    update_job(job.job_id, stage=JobStage.IMAGE_POLL, progress=current_base + (step_val * 0.1))
                    add_event(job.job_id, f"Generando variación {k}/{total}...")
                elif stage_name == "IMAGE_POLL":
                     # No spamear logs
                     pass
                elif stage_name == "IMAGE_DONE":
                    update_job(job.job_id, progress=current_base + step_val)
                    url = payload.get("image_url")
                    idx = payload.get("index")
                    
                    add_partial_result(job.job_id, {"index": idx, "image_url": url})
                    add_event(job.job_id, f"✅ Variación {k} lista")
                elif stage_name == "IMAGE_ERROR":
                    add_event(job.job_id, f"⚠️ Error en variación {k}: {payload.get('error')}")

            # Ejecutar Plan
            final_plan = self.execute_plan_stepwise(
                plan, 
                job.aspect_ratio or "1:1", 
                on_step=on_img_step
            )
            
            results = final_plan.get("results", [])
            complete_job(job.job_id, results)

        except Exception as e:
            logger.exception(f"Error crítico en pipeline job {job.job_id}")
            fail_job(job.job_id, str(e), traceback.format_exc())


# Singleton instance
_orchestrator: Optional[Orchestrator] = None

def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator
