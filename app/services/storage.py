# app/services/storage.py
import boto3
import os
from botocore.exceptions import NoCredentialsError
from fastapi import UploadFile
import uuid
from typing import Optional
from urllib.parse import urlparse

# Cargar config
ENDPOINT_URL = os.getenv("SUPABASE_ENDPOINT_URL")
ACCESS_KEY = os.getenv("SUPABASE_ACCESS_KEY")
SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")
BUCKET_NAME = os.getenv("SUPABASE_BUCKET_NAME")
REGION = os.getenv("SUPABASE_REGION")

if not all([ENDPOINT_URL, ACCESS_KEY, SECRET_KEY, BUCKET_NAME]):
    raise ValueError("Missing Supabase environment variables.")

s3_client = boto3.client(
    's3',
    endpoint_url=ENDPOINT_URL,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name=REGION
)

async def upload_image_to_supabase(file: UploadFile, user_id: str) -> Optional[str]:
    """Sube archivo a Supabase Storage en carpeta del usuario y devuelve URL pública."""
    
    # Secure Extension Handling
    file_extension = ""
    if file.filename:
        _, ext = os.path.splitext(file.filename)
        if ext: file_extension = ext.lstrip(".")
    if not file_extension and file.content_type:
        file_extension = file.content_type.split("/")[-1].split("+")[0]
    file_extension = file_extension or "bin"
    
    # Organize files by user_id
    unique_filename = f"{user_id}/{uuid.uuid4()}.{file_extension}"
    
    try:
        s3_client.upload_fileobj(
            file.file,
            BUCKET_NAME,
            unique_filename,
            ExtraArgs={'ContentType': file.content_type} 
        )
        
        # Parcing the endpoint URL to extract hostname
        parsed_url = urlparse(ENDPOINT_URL)
        hostname = parsed_url.hostname
        assert hostname is not None, "Could not parse hostname"
        public_url = f"https://{hostname}/storage/v1/object/public/{BUCKET_NAME}/{unique_filename}"
        
        return public_url

    except Exception as e:
        print(f"Error S3: {e}")
        return None