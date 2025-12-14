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
            
            # 3. Test Upload and Public Access
            print("\nTesting Upload & Public Access...")
            test_filename = "test_connectivity.txt"
            try:
                s3.put_object(Bucket=bucket, Key=test_filename, Body=b"Hello Bria", ContentType="text/plain")
                print("✅ Upload successful.")
                
                # Construct Public URL
                endpoint_clean = endpoint.replace("/storage/v1/s3", "")
                public_url = f"{endpoint_clean}/storage/v1/object/public/{bucket}/{test_filename}"
                print(f"   URL: {public_url}")
                
                import requests
                r = requests.get(public_url, timeout=10)
                if r.status_code == 200:
                    print("✅ Public URL is accessible (HTTP 200). Bria should be able to read it.")
                else:
                    print(f"❌ Public URL FAILED ({r.status_code}). Bria cannot read this file!")
                    print("   👉 ACTION: Go to Supabase > Storage > ai_art_director > Toggle 'Public Bucket' to ON.")
            except Exception as e:
                print(f"❌ Upload/Fetch Error: {repr(e)}")
            finally:
                # Cleanup
                try:
                    s3.delete_object(Bucket=bucket, Key=test_filename)
                    print("🧹 Cleanup: Test object deleted.")
                except Exception as cleanup_e:
                    print(f"⚠️ Cleanup Failed: {repr(cleanup_e)}")

    except ClientError as e:
        print(f"\n❌ S3 Error: {e}")
    except Exception as e:
        print(f"\n❌ General Error: {repr(e)}")

if __name__ == "__main__":
    check_s3()
