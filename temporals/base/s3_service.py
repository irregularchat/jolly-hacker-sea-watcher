import os
import base64
import uuid
import logging
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger("s3_service")

class S3Service:
    def __init__(self):
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )
        self.bucket = os.getenv("S3_BUCKET_NAME")
        if not self.bucket:
            raise ValueError("S3_BUCKET_NAME environment variable not set.")

    def upload_base64_image(self, base64_data: str, prefix: str = "maritime-images/") -> Optional[str]:
        try:
            header, encoded = base64_data.split(",", 1) if "," in base64_data else (None, base64_data)
            image_bytes = base64.b64decode(encoded)
            ext = self._get_extension(header)
            key = f"{prefix}{uuid.uuid4()}{ext}"
            self.s3.put_object(Bucket=self.bucket, Key=key, Body=image_bytes, ACL="public-read", ContentType=self._get_content_type(header))
            url = f"https://{self.bucket}.s3.{self.s3.meta.region_name}.amazonaws.com/{key}"
            logger.info(f"Image uploaded to S3: {url}")
            return url
        except (BotoCoreError, ClientError, Exception) as e:
            logger.error(f"Failed to upload image to S3: {e}")
            return None

    def _get_extension(self, header: Optional[str]) -> str:
        if not header:
            return ".jpg"
        if "image/jpeg" in header:
            return ".jpg"
        if "image/png" in header:
            return ".png"
        if "image/gif" in header:
            return ".gif"
        return ".jpg"

    def _get_content_type(self, header: Optional[str]) -> str:
        if not header:
            return "image/jpeg"
        if "image/jpeg" in header:
            return "image/jpeg"
        if "image/png" in header:
            return "image/png"
        if "image/gif" in header:
            return "image/gif"
        return "image/jpeg"

# Singleton instance
s3_service = S3Service()
