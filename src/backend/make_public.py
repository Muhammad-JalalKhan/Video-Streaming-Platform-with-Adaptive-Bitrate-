import json
from minio import Minio

# 1. Connect to MinIO
minio_client = Minio(
    "localhost:9000", 
    access_key="admin",
    secret_key="password123",
    secure=False
) 

BUCKET_NAME = "processed-videos"

# 2. Define a "Public Read-Only" Policy
policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"AWS": "*"},
            "Action": ["s3:GetObject"],
            "Resource": [f"arn:aws:s3:::{BUCKET_NAME}/*"]
        }
    ]
}

# 3. Apply the policy to the bucket
try:
    minio_client.set_bucket_policy(BUCKET_NAME, json.dumps(policy))
    print(f"SUCCESS! The '{BUCKET_NAME}' bucket is now PUBLIC.")
except Exception as e:
    print(f"Error: {e}")