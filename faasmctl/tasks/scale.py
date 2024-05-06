from faasmctl.util.backend import COMPOSE_BACKEND
from faasmctl.util.compose import (
    get_container_ips_from_compose,
    get_container_names_from_compose,
    run_compose_cmd,
)
from faasmctl.util.config import (
    BACKEND_INI_STRING,
    get_faasm_ini_file,
    get_faasm_ini_value,
    update_faasm_ini_value,
)
from invoke import task


@task(default=True)
def scale(ctx, service, replicas, ini_file=None):
    """
    Scale a service to a number of replicas

    Parameters:
    - service (str): service to scale
    - replicas (int): number of replicas to scale to
    """
    if not ini_file:
        ini_file = get_faasm_ini_file()

    backend = get_faasm_ini_value(ini_file, "Faasm", BACKEND_INI_STRING)
    if backend != COMPOSE_BACKEND:
        raise RuntimeError(
            "Can only get a CLI shell for a cluster that is "
            "running on a '{}' backend".format(COMPOSE_BACKEND)
        )

    run_compose_cmd(ini_file, "scale {}={}".format(service, replicas))

    # Update the worker names and ips in the INI file
    faasm_checkout = get_faasm_ini_value(ini_file, "Faasm", "working_dir")
    cluster_name = get_faasm_ini_value(ini_file, "Faasm", "cluster_name")
    worker_names = "{}".format(
        ",".join(get_container_names_from_compose(faasm_checkout, cluster_name))
    )
    worker_ips = "{}".format(
        ",".join(get_container_ips_from_compose(faasm_checkout, cluster_name))
    )
    update_faasm_ini_value(ini_file, "Faasm", "worker_names", worker_names)
    update_faasm_ini_value(ini_file, "Faasm", "worker_ips", worker_ips)
