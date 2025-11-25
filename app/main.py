from fastapi import FastAPI
from app.api.routes import router as api_router

app = FastAPI(
    title="AI Art direction API",
    description="Backend for BRIA Hackathon",
    version="1.0.0"
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def health_check():
    return {"status": "online", "message": "API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)