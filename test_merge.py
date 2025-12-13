import requests
import time
import os
import sys

BASE_URL = "http://localhost:8001/api/v1"
IMAGE_PATH = r"C:\Users\Zenit\Desktop\Hackaton\backend legacy\data\295b1a7f-c83f-41d5-968b-76f6d6ff4dd5.png"

def test_pipeline():
    print("🚀 Iniciando prueba completa del backend...")
    
    # 1. Verificar Health
    try:
        r = requests.get("http://localhost:8001/health")
        print(f"📡 Health check: {r.status_code} {r.json()}")
    except Exception as e:
        print(f"❌ Backend no responde: {e}")
        return

    # 2. Iniciar Job
    print(f"\n📤 Subiendo imagen ({os.path.basename(IMAGE_PATH)}) e iniciando job...")
    
    if not os.path.exists(IMAGE_PATH):
        print(f"❌ No se encuentra la imagen de prueba: {IMAGE_PATH}")
        return

    files = {
        'image': open(IMAGE_PATH, 'rb')
    }
    data = {
        'prompt': 'A futuristic bottle of perfume on a neon city background, cyberpunk style',
        'brand_guidelines': 'Use cyan and magenta colors. Maintain premium look.',
        'variations': '2',
        'aspect_ratio': '1:1'
    }
    
    try:
        r = requests.post(f"{BASE_URL}/generate-async", files=files, data=data)
        if r.status_code != 200:
            print(f"❌ Error al iniciar job: {r.text}")
            return
        
        job_id = r.json().get("job_id")
        print(f"✅ Job iniciado ID: {job_id}")
    except Exception as e:
        print(f"❌ Excepción al iniciar job: {e}")
        return

    # 3. Polling Status
    print("\n⏳ Monitoreando progreso...")
    completed = False
    
    while not completed:
        try:
            r = requests.get(f"{BASE_URL}/jobs/{job_id}")
            if r.status_code != 200:
                print(f"⚠️ Error checkeando status: {r.status_code}")
                time.sleep(2)
                continue
                
            status = r.json()
            stage = status.get("stage")
            progress = status.get("progress")
            events = status.get("events", [])
            
            # Mostrar último evento
            last_msg = events[-1].get("msg") if events else "..."
            timestamp = events[-1].get("t") if events else 0
            
            print(f"[{stage}] {progress:.1f}% - {last_msg}")
            
            if stage == "DONE":
                print(f"\n✅ Job Completado!")
                print("Resultados:")
                results = status.get("results", [])
                for res in results:
                    print(f" - {res}")
                
                partial = status.get("partial_results", [])
                print(f"Resultados Parciales (Streaming): {len(partial)}")
                completed = True
                
            elif stage == "ERROR":
                print(f"\n❌ Job Falló: {status.get('error')}")
                completed = True
                
            time.sleep(2)
            
        except KeyboardInterrupt:
            print("\n🛑 Prueba detenida por usuario")
            break
        except Exception as e:
            print(f"⚠️ Error polling: {e}")
            time.sleep(2)

if __name__ == "__main__":
    test_pipeline()
