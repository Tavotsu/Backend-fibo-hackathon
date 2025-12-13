#@title 🧠 2) Crear microservicio LLM+RAG en Drive (Jobs/Stages + fallback Ollama) ✅
DRIVE_PROJECT_FOLDER = "Hackathon Bria Fibo" #@param {type:"string"}
SERVICE_FOLDER_NAME = "llm_rag_service" #@param {type:"string"}

BRIA_V2_BASE_URL = "https://engine.prod.bria-api.com/v2" #@param {type:"string"}
BRIA_API_TOKEN = "db81b51414d34465b1c7968dacaad14d" #@param {type:"string"}  # ⚠️ NO lo hardcodees en repo. Usarlo como env al levantar.

OLLAMA_MODEL = "deepseek-r1:8b" #@param {type:"string"}
DEFAULT_VARIATIONS = 4 #@param {type:"integer"}
DEFAULT_TIMEOUT_SEC = 300 #@param {type:"integer"}
DEFAULT_POLL_EVERY_SEC = 2 #@param {type:"integer"}

import textwrap
from pathlib import Path
from google.colab import drive

drive.mount("/content/drive", force_remount=False)

DRIVE_ROOT = Path("/content/drive/MyDrive") / DRIVE_PROJECT_FOLDER
SERVICE_DIR = DRIVE_ROOT / SERVICE_FOLDER_NAME
(SERVICE_DIR / "data").mkdir(parents=True, exist_ok=True)
(SERVICE_DIR / "rag").mkdir(parents=True, exist_ok=True)

print("✅ Microservicio en:", SERVICE_DIR)

