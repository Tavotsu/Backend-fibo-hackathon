# app/services/storage.py
"""
Servicio de almacenamiento de imágenes
Soporta Supabase Storage (S3) o almacenamiento local
"""

import os
import uuid
import logging
from typing import Optional
from urllib.parse import urlparse
from pathlib import Path
from fastapi import UploadFile

logger = logging.getLogger(__name__)

# Cargar config
ENDPOINT_URL = os.getenv("SUPABASE_ENDPOINT_URL")
ACCESS_KEY = os.getenv("SUPABASE_ACCESS_KEY")
SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")
BUCKET_NAME = os.getenv("SUPABASE_BUCKET_NAME")
REGION = os.getenv("SUPABASE_REGION")

# Cliente S3 (solo si está configurado)
s3_client = None
SUPABASE_CONFIGURED = all([ENDPOINT_URL, ACCESS_KEY, SECRET_KEY, BUCKET_NAME])

if SUPABASE_CONFIGURED:
    try:
        import boto3
        s3_client = boto3.client(
            's3',
            endpoint_url=ENDPOINT_URL,
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
            region_name=REGION
        )
        logger.info("✅ Supabase Storage configurado")
    except Exception as e:
        logger.warning(f"⚠️ Error configurando Supabase: {e}")
        SUPABASE_CONFIGURED = False
else:
    logger.info("📁 Supabase no configurado - usando almacenamiento local")


async def upload_image_to_supabase(file: UploadFile) -> Optional[str]:
    """
    Sube archivo a Supabase Storage y devuelve URL pública.
    Si Supabase no está configurado, guarda localmente.
    """
    
    # Secure Extension Handling
    file_extension = ""
    if file.filename:
        _, ext = os.path.splitext(file.filename)
        if ext: file_extension = ext.lstrip(".")
    if not file_extension and file.content_type:
        file_extension = file.content_type.split("/")[-1].split("+")[0]
    file_extension = file_extension or "bin"
    
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    
    # Si Supabase está configurado, subir a S3
    if SUPABASE_CONFIGURED and s3_client:
        try:
            s3_client.upload_fileobj(
                file.file,
                BUCKET_NAME,
                unique_filename,
                ExtraArgs={'ContentType': file.content_type, 'ACL': 'public-read'} 
            )
            
            # Parsing the endpoint URL to extract hostname
            parsed_url = urlparse(ENDPOINT_URL)
            hostname = parsed_url.hostname
            assert hostname is not None, "Could not parse hostname"
            public_url = f"https://{hostname}/storage/v1/object/public/{BUCKET_NAME}/{unique_filename}"
            
            return public_url

        except Exception as e:
            logger.error(f"Error S3: {e}")
            # Fallback a almacenamiento local
    
    # Almacenamiento local como fallback
    try:
        data_dir = Path(os.getenv("DATA_DIR", "./data"))
        data_dir.mkdir(parents=True, exist_ok=True)
        
        local_path = data_dir / unique_filename
        
        content = await file.read()
        with open(local_path, "wb") as f:
            f.write(content)
        
        # Devolver URL relativa (el frontend puede accederla via /data/)
        return f"/data/{unique_filename}"
        
    except Exception as e:
        logger.error(f"Error guardando localmente: {e}")
        return None