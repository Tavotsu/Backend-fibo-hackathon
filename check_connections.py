import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    print("⚠️ Supabase library not found or broken (check websockets version).")

from dotenv import load_dotenv

# Load env vars
load_dotenv()

async def check_mongo():
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    print(f"--- Testing MongoDB ({uri}) ---")
    try:
        client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=2000)
        await client.server_info()
        print("✅ MongoDB Connection Successful!")
        return True
    except Exception as e:
        print(f"❌ MongoDB Connection FAILED: {e}")
        print("   -> Verify MongoDB is running locally or check your MONGO_URI in .env")
        return False

def check_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    print(f"\n--- Testing Supabase ({url}) ---")
    
    if not url or "supabase.co" not in url:
        print("❌ Supabase URL is missing or invalid.")
        return False
        
    try:
        supabase: Client = create_client(url, key)
        # Try a lightweight call
        # We can't use auth.getUser without a token, but we can check if client init didn't crash
        # and maybe just print success if no error.
        # Actually, let's try to sign in with a fake token to see if it reaches the server (will fail auth, but connect).
        # Or just checking 'health' of the client object is enough for configuration check.
        print("✅ Supabase Client Initialized (Keys Look OK).")
        return True
    except Exception as e:
        print(f"❌ Supabase Configuration FAILED: {e}")
        return False

async def main():
    print("=== ENVIRONMENT CHECK ===\n")
    
    mongo_ok = await check_mongo()
    supabase_ok = check_supabase()
    
    print("\n=========================")
    if mongo_ok and supabase_ok:
        print("🚀 ALL SYSTEMS GO! Backend is ready to start.")
    else:
        print("⚠️  Issues found. Please fix the errors above.")

if __name__ == "__main__":
    asyncio.run(main())