app_py = r"""from __future__ import annotations

import base64, json, os, time, uuid, threading, traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

import requests
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

# ============================================================
# Configs (@dataclass)
# ============================================================
@dataclass
class BriaConfig:
    base_url: str
    api_token: str
    timeout_sec: int = 300
    poll_every_sec: int = 2

@dataclass
class OllamaConfig:
    model: str = "deepseek-r1:8b"
    temperature: float = 0.2
    max_tokens: int = 900

@dataclass
class RagConfig:
    kb_path: Path
    max_chars: int = 4000

@dataclass
class ServiceConfig:
    root_dir: Path
    bria: BriaConfig
    ollama: OllamaConfig
    rag: RagConfig
    default_variations: int = 4

# ============================================================
# Utilidades
# ============================================================
def _now() -> float:
    return time.time()

def _b64_from_upload(upload: UploadFile) -> str:
    raw = upload.file.read()
    return base64.b64encode(raw).decode("utf-8")

def _safe_json_extract(text: str) -> Optional[str]:
    if not text:
        return None
    try:
        json.loads(text)
        return text
    except Exception:
        pass
    start = min([i for i in [text.find("{"), text.find("[")] if i != -1], default=-1)
    if start == -1:
        return None
    stack = []
    for i in range(start, len(text)):
        ch = text[i]
        if ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if not stack:
                continue
            stack.pop()
            if not stack:
                cand = text[start:i+1]
                try:
                    json.loads(cand)
                    return cand
                except Exception:
                    return None
    return None

def _deep_update(dst: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _deep_update(dst[k], v)
        else:
            dst[k] = v
    return dst

# ============================================================
# Job Store (thread-safe)
# ============================================================
class JobStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._jobs: Dict[str, Dict[str, Any]] = {}

    def create(self) -> str:
        job_id = "job_" + uuid.uuid4().hex[:10]
        with self._lock:
            self._jobs[job_id] = {
                "job_id": job_id,
                "stage": "QUEUED",
                "progress": 0,
                "created_at": _now(),
                "updated_at": _now(),
                "events": [],
                "partial_results": [],
            }
        self.event(job_id, "Job creado")
        return job_id

    def get(self, job_id: str) -> Dict[str, Any]:
        with self._lock:
            if job_id not in self._jobs:
                raise KeyError(job_id)
            return json.loads(json.dumps(self._jobs[job_id]))

    def update(self, job_id: str, **kw):
        with self._lock:
            if job_id not in self._jobs:
                raise KeyError(job_id)
            self._jobs[job_id].update(kw)
            self._jobs[job_id]["updated_at"] = _now()

    def event(self, job_id: str, msg: str):
        with self._lock:
            if job_id not in self._jobs:
                return
            self._jobs[job_id].setdefault("events", [])
            self._jobs[job_id]["events"].append({"t": _now(), "msg": msg})
            if len(self._jobs[job_id]["events"]) > 250:
                self._jobs[job_id]["events"] = self._jobs[job_id]["events"][-250:]

# ============================================================
# Cliente Bria v2
# ============================================================
class BriaV2Client:
    def __init__(self, cfg: BriaConfig):
        self.cfg = cfg
        self.session = requests.Session()
        self.session.headers.update({"api_token": self.cfg.api_token})

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = self.cfg.base_url.rstrip("/") + "/" + path.lstrip("/")
        r = self.session.post(url, json=payload, timeout=self.cfg.timeout_sec)
        if r.status_code not in (200, 202):
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()

    def _get(self, url: str) -> Dict[str, Any]:
        r = self.session.get(url, timeout=self.cfg.timeout_sec)
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()

    def structured_prompt_generate(self, prompt: str, image_b64: str) -> Dict[str, Any]:
        return self._post("/structured_prompt/generate", {"prompt": prompt, "images": [image_b64], "sync": False})

    def image_generate(self, structured_prompt: str, seed: Optional[int], aspect_ratio: str) -> Dict[str, Any]:
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
        t0 = _now()
        while True:
            if _now() - t0 > self.cfg.timeout_sec:
                raise HTTPException(status_code=504, detail="Timeout esperando Status Service.")
            data = self._get(status_url)
            st = (data.get("status") or "").upper()
            if st in ("COMPLETED", "ERROR", "UNKNOWN"):
                return data
            time.sleep(self.cfg.poll_every_sec)

# ============================================================
# RAG simple
# ============================================================
class SimpleRAG:
    def __init__(self, cfg: RagConfig):
        self.cfg = cfg

    def load_context(self, extra_guidelines: Optional[str]) -> str:
        chunks = []
        if self.cfg.kb_path.exists():
            chunks.append(self.cfg.kb_path.read_text(encoding="utf-8"))
        if extra_guidelines:
            chunks.append(extra_guidelines)
        ctx = "\n\n".join([c.strip() for c in chunks if c and c.strip()]).strip()
        return (ctx[: self.cfg.max_chars] + "\n\n[...truncado...]") if len(ctx) > self.cfg.max_chars else ctx

# ============================================================
# LLM planner (Ollama) con fallback
# ============================================================
class LLMPlanner:
    def __init__(self, cfg: OllamaConfig):
        self.cfg = cfg
        self.client = None
        try:
            import ollama as _ollama
            host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
            self.client = _ollama.Client(host=host)
        except Exception:
            self.client = None

    def propose_patches(self, user_prompt: str, base_sp: Dict[str, Any], brand_ctx: str, n: int) -> List[Dict[str, Any]]:
        if self.client is None:
            return self._fallback(n)

        system = (
            "Output ONLY valid JSON. Return an array of exactly N patch objects. "
            "Each patch is a partial JSON dict to merge into base structured_prompt. "
            "Keep product identity and label readable. "
            "Vary camera_angle, lighting, background_setting, aesthetics. "
            "Do NOT invent fake logos or change brand name on product."
        ).replace("N", str(n))

        payload = {
            "N": n,
            "user_prompt": user_prompt,
            "brand_context": brand_ctx,
            "base_structured_prompt": base_sp,
            "output_format": "JSON array of N patch objects",
        }

        try:
            resp = self.client.chat(
                model=self.cfg.model,
                messages=[
                    {"role":"system","content":system},
                    {"role":"user","content":json.dumps(payload, ensure_ascii=False)},
                ],
                options={"temperature": self.cfg.temperature},
            )
        except Exception:
            return self._fallback(n)

        text = (resp.get("message") or {}).get("content","")
        extracted = _safe_json_extract(text)
        if not extracted:
            return self._fallback(n)

        try:
            patches = json.loads(extracted)
            if not isinstance(patches, list):
                return self._fallback(n)
            patches = patches[:n]
            while len(patches) < n:
                patches.append({})
            return [p if isinstance(p, dict) else {} for p in patches]
        except Exception:
            return self._fallback(n)

    def _fallback(self, n: int) -> List[Dict[str, Any]]:
        presets = [
            {"lighting":{"conditions":"studio softbox"},"photographic_characteristics":{"camera_angle":"eye-level","depth_of_field":"shallow"},
             "background_setting":"clean premium studio background","aesthetics":{"mood_atmosphere":"premium minimal","color_scheme":"brand-aligned"}},
            {"lighting":{"conditions":"golden hour"},"photographic_characteristics":{"camera_angle":"three-quarter","depth_of_field":"medium"},
             "background_setting":"subtle lifestyle scene (out-of-focus)","aesthetics":{"mood_atmosphere":"warm aspirational","color_scheme":"warm + brand accent"}},
            {"lighting":{"conditions":"dramatic rim light"},"photographic_characteristics":{"camera_angle":"low angle","depth_of_field":"shallow"},
             "background_setting":"dark premium backdrop","aesthetics":{"mood_atmosphere":"bold luxury","color_scheme":"dark + brand accent"}},
            {"lighting":{"conditions":"top light diffused"},"photographic_characteristics":{"camera_angle":"top-down flat lay","depth_of_field":"deep"},
             "background_setting":"flat lay surface (stone/wood) minimal props","aesthetics":{"mood_atmosphere":"editorial clean","color_scheme":"neutral + brand accent"}},
        ]
        out = presets[:n]
        while len(out) < n:
            out.append({})
        return out

# ============================================================
# Orquestador con callback de etapas
# ============================================================
class Orchestrator:
    def __init__(self, cfg: ServiceConfig):
        self.cfg = cfg
        self.bria = BriaV2Client(cfg.bria)
        self.rag = SimpleRAG(cfg.rag)
        self.planner = LLMPlanner(cfg.ollama)
        self.data_dir = cfg.root_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def generate_plan(
        self,
        prompt: str,
        image_b64: str,
        brand_guidelines: Optional[str],
        variations: int,
        on_step: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        if on_step: on_step("BRIA_SP_REQUEST", {})
        init = self.bria.structured_prompt_generate(prompt, image_b64)
        status_url = init.get("status_url") or (self.cfg.bria.base_url.rstrip("/") + f"/status/{init.get('request_id')}")

        if on_step: on_step("BRIA_SP_POLL", {"status_url": status_url})
        done = self.bria.poll_until_done(status_url)

        if (done.get("status") or "").upper() != "COMPLETED":
            raise HTTPException(status_code=502, detail={"bria_status": done})

        result = done.get("result") or {}
        sp_str = result.get("structured_prompt")
        seed = result.get("seed")

        if not sp_str:
            raise HTTPException(status_code=502, detail={"missing_structured_prompt": done})

        base_sp = json.loads(sp_str)

        if on_step: on_step("RAG_CONTEXT", {})
        ctx = self.rag.load_context(brand_guidelines)

        if on_step: on_step("LLM_PATCHES", {"model": self.cfg.ollama.model})
        patches = self.planner.propose_patches(prompt, base_sp, ctx, variations)

        sps = []
        for i, patch in enumerate(patches):
            sp = json.loads(json.dumps(base_sp))
            if patch:
                _deep_update(sp, patch)
            sps.append({"index": i, "seed": (int(seed)+i) if seed is not None else None, "structured_prompt": sp})

        plan_id = "plan_" + uuid.uuid4().hex[:10]
        plan = {"plan_id": plan_id, "base_seed": seed, "prompt": prompt, "structured_prompts": sps}
        (self.data_dir / f"{plan_id}.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        if on_step: on_step("PLAN_SAVED", {"plan_id": plan_id})
        return plan

    def execute_plan_stepwise(self, plan: Dict[str, Any], aspect_ratio: str, on_step=None) -> Dict[str, Any]:
        results = []
        items = plan.get("structured_prompts", [])
        total = len(items)

        for k, item in enumerate(items, start=1):
            idx = item["index"]
            if on_step: on_step("IMAGE_SUBMIT", {"k": k, "total": total, "index": idx})

            sp_str = json.dumps(item["structured_prompt"], ensure_ascii=False)
            init = self.bria.image_generate(sp_str, item.get("seed"), aspect_ratio)
            status_url = init.get("status_url") or (self.cfg.bria.base_url.rstrip("/") + f"/status/{init.get('request_id')}")

            if on_step: on_step("IMAGE_POLL", {"k": k, "total": total, "index": idx, "status_url": status_url})
            done = self.bria.poll_until_done(status_url)

            if (done.get("status") or "").upper() != "COMPLETED":
                results.append({"index": idx, "status": done.get("status"), "raw": done})
                if on_step: on_step("IMAGE_ERROR", {"k": k, "total": total, "index": idx, "status": done.get("status")})
                continue

            res = done.get("result") or {}
            image_url = res.get("image_url") or res.get("image_urls")
            results.append({"index": idx, "seed": item.get("seed"), "image_url": image_url})
            if on_step: on_step("IMAGE_DONE", {"k": k, "total": total, "index": idx, "image_url": image_url})

        plan["results"] = results
        return plan

# ============================================================
# FastAPI
# ============================================================
def build_app(cfg: ServiceConfig) -> FastAPI:
    app = FastAPI(title="Bria FIBO — AI Art Director (LLM+RAG)", version="0.3.0")
    orch = Orchestrator(cfg)
    jobs = JobStore()

    @app.get("/health")
    def health():
        return {"status":"ok","service":"llm_rag_service"}

    # Async (front-friendly)
    def _run_job(job_id: str, prompt: str, image_b64: str, brand_guidelines: Optional[str], variations: int, aspect_ratio: str):
        try:
            jobs.update(job_id, stage="STARTED", progress=1, done=0)

            def on_plan_step(stage: str, payload: Dict[str, Any]):
                if stage == "BRIA_SP_REQUEST":
                    jobs.update(job_id, stage="BRIA_SP_REQUEST", progress=2)
                    jobs.event(job_id, "Solicitando structured_prompt a Bria…")
                elif stage == "BRIA_SP_POLL":
                    jobs.update(job_id, stage="BRIA_SP_POLL", progress=6, last_status_url=payload.get("status_url"))
                    jobs.event(job_id, "Esperando structured_prompt (poll)…")
                elif stage == "RAG_CONTEXT":
                    jobs.update(job_id, stage="RAG_CONTEXT", progress=10)
                    jobs.event(job_id, "Cargando contexto RAG (kb + guidelines)…")
                elif stage == "LLM_PATCHES":
                    jobs.update(job_id, stage="LLM_PATCHES", progress=13)
                    jobs.event(job_id, f"Generando patches JSON con LLM ({payload.get('model')})…")
                elif stage == "PLAN_SAVED":
                    jobs.update(job_id, stage="PLAN_SAVED", progress=15, plan_id=payload.get("plan_id"))
                    jobs.event(job_id, f"Plan guardado: {payload.get('plan_id')}")

            plan = orch.generate_plan(prompt, image_b64, brand_guidelines, variations, on_step=on_plan_step)
            plan_id = plan["plan_id"]
            total = len(plan.get("structured_prompts", []))
            jobs.update(job_id, total=total, done=0)

            def on_img_step(stage: str, payload: Dict[str, Any]):
                k, tot = payload.get("k", 0), payload.get("total", total) or 1
                base = 15
                prog = base + int(80 * (max(0, k-1) / max(1, tot)))
                if stage == "IMAGE_DONE":
                    prog = base + int(80 * (k / max(1, tot)))

                jobs.update(job_id, stage=stage, progress=prog, last_status_url=payload.get("status_url"),
                            done=(k if stage=="IMAGE_DONE" else max(0, k-1)))

                if stage == "IMAGE_SUBMIT":
                    jobs.event(job_id, f"Enviando imagen {k}/{tot} a Bria…")
                elif stage == "IMAGE_POLL":
                    jobs.event(job_id, f"Esperando imagen {k}/{tot} (poll)…")
                elif stage == "IMAGE_DONE":
                    cur = jobs.get(job_id).get("partial_results", [])
                    cur.append({"index": payload.get("index"), "image_url": payload.get("image_url")})
                    jobs.update(job_id, partial_results=cur)
                    jobs.event(job_id, f"Imagen {k}/{tot} lista ✅")
                elif stage == "IMAGE_ERROR":
                    jobs.event(job_id, f"Imagen {k}/{tot} falló ❌")

            plan = orch.execute_plan_stepwise(plan, aspect_ratio, on_step=on_img_step)
            (orch.data_dir / f"{plan_id}.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

            jobs.update(job_id, stage="DONE", progress=100, results=plan.get("results", []))
            jobs.event(job_id, "Job completado ✅")

        except Exception as e:
            jobs.update(job_id, stage="ERROR", progress=100, error=str(e), trace=traceback.format_exc())
            jobs.event(job_id, "Job falló ❌")

    @app.post("/api/v1/generate-async")
    async def generate_async(
        image: UploadFile = File(...),
        prompt: str = Form(...),
        brand_guidelines: str = Form(""),
        variations: int = Form(cfg.default_variations),
        aspect_ratio: str = Form("1:1"),
    ):
        if not cfg.bria.api_token:
            raise HTTPException(status_code=400, detail="Falta BRIA_API_TOKEN.")

        job_id = jobs.create()
        jobs.update(job_id, stage="QUEUED", progress=0, prompt=prompt, variations=int(variations), aspect_ratio=aspect_ratio)

        image_b64 = _b64_from_upload(image)

        t = threading.Thread(
            target=_run_job,
            args=(job_id, prompt, image_b64, brand_guidelines or None, max(1,int(variations)), aspect_ratio),
            daemon=True
        )
        t.start()

        return {"job_id": job_id}

    @app.get("/api/v1/jobs/{job_id}")
    def get_job(job_id: str):
        try:
            return jobs.get(job_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Job no encontrado.")

    return app

ROOT_DIR = Path(os.environ.get("LLM_RAG_ROOT", Path(__file__).resolve().parent))
cfg = ServiceConfig(
    root_dir=ROOT_DIR,
    bria=BriaConfig(
        base_url=os.environ.get("BRIA_V2_BASE_URL","https://engine.prod.bria-api.com/v2"),
        api_token=os.environ.get("BRIA_API_TOKEN",""),
        timeout_sec=int(os.environ.get("BRIA_TIMEOUT_SEC","300")),
        poll_every_sec=int(os.environ.get("BRIA_POLL_EVERY_SEC","2")),
    ),
    ollama=OllamaConfig(model=os.environ.get("OLLAMA_MODEL","deepseek-r1:8b")),
    rag=RagConfig(kb_path=ROOT_DIR / "rag" / "kb.txt"),
    default_variations=int(os.environ.get("DEFAULT_VARIATIONS","4")),
)

app = build_app(cfg)
"""

