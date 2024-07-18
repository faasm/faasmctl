from invoke import task
from minio import Minio


@task
def list(ctx):
    # TODO: read port from environment
    client = Minio(
        "localhost:9000",
        access_key="minio",
        secret_key="minio123",
        secure=False,
        region="",
    )
    for bucket in client.list_buckets():
        print(bucket)
