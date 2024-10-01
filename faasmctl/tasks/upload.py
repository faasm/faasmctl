from faasmctl.util.upload import upload_file, upload_wasm
from invoke import task
from os.path import join
from subprocess import run


@task(default=True)
def wasm(ctx, user, func, wasm_file, ini_file=None):
    """
    Upload a WASM file under user/func (from --wasm-file)

    Arguments:
    - user (str): user to register the function with
    - func (str): name to register the function with
    - ini_file (str): optional path to the INI file
    """
    # Directly call the util function so that it uses the same code than the
    # API consumers (i.e. using faasmctl in a python script)
    upload_wasm(user, func, wasm_file, ini_file)


@task
def workflow(ctx, wflow, path, ini_file=None):
    """
    Upload all WASM files corresponding to a workflow (from --path)

    Path indicates a directory where each function in the workflow is in a
    different sub-directory, in a single WASM file. Uploading a workflow is
    equivalent to uplodaing a `user` in the traditional Faasm sense. Note that
    you may prefix the path with a container name, followed by a colon, and
    then the path, to copy the file from a path inside a container.
    """
    wasm_in_ctr = path.rfind(":") != -1
    if wasm_in_ctr:
        ctr_image = path[: path.rfind(":")]
        in_ctr_path = path[path.rfind(":") + 1 :]
        docker_cmd = "docker run --rm {} ls --format=commas {}".format(
            ctr_image, in_ctr_path
        )
        funcs = (
            run(docker_cmd, shell=True, capture_output=True)
            .stdout.decode("utf-8")
            .strip()
            .split(", ")
        )

        for func in funcs:
            upload_wasm(wflow, func, join(path, func, "function.wasm"))
    else:
        raise RuntimeError("Not implemented!")


@task()
def file(ctx, host_path, faasm_path, ini_file=None):
    """
    Upload a file to Faasm's distributed filesystem

    This task uploads a file to Faasm's distributed filesystem for its
    usage from WASM functions running in Faasm. A file uploaded to <faasm_path>
    is visible from WASM functions at file path: faasm://<faasm_path>

    Parameters:
    - host_path (str): path in the host system to read the file from
    - faasm_path (str): path in the Faasm file system to store the file to
    - ini_file (str): path to the cluster's INI file
    """
    # Directly call the util function so that it uses the same code than the
    # API consumers (i.e. using faasmctl in a python script)
    upload_file(host_path, faasm_path, ini_file)
