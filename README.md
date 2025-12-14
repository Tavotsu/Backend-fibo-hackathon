# Backend FIBO Hackathon - AI Art Director

Backend API para el FIBO Hackathon de Bria AI. Sistema de generación automática de variaciones de productos usando FIBO (JSON-native text-to-image model).

## 🎯 Características

- **Integración completa con FIBO API** (Generate, Refine, Inspire modes)
- **Agente LLM** que convierte brand guidelines en variaciones creativas
- **Generación batch** de múltiples variaciones
- **MongoDB** para persistencia de campañas y planes
- **Supabase Storage** para almacenamiento de imágenes
- **Workflow profesional**: Campaign → Product → Plan → Execute

## 🚀 Setup

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Copia `.env.example` a `.env` y completa las API keys:

```bash
cp .env.example .env
```

**Variables requeridas:**
- `BRIA_API_KEY`: API key de Bria AI ([obtener aquí](https://platform.bria.ai/console/account/api-keys))
- `MONGO_URI`: URI de MongoDB
- `SUPABASE_*`: Credenciales de Supabase Storage

**Variables opcionales:**
- `OPENAI_API_KEY`: Para agente LLM (si no está, usa variaciones mock)
- `GOOGLE_API_KEY`: Alternativa para VLM

### 3. Ejecutar servidor

```bash
uvicorn app.main:app --reload
```

El servidor estará disponible en `http://localhost:8000`

## 📋 Endpoints

### Crear Campaña
```http
POST /api/v1/campaigns
Content-Type: application/json

{
  "name": "Summer Collection 2025",
  "brand_guidelines": {
    "primary_color": "coral pink",
    "mood": "fresh and vibrant",
    "target_audience": "young professionals",
    "style_preferences": ["minimalist", "modern"]
  }
}
```

### Subir Producto
```http
POST /api/v1/campaigns/{campaign_id}/upload-product
Content-Type: multipart/form-data

file: [imagen del producto]
```

### Generar Plan (con AI Agent)
```http
POST /api/v1/campaigns/{campaign_id}/generate-plan
Content-Type: application/json

{
  "product_id": "producto_id",
  "variations_count": 5
}
```

### Ejecutar Plan (con FIBO)
```http
POST /api/v1/campaigns/{campaign_id}/execute
Content-Type: application/json

{
  "plan_id": "plan_id",
  "selected_variations": [0, 1, 2]
}
```

### Ver Plan y Resultados
```http
GET /api/v1/plans/{plan_id}
```

## 🏗️ Arquitectura

```
app/
├── main.py              # FastAPI app + MongoDB setup
├── core/
│   └── config.py        # Configuración centralizada
├── api/
│   └── routes.py        # Endpoints REST
├── schemas/
│   └── fibo.py          # Modelos Pydantic + Beanie
└── services/
    ├── bria.py          # Integración FIBO API
    ├── agent.py         # Agente LLM
    └── storage.py       # Supabase Storage
```

## 🎨 Modos de FIBO

### Generate Mode
Genera imagen desde prompt de texto:
```python
{
  "prompt": "Professional product photography...",
  "camera_angle": "eye_level",
  "lighting_mode": "studio",
  "aspect_ratio": "1:1"
}
```

### Refine Mode
Refina imagen existente con nuevas instrucciones:
```python
{
  "structured_prompt": {...},  # JSON previo
  "prompt": "make it warmer",
  "seed": 42
}
```

### Inspire Mode
Genera variación inspirada en imagen:
```python
{
  "reference_image_url": "https://...",
  "prompt": "make it futuristic"
}
```

## 🤖 Agente LLM

El agente convierte brand guidelines en variaciones creativas:

**Input:**
- Brand guidelines (color, mood, audience)
- Descripción del producto
- Número de variaciones

**Output:**
- Lista de variaciones con parámetros FIBO optimizados
- Conceptos creativos (Hero Shot, Lifestyle, Dramatic, etc.)

## 📦 Dependencias

- **FastAPI**: Framework web
- **Beanie**: ODM para MongoDB
- **httpx**: Cliente HTTP async para FIBO API
- **DeepSeek**: Agente LLM
- **boto3**: Cliente S3 para Supabase
- **pydantic-settings**: Gestión de configuración

## 🔑 Obtener API Keys

1. **Bria AI**: https://platform.bria.ai/console/account/api-keys
2. **OpenAI**: https://platform.openai.com/api-keys
3. **MongoDB**: https://www.mongodb.com/cloud/atlas
4. **Supabase**: https://supabase.com/dashboard/project/_/settings/api

## 📝 Licencia

Este proyecto es para el FIBO Hackathon de Bria AI.
