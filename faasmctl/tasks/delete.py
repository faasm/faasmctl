from faasmctl.util.compose import delete_compose_cluster
from faasmctl.util.config import get_faasm_ini_file, get_faasm_ini_value
from invoke import task


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
    else:
        raise RuntimeError("Unsupported backend: {}".format(backend))
