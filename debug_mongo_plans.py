import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.schemas.fibo import Campaign, Product, Plan

from app.core.config import settings

async def main():
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("ERROR: MONGO_URI missing")
        return

    client = AsyncIOMotorClient(mongo_uri)
    try:
        # Use settings.DB_NAME if available, else default
        db_name = getattr(settings, "DB_NAME", "ai_art_director")
        
        await init_beanie(
            database=client[db_name],
            document_models=[Campaign, Product, Plan]
        )
        print("MongoDB Connected.")

        print("--- Checking Plans in MongoDB ---")
        plans = await Plan.find_all().to_list()
        print(f"Total Plans found: {len(plans)}")
        for p in plans:
            print(f"ID: {p.id} | User: {p.user_id} | Status: {p.status} | Variations: {len(p.proposed_variations)}")
            if p.proposed_variations:
                print(f"   -> First Var URL: {p.proposed_variations[0].generated_image_url}")
                
    finally:
        client.close()
        print("MongoDB Connection closed.")

if __name__ == "__main__":
    asyncio.run(main())
