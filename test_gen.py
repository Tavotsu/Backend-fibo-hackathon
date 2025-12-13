import requests
import time
import sys

BASE_URL = "http://localhost:8001/api/v1"

def test_generation():
    print(f"🚀 Iniciando prueba contra {BASE_URL}")
    
    # 1. Iniciar Job
    try:
        resp = requests.post(
            f"{BASE_URL}/generate-async",
            data={
                "prompt": "A futuristic city with flying cars, cyberpunk style",
                "variations": 1,
                "aspect_ratio": "16:9"
            }
        )
        resp.raise_for_status()
        data = resp.json()
        job_id = data["job_id"]
        print(f"✅ Job creado: {job_id}")
    except Exception as e:
        print(f"❌ Error creando job: {e}")
        if 'resp' in locals(): print(resp.text)
        return

    # 2. Polling
    print("⏳ Esperando resultados...")
    while True:
        try:
            resp = requests.get(f"{BASE_URL}/jobs/{job_id}")
            resp.raise_for_status()
            status = resp.json()
            
            stage = status.get("stage")
            progress = status.get("progress")
            print(f"Status: {stage} ({progress}%)")
            
            if stage == "DONE":
                print("\n🎉 VIDEO GENERATION COMPLETE!")
                results = status.get("results", [])
                for i, url in enumerate(results):
                    print(f"Result {i+1}: {url}")
                break
            
            if stage == "ERROR":
                print(f"\n❌ VIDEO GENERATION FAILED: {status.get('error')}")
                break
            
            time.sleep(2)
            
        except Exception as e:
            print(f"⚠️ Error polling: {e}")
            time.sleep(2)

if __name__ == "__main__":
    test_generation()
