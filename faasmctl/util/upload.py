from faasmctl.util.config import (
    get_faasm_ini_file,
    get_faasm_upload_host_port,
)
from faasmctl.util.docker import in_docker
from requests import put
from subprocess import run


def upload_wasm(user, func, wasm_file, ini_file=None):
    """
    Upload a WASM file under the pair user/func
    """
    if not ini_file:
        ini_file = get_faasm_ini_file()

    # Work out if WASM file is a host path, or a path in a container
    wasm_in_ctr = wasm_file.rfind(":") != -1
    if wasm_in_ctr:
        tmp_ctr_name = "wasm-ctr"

        def stop_ctr():
            run(f"docker rm -f {tmp_ctr_name}", shell=True, capture_output=True)

        ctr_image = wasm_file[: wasm_file.rfind(":")]
        in_ctr_path = wasm_file[wasm_file.rfind(":") + 1 :]
        docker_cmd = "docker run -d --name {} {} bash".format(tmp_ctr_name, ctr_image)
        run(docker_cmd, shell=True, capture_output=True)

        tmp_wasm_file = "/tmp/wasm-ctr-func.wasm"
        docker_cmd = "docker cp {}:{} {}".format(
            tmp_ctr_name, in_ctr_path, tmp_wasm_file
        )
        try:
            run(docker_cmd, shell=True, capture_output=True)
        except Exception as e:
            print("Caught exception copying: {}".format(e))

        stop_ctr()

        wasm_file = tmp_wasm_file

    host, port = get_faasm_upload_host_port(ini_file, in_docker())
    url = "http://{}:{}/f/{}/{}".format(host, port, user, func)

    response = put(url, data=open(wasm_file, "rb"))
    if response.status_code != 200:
        raise RuntimeError(f"Error uploading WASM: {response.text}")


def upload_python(func, python_file, ini_file=None):
    """
    Upload a Python function to be executed with our WASM-compiled CPython
    """
    if not ini_file:
        ini_file = get_faasm_ini_file()

    host, port = get_faasm_upload_host_port(ini_file, in_docker())
    url = "http://{}:{}/p/{}/{}".format(host, port, "python", func)

    response = put(url, data=open(python_file, "rb"))
    print("Response ({}): {}".format(response.status_code, response.text))


def upload_file(host_path, faasm_path, ini_file=None):
    """
    Upload a file to Faasm's distributed filesystem

    This helper method uploads a file to Faasm's distributed filesystem for its
    usage from WASM functions running in Faasm. A file uploaded to <faasm_path>
    is visible from WASM functions at file path: faasm://<faasm_path>

    Parameters:
    - host_path (str): path in the host system to read the file from
    - faasm_path (str): path in the Faasm file system to store the file to
    - ini_file (str): path to the cluster's INI file
    """
    if not ini_file:
        ini_file = get_faasm_ini_file()

    host, port = get_faasm_upload_host_port(ini_file, in_docker())
    url = "http://{}:{}/file".format(host, port)

    response = put(
        url,
        data=open(host_path, "rb"),
        headers={"FilePath": faasm_path},
    )
    print("Response ({}): {}".format(response.status_code, response.text))
