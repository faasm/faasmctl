from faasmctl.util.config import (
    get_faasm_ini_file,
    get_faasm_upload_host_port,
)
from faasmctl.util.docker import in_docker
from requests import put


def upload_wasm(user, func, wasm_file, ini_file=None):
    """
    Upload a WASM file under the pair user/func
    """
    if not ini_file:
        ini_file = get_faasm_ini_file()

    host, port = get_faasm_upload_host_port(ini_file, in_docker())
    url = "http://{}:{}/f/{}/{}".format(host, port, user, func)

    response = put(url, data=open(wasm_file, "rb"))
    print("Response ({}): {}".format(response.status_code, response.text))


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
