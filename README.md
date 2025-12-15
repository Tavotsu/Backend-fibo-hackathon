# BrandLab | Backend for AI-driven Product Variation

BrandLab is a backend service that automates the generation of product image variations using Bria's FIBO (JSON-native text-to-image) model. It provides an agent-driven workflow that converts brand guidelines into structured variation plans and executes them against the FIBO API. The service includes persistence (MongoDB), image storage (Supabase), and an HTTP API built with FastAPI.

**Contents:** quickstart, configuration, Bria FIBO integration details, API reference, example outputs, and development notes.

**Requirements**
- Python 3.10+ recommended
- A running MongoDB instance (URI)
- Supabase project for object storage (or compatible S3)
- Bria API key with FIBO access
- Optional: OpenAI API key for the LLM agent

## Quickstart

1. Create a Python virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

2. Copy the example environment file and set secrets:

```bash
copy .env.example .env
# Edit .env and add your BRIA_API_KEY, MONGO_URI, SUPABASE_*, etc.
```

3. Run the development server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000.

## Environment Variables
Populate `.env` with at least the following values:

- `BRIA_API_KEY` — Bria platform API key (required)
- `MONGO_URI` — MongoDB connection string (required)
- `SUPABASE_URL` — Supabase project URL (required for storage)
- `SUPABASE_KEY` — Supabase service key (or S3 credentials if using S3)
- `OPENAI_API_KEY` — Optional: used by the LLM agent for plan generation

Other configuration values are in `app/core/config.py`.

## Bria FIBO Integration

BrandLab uses Bria's FIBO model to generate, refine, and inspire image variants. The integration follows three modes:

- Generate: create an image from text-based parameters.
- Refine: update an existing structured prompt / image with new instructions.
- Inspire: produce variations inspired by a reference image.

Authentication: include the `BRIA_API_KEY` in the `Authorization` header as a bearer token.

Example Python (async) request using `httpx`:

```python
import httpx

async def call_fibo_generate(api_key: str, payload: dict) -> dict:
    url = "https://api.bria.ai/v1/fibo/generate"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        return r.json()

# Example payload
payload = {
    "prompt": "High-quality product photography of a modern ceramic mug on a white background",
    "camera_angle": "eye_level",
    "lighting_mode": "studio",
    "aspect_ratio": "1:1",
    "seed": 12345
}

# call_fibo_generate(BRIA_API_KEY, payload)
```

Example curl (Generate mode):

```bash
curl -X POST "https://api.bria.ai/v1/fibo/generate" \\
  -H "Authorization: Bearer $BRIA_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"prompt":"Modern product photography of a sneaker","aspect_ratio":"1:1"}'
```

Example typical response (abbreviated):

```json
{
  "id": "img_abc123",
  "image_url": "https://.../image.png",
  "seed": 12345,
  "metadata": {
    "camera_angle": "eye_level",
    "lighting_mode": "studio",
    "aspect_ratio": "1:1"
  }
}
```

Note: the exact response fields may vary by Bria API version — the code in `app/services/bria.py` adapts returned payloads into the project's domain models.

## Project HTTP API (select endpoints)

The backend exposes REST endpoints for campaigns, products, plans, and execution. Example endpoints:

- `POST /api/v1/campaigns` — create a campaign with brand guidelines.
- `POST /api/v1/campaigns/{campaign_id}/upload-product` — upload product image.
- `POST /api/v1/campaigns/{campaign_id}/generate-plan` — ask the LLM agent to produce a variation plan.
- `POST /api/v1/campaigns/{campaign_id}/execute` — run a plan using FIBO to create images.
- `GET /api/v1/plans/{plan_id}` — inspect generated plan and results.

Example create-campaign request body:

```json
{
  "name": "Summer Collection",
  "brand_guidelines": {
    "primary_color": "coral pink",
    "mood": "fresh and vibrant",
    "target_audience": "young professionals",
    "style_preferences": ["minimalist", "modern"]
  }
}
```

## Example workflow

1. Create a campaign with brand guidelines.
2. Upload a product image for the campaign.
3. Request the agent to generate a plan (N variations). The agent outputs structured prompts with camera angle, lighting, aspect ratio, and creative concept.
4. Execute the plan. Each plan item is submitted to Bria (Generate/Refine/Inspire) and the resulting images are stored in Supabase. Metadata and links are saved to MongoDB.

## Storage and Persistence

- MongoDB stores campaigns, products, plans, and execution results using Beanie models defined in `app/schemas/fibo.py`.
- Images are uploaded to Supabase storage via `app/services/storage.py`. The service can be adapted to S3-compatible endpoints.

## Development notes

- Code entrypoint: `app/main.py`.
- API routes: `app/api/routes.py`.
- Bria integration: `app/services/bria.py` (or `bria_v2.py` for alternate flows).
- LLM planner/agent: `app/services/llm_planner.py` and `app/services/agent.py`.

When modifying integration code, add unit tests for the request/response transformation and use a recorded HTTP fixture for external calls.

## Testing

1. Install test dependencies (if any) and run pytest:

```bash
pip install -r requirements.txt
pytest -q
```

2. For integration tests that call Bria or Supabase, use mock keys and a local fixture or run tests in a staging account.

## Troubleshooting

- Invalid or missing `BRIA_API_KEY`: verify the key and ensure it has FIBO access.
- Mongo connection issues: confirm `MONGO_URI` is reachable from the host.
- Storage upload failures: check `SUPABASE_URL` and `SUPABASE_KEY` or S3 credentials.

## Extending and Production

- Add authentication and role-based access to the API.
- Add background workers (e.g., Celery or RQ) for high-volume plan execution.
- Add observability: structured logs and tracing.

## Contribution and License

This repository is intended for the FIBO Hackathon and is published under the included LICENSE file. Contributions and issues are welcome — open a PR or an issue in the project repository.

---

For implementation details, see the following key files:

- [app/main.py](app/main.py)
- [app/services/bria.py](app/services/bria.py)
- [app/services/agent.py](app/services/agent.py)
- [app/services/storage.py](app/services/storage.py)

## BrandLab team

- Tavotsu -> `Backend & Deployment`
- Zenith-AB -> `Backend & AI integration`
- Krist0-afk -> `Frontend`
- Elchacra -> `Testing`
- ManuelADMN -> `AI integration`

