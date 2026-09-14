from google.cloud import storage


def delete_bucket(bucket_name):
    """Deletes a bucket. The bucket must be empty."""
    storage_client = storage.Client(project="gcai-sep-26")
    bucket = storage_client.get_bucket(bucket_name)
    bucket.delete()
    print(f"Bucket {bucket.name} deleted")

delete_bucket("test-bucket-afc-1123")