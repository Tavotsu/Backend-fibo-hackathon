import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def check_bria():
    print("--- Testing Bria AI Connection ---")
    
    api_key = os.getenv("BRIA_API_KEY")
    # Based on search results: V2 is more standard now
    base_url = "https://engine.prod.bria-api.com/v2" 
    endpoint = "/image/generate"
    
    # Simulate "inspire" mode payload (Image + Prompt)
    if not api_key:
        print("❌ FAIL: BRIA_API_KEY is missing in .env")
        return

    print(f"API Key: {api_key[:5]}... (Redacted)")
    
    headers = {
        "api_token": api_key,
        "Content-Type": "application/json"
    }

    # Using a placeholder image for testing
    payload = {
        "num_results": 1,
        "sync": True,
        "prompt": "A beautiful landscape version of this image",
        "images": ["https://picsum.photos/512/512"] # Public URL required by Bria V2
    }
    
    url = f"{base_url}{endpoint}"
    print(f"Requesting: {url}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Success! Response:")
                print(data)
                if "result_url" in data:
                    print(f"🖼️ Image URL: {data['result_url']}")
                elif isinstance(data, list) and len(data) > 0 and "urls" in data[0]:
                     print(f"🖼️ Image URL: {data[0]['urls'][0]}")
                else:
                    print("⚠️ Warning: Unexpected JSON structure.")
            else:
                print(f"❌ API Error: {response.text}")
                
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_bria())
