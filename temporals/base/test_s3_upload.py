import os
import boto3
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

bucket = os.getenv("S3_BUCKET_NAME")
key = "test-upload.txt"
body = b"This is a test file from manual script."

try:
    resp = s3.put_object(Bucket=bucket, Key=key, Body=body, ContentType="text/plain")
    print(f"Upload succeeded: {resp}")
    print(f"Check: https://{bucket}.s3.{s3.meta.region_name}.amazonaws.com/{key}")
except Exception as e:
    print(f"Upload failed: {e}")
