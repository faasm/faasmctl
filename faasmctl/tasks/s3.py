from faasmctl.util.backend import COMPOSE_BACKEND, K8S_BACKEND
from faasmctl.util.config import (
    BACKEND_INI_STRING,
    get_faasm_ini_file,
    get_faasm_ini_value,
)
from faasmctl.util.s3 import (
    list_buckets as do_list_buckets,
    clear_bucket as do_clear_bucket,
    list_objects as do_list_objects,
    upload_file as do_upload_file,
    upload_dir as do_upload_dir,
    dump_object as do_dump_object,
)
from invoke import task


@task
def list_buckets(ctx):
    """
    List available buckets
    """
    do_list_buckets()


@task
def clear_bucket(ctx, bucket):
    """
    Clear (i.e. remove) bucket
    """
    do_clear_bucket(bucket)


@task
def get_url(ctx):
    """
    Get the URL for the S3 server
    """
    ini_file = get_faasm_ini_file()

    backend = get_faasm_ini_value(ini_file, "Faasm", BACKEND_INI_STRING)
    if backend == COMPOSE_BACKEND:
        print("127.0.0.1")
    elif backend == K8S_BACKEND:
        raise RuntimeError("Unimplemented for backend: {}".format(backend))
    else:
        raise RuntimeError("Unrecognised backend: {}".format(backend))


@task
def list_objects(ctx, bucket, recursive=False):
    """
    List available objects in bucket
    """
    do_list_objects(bucket, recursive)


@task
def upload_file(ctx, bucket, host_path, s3_path):
    """
    Upload a file to S3
    """
    do_upload_file(bucket, host_path, s3_path)


@task
def upload_dir(ctx, bucket, host_path, s3_path):
    """
    Upload all the files in a directory to S3
    """
    do_upload_dir(bucket, host_path, s3_path)


@task
def dump_object(ctx, bucket, path):
    """
    Dump the contents of an object in S3
    """
    response = do_dump_object(bucket, path)

    print(response.data)
