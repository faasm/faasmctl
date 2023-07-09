from faasmctl.util.config import (
    get_faasm_ini_file,
    get_faasm_upload_host_port,
)
from requests import put


def upload_wasm(user, func, wasm_file, ini_file=None):
    if not ini_file:
        ini_file = get_faasm_ini_file()

    host, port = get_faasm_upload_host_port(ini_file)
    url = "http://{}:{}/f/{}/{}".format(host, port, user, func)

    response = put(url, data=open(wasm_file, "rb"))
    print("Response ({}): {}".format(response.status_code, response.text))
