import os
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.routes import router as api_router
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.schemas.fibo import Campaign, Product, Plan

load_dotenv()

# Life cycle of the application
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("ADVERTENCIA: MONGO_URI no está definido")
    else:
        client = AsyncIOMotorClient(mongo_uri)
        # Initialize Beanie with the Motor client and document models
        await init_beanie(
            database=client.ai_art_director, # type: ignore
            document_models=[Campaign, Product, Plan]
        )
        print("MongoDB Conectado")
    
    yield
    

    # Shutdown logic
    print("Aplicación cerrándose")

# Passing the lifespan to FastAPI
app = FastAPI(title="AI Art Director API", version="1.0.0", lifespan=lifespan)

app.include_router(api_router, prefix="/api/v1")