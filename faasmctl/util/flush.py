from faasmctl.util.config import (
    get_faasm_ini_file,
    get_faasm_planner_host_port,
)
from faasmctl.util.planner import prepare_planner_msg
from requests import post


def do_flush(msg, ini_file):
    if not ini_file:
        ini_file = get_faasm_ini_file()

    host, port = get_faasm_planner_host_port(ini_file)
    url = "http://{}:{}".format(host, port)

    response = post(url, data=msg, timeout=None)

    if response.status_code != 200:
        print(
            "POST request to do flush failed (code: {}): {}".format(
                response.status_code, response.text
            )
        )
        raise RuntimeError("POST request to flush failed!")

    print("Response ({}): {}".format(response.status_code, response.text))


def flush_hosts(ini_file=None):
    msg = prepare_planner_msg("FLUSH_HOSTS")
    do_flush(msg, ini_file)


def flush_workers(ini_file=None):
    msg = prepare_planner_msg("FLUSH_EXECUTORS")
    do_flush(msg, ini_file)
