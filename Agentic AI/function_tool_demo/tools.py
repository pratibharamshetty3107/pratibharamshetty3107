from google.cloud import storage

project = "gcai-sep-26"

def list_buckets():
    """Lists all buckets."""
    storage_client = storage.Client(project=project)
    buckets = storage_client.list_buckets()
    bucket_names = [bucket.name for bucket in buckets]
    for name in bucket_names:
        print(name)
    return {"buckets": bucket_names}

def create_bucket(bucket_name: str):
    """
    This function is used to create bucket
    """
    storage_client = storage.Client(project=project)
    bucket = storage_client.bucket(bucket_name)
    new_bucket = storage_client.create_bucket(bucket, location="us")
    print(
        "Created bucket {} in {} with storage class {}".format(
            new_bucket.name, new_bucket.location, new_bucket.storage_class
        )
    )
    return {"name": new_bucket.name, "location": new_bucket.location, "storage_class": new_bucket.storage_class}

def delete_bucket(bucket_name: str):
    """Deletes a bucket. The bucket must be empty."""
    storage_client = storage.Client(project=project)
    bucket = storage_client.get_bucket(bucket_name)
    bucket.delete()
    print(f"Bucket {bucket_name} deleted")
    return {"deleted": bucket_name}


