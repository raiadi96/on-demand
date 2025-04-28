# config.py

# AWS Configuration
AWS_REGION = "us-east-1"  # Update this if you are using a different AWS region

# Optional: if using IAM role on EC2 / credentials already in ~/.aws/credentials, leave these None
AWS_ACCESS_KEY_ID = "AKIAZRORWT73MD5UHUYN"
AWS_SECRET_ACCESS_KEY = "BMUeDt/CwESQwhz9c7AzPJu1Uw1FWe1KZqZ98B0w"

# S3 UUID to Asset Mapping
# Map your UUIDs to corresponding S3 Bucket and Object Key
UUID_TO_S3 = {
    "123765": {
        "bucket": "aditya-aduio-sample",
        "key": "audio.mp3"
    },
    # Add more UUID mappings here as needed
}

# Subtitle Format Configuration
# Options: "srt" or "webvtt"
SUBTITLE_FORMAT = "webvtt"
