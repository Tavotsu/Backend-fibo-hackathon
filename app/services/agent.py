import os
import json
from openai import OpenAI
from app.schemas.fibo import AgentOutput, BriaStructuredPrompt

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def analyze_and_plan(image_url: str, mood: str, count: int = 3) -> list[BriaStructuredPrompt]:
    """
    Usa GPT-4o Vision para analizar el producto y generar 
    Structured Prompts (JSON) válidos para Bria v2.
    """
    # Le damos el prompt al modelo
    system_prompt = """
    Eres un Director de Arte experto en Fotografía Publicitaria y en el modelo generativo Bria AI v2.
    Tu objetivo es tomar la imagen de un producto y generar variaciones creativas para una campaña de marketing.
    
    IMPORTANTE:
    1. NO uses prompts de texto normales. Debes generar un JSON ESTRUCTURADO (BriaStructuredPrompt).
    2. Mantén la integridad del producto. Describe el objeto principal basándote en la imagen que ves.
    3. Adapta el 'background_setting', 'lighting' y 'aesthetics' al MOOD solicitado por el usuario.
    4. Sé técnico con 'camera_angle' y 'lens_focal_length' (ej: 50mm, 85mm, macro).
    """

    user_message = f"""
    Aquí tienes la imagen de mi producto: {image_url}
    
    El Mood/Vibe de la campaña es: "{mood}".
    
    Genera {count} variaciones distintas de configuración visual (JSON) para Bria.
    Varía los ángulos y la iluminación entre las opciones.
    """

    try:
        print(f"Consultando a GPT-4o para mood: {mood}...")
        response = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": user_message},
                        {
                            "type": "image_url", 
                            "image_url": {"url": image_url}
                        }
                    ]
                }
            ],
            response_format=AgentOutput,
        )
        
        parsed_output = response.choices[0].message.parsed
        if not parsed_output:
            print("El Agente no devolvió un resultado analizable.")
            return []

        variations = parsed_output.variations
        print(f"Agente generó {len(variations)} variaciones estructuradas.")
        return variations

    except Exception as e:
        print(f"Error en el Agente: {e}")
        return []