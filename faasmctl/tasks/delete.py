from faasmctl.util.compose import delete_compose_cluster
from faasmctl.util.config import get_faasm_ini_file, get_faasm_ini_value
from faasmctl.util.k8s import delete_k8s_cluster
from invoke import task
from os import remove


@task(default=True)
def delete(ctx, ini_file=None):
    """
    Delete a running Faasm cluster

    Parameters:
    - ini_file (str): path to the cluster's INI file (FAASM_INI_FILE env. var
                      if not found)
    """
    if not ini_file:
        ini_file = get_faasm_ini_file()

    backend = get_faasm_ini_value(ini_file, "Faasm", "backend")
    if backend == "compose":
        delete_compose_cluster(ini_file)
    elif backend == "k8s":
        delete_k8s_cluster(ini_file)
    else:
        raise RuntimeError("Unsupported backend: {}".format(backend))

    remove(ini_file)
