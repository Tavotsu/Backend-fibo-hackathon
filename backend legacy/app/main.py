import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.api.routes import router as api_router
from app.core.config import settings
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.schemas.fibo import Campaign, Product, Plan


# Life cycle of the application
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    
    # Crear directorio data si no existe
    data_dir = Path(settings.DATA_DIR)
    data_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Directorio de datos: {data_dir.absolute()}")
    
    # Conectar a MongoDB si está configurado
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("⚠️ ADVERTENCIA: MONGO_URI no está definido - algunas funciones no estarán disponibles")
    else:
        try:
            client = AsyncIOMotorClient(mongo_uri)
            # Initialize Beanie with the Motor client and document models
            await init_beanie(
                database=client.ai_art_director,  # type: ignore
                document_models=[Campaign, Product, Plan]
            )
            print("✅ MongoDB Conectado")
        except Exception as e:
            print(f"⚠️ Error conectando a MongoDB: {e}")
    
    print("🚀 Backend inicializado")
    print(f"📡 CORS habilitado para: {settings.CORS_ALLOW_ORIGINS}")
    print(f"🤖 LLM configurado: {settings.OLLAMA_MODEL} @ {settings.OLLAMA_HOST}")
    
    yield
    
    # Shutdown logic
    print("👋 Backend Apagándose")


# Passing the lifespan to FastAPI
app = FastAPI(
    title="AI Art Director API", 
    version="2.0.0", 
    lifespan=lifespan,
    description="API unificada para generación de imágenes con FIBO + LLM"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for generated images
data_path = Path(settings.DATA_DIR)
if data_path.exists():
    app.mount("/data", StaticFiles(directory=str(data_path)), name="data")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check para verificar que el backend está corriendo"""
    return {"status": "ok"}


# API Routes
app.include_router(api_router, prefix="/api/v1")