from faasmctl.util.config import get_faasm_ini_file, get_faasm_ini_value
from minio import Minio
from minio.error import S3Error
from os import listdir
from os.path import isfile, join


def get_minio_client():
    minio_port = get_faasm_ini_value(get_faasm_ini_file(), "Faasm", "minio_port")

    client = Minio(
        "localhost:{}".format(minio_port),
        access_key="minio",
        secret_key="minio123",
        secure=False,
        region="",
    )

    return client


def list_buckets():
    client = get_minio_client()
    for bucket in client.list_buckets():
        print(bucket)


def list_objects(bucket, recursive=False):
    client = get_minio_client()
    for bucket_key in client.list_objects(bucket, recursive=recursive):
        print(bucket_key.object_name)


def clear_bucket(bucket):
    client = get_minio_client()

    # Got to make sure the bucket is empty first
    for bucket_key in client.list_objects(bucket, recursive=True):
        client.remove_object(bucket, bucket_key.object_name)

    client.remove_bucket(bucket)


def upload_file(bucket, host_path, s3_path):
    client = get_minio_client()

    # Create the bucket if it does not exist
    found = client.bucket_exists(bucket)
    if not found:
        client.make_bucket(bucket)

    # Upload the file, renaming it in the process
    try:
        client.fput_object(bucket, s3_path, host_path)
    except S3Error as ex:
        print("error: error uploading file to s3: {}".format(ex))
        raise RuntimeError("error: error uploading file to s3")


def upload_dir(bucket, host_path, s3_path):
    for f in listdir(host_path):
        host_file_path = join(host_path, f)

        if isfile(host_file_path):
            s3_file_path = join(s3_path, f)
            upload_file(bucket, host_file_path, s3_file_path)


def dump_object(bucket, path):
    client = get_minio_client()
    response = client.get_object(bucket, path)

    return response
