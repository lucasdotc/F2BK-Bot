import os
import logging


def sync_knowledge_from_bucket(bucket: str, local_dir: str = "knowledge", prefix: str = "") -> int:
    """
    Downloads all .md objects under `prefix` in the given private bucket into `local_dir`,
    preserving the key's relative path. Works with AWS S3 by default; set S3_ENDPOINT_URL
    to point at an S3-compatible provider (e.g. Cloudflare R2) instead.
    """
    import boto3

    endpoint_url = os.environ.get("S3_ENDPOINT_URL") or None
    region_name = os.environ.get("AWS_REGION") or ("auto" if endpoint_url else None)
    client = boto3.client("s3", endpoint_url=endpoint_url, region_name=region_name)

    os.makedirs(local_dir, exist_ok=True)

    downloaded = 0
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.endswith(".md"):
                continue
            relative_path = key[len(prefix):].lstrip("/") if prefix else key
            dest_path = os.path.join(local_dir, relative_path)
            os.makedirs(os.path.dirname(dest_path) or local_dir, exist_ok=True)
            client.download_file(bucket, key, dest_path)
            downloaded += 1

    logging.info(f"Synced {downloaded} knowledge file(s) from bucket '{bucket}'.")
    return downloaded
