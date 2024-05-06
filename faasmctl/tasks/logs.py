from faasmctl.util.backend import COMPOSE_BACKEND, K8S_BACKEND
from faasmctl.util.compose import run_compose_cmd
from faasmctl.util.config import (
    BACKEND_INI_STRING,
    get_faasm_ini_file,
    get_faasm_ini_value,
)
from faasmctl.util.k8s import run_k8s_cmd
from invoke import task


def get_compose_logs(s, follow, ini_file, last_restart):
    compose_cmd = [
        "logs",
        "--since {}".format(last_restart),
        "-f" if follow else "",
        "{}".format(" ".join(s)),
    ]
    compose_cmd = " ".join(compose_cmd)
    run_compose_cmd(ini_file, compose_cmd)


def get_k8s_logs(s, follow, ini_file, last_restart):
    if len(s) > 1:
        raise RuntimeError(
            "Getting the logs for a K8s service only works with one service at a time!"
        )

    service_to_k8s_str = {
        "planner": "pod/planner",
        "worker": "-l run=faasm-worker",
        "upload": "pod/upload",
    }

    service = s[0]
    if service not in service_to_k8s_str:
        raise RuntimeError(
            "Unrecognised service name: {} (must be one in: {})".format(
                service, service_to_k8s_str.keys()
            )
        )

    k8s_cmd = [
        "logs",
        "-f" if follow else "",
        service_to_k8s_str[service],
        "--tail=-1",
    ]
    k8s_cmd = " ".join(k8s_cmd)
    k8s_config = get_faasm_ini_value(ini_file, "Faasm", "k8s_config")
    run_k8s_cmd(k8s_config, "faasm", k8s_cmd)


@task(default=True, iterable=["s"])
def logs(ctx, s, follow=False, ini_file=None):
    """
    Get the logs of a running service in the cluster

    Parameters:
    - s (str, repeateble): service to get the logs from
    - ini_file (str): path to the cluster's INI file
    """
    if not ini_file:
        ini_file = get_faasm_ini_file()

    backend = get_faasm_ini_value(ini_file, "Faasm", BACKEND_INI_STRING)
    last_restart = get_faasm_ini_value(ini_file, "Faasm", "last_restart")
    if backend == COMPOSE_BACKEND:
        get_compose_logs(s, follow, ini_file, last_restart)
    elif backend == K8S_BACKEND:
        get_k8s_logs(s, follow, ini_file, last_restart)
    else:
        raise RuntimeError("Unrecognised backend: {}".format(backend))
