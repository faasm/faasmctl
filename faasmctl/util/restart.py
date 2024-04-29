from faasmctl.util.backend import COMPOSE_BACKEND, K8S_BACKEND
from faasmctl.util.compose import restart_ctr_by_name
from faasmctl.util.config import (
    BACKEND_INI_STRING,
    get_faasm_ini_file,
    get_faasm_ini_value,
)
from faasmctl.util.k8s import restart_pod_by_name


def replica(names, ini_file=None):
    if not ini_file:
        ini_file = get_faasm_ini_file()

    backend = get_faasm_ini_value(ini_file, "Faasm", BACKEND_INI_STRING)
    if backend == COMPOSE_BACKEND:
        restart_ctr_by_name(ini_file, names)
    elif backend == K8S_BACKEND:
        restart_pod_by_name(ini_file, names)
    else:
        raise RuntimeError("Unrecognised backend: {}".format(backend))
