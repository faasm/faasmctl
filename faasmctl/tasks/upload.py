from faasmctl.util.upload import upload_file, upload_wasm
from invoke import task


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
