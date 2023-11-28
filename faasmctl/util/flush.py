from faasmctl.util.config import (
    get_faasm_ini_file,
    get_faasm_planner_host_port,
)
from faasmctl.util.docker import in_docker
from faasmctl.util.planner import prepare_planner_msg
from requests import post


def do_flush(msg, ini_file, quiet=True):
    if not ini_file:
        ini_file = get_faasm_ini_file()

    host, port = get_faasm_planner_host_port(ini_file, in_docker())
    url = "http://{}:{}".format(host, port)

    response = post(url, data=msg, timeout=None)

    if response.status_code != 200:
        print(
            "POST request to do flush failed (code: {}): {}".format(
                response.status_code, response.text
            )
        )
        raise RuntimeError("POST request to flush failed!")

    if not quiet:
        print("Response ({}): {}".format(response.status_code, response.text))


def flush_hosts(ini_file=None):
    msg = prepare_planner_msg("FLUSH_AVAILABLE_HOSTS")
    do_flush(msg, ini_file)


def flush_workers(ini_file=None):
    msg = prepare_planner_msg("FLUSH_EXECUTORS")
    do_flush(msg, ini_file)