# escribir archivos
(SERVICE_DIR / "app.py").write_text(app_py, encoding="utf-8")
(SERVICE_DIR / "requirements.txt").write_text(
    "fastapi\nuvicorn[standard]\npython-multipart\npydantic\nrequests\npillow\ntqdm\nollama\n",
    encoding="utf-8"
)

kb = SERVICE_DIR / "rag" / "kb.txt"
if not kb.exists():
    kb.write_text(
        "Brand rules (ejemplo):\n- Keep product centered\n- Background clean\n- Accent color #FF5733\n",
        encoding="utf-8"
    )

print("✅ Listo. Archivos creados:")
print(" -", SERVICE_DIR / "app.py")
print(" -", SERVICE_DIR / "rag" / "kb.txt")

print("\n📌 Variables de entorno recomendadas (NO pegues el token en el repo):")
print(textwrap.dedent(f"""
export BRIA_API_TOKEN='(pega aquí tu token en runtime)'
export BRIA_V2_BASE_URL='{BRIA_V2_BASE_URL}'
export OLLAMA_HOST='http://127.0.0.1:11434'
export OLLAMA_MODEL='{OLLAMA_MODEL}'
export DEFAULT_VARIATIONS='{DEFAULT_VARIATIONS}'
export BRIA_TIMEOUT_SEC='{DEFAULT_TIMEOUT_SEC}'
export BRIA_POLL_EVERY_SEC='{DEFAULT_POLL_EVERY_SEC}'
"""))
