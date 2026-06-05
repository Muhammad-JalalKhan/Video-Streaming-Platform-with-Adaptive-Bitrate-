from minio import Minio
import json

# Connect to MinIO
client = Minio(
    "localhost:9000",
    access_key="admin",
    secret_key="password123",
    secure=False
)

# The standard AWS/MinIO policy to make a bucket completely readable to the public
policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"AWS": "*"},
            "Action": ["s3:GetObject"],
            "Resource": ["arn:aws:s3:::processed-videos/*"]
        }
    ]
}

# Apply the policy
try:
    client.set_bucket_policy("processed-videos", json.dumps(policy))
    print("✅ SUCCESS: 'processed-videos' is now PUBLIC!")
except Exception as e:
    print(f"❌ Error: {e}")