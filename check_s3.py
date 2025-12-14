import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()

def check_s3():
    print("--- Testing Supabase S3 Connection ---")
    
    endpoint = os.getenv("SUPABASE_ENDPOINT_URL")
    key = os.getenv("SUPABASE_ACCESS_KEY")
    secret = os.getenv("SUPABASE_SECRET_KEY")
    bucket = os.getenv("SUPABASE_BUCKET_NAME")
    region = os.getenv("SUPABASE_REGION")

    print(f"Endpoint: {endpoint}")
    print(f"Bucket:   {bucket}")
    print(f"Region:   {region}")
    # Don't print keys for security
    
    if "PLACEHOLDER" in key or "PLACEHOLDER" in secret:
        print("\n❌ FAIL: You still have PLACEHOLDER keys in .env!")
        print("   Please replace them with real Supabase Storage keys.")
        return

    try:
        s3 = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=key,
            aws_secret_access_key=secret,
            region_name=region
        )
        
        # 1. List Buckets
        print("\nAttempting to list buckets...")
        response = s3.list_buckets()
        buckets = [b['Name'] for b in response['Buckets']]
        print(f"✅ Connection Successful! Buckets found: {buckets}")
        
        # 2. Check specific bucket
        if bucket not in buckets:
            print(f"\n❌ WARNING: Bucket '{bucket}' not found in the list!")
            print("   Did you create it in Supabase Dashboard -> Storage -> New Bucket?")
        else:
            print(f"✅ Bucket '{bucket}' exists.")
            
            # 3. Try partial upload test (optional, just listing is usually enough proof of auth)
            print("✅ Write permission check skipped (Listing succeeded).")

    except ClientError as e:
        print(f"\n❌ S3 Error: {e}")
    except Exception as e:
        print(f"\n❌ General Error: {e}")

if __name__ == "__main__":
    check_s3()
