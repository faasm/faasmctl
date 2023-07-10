from faasmctl.util.config import get_faasm_ini_value
from subprocess import run


def delete_compose_cluster(ini_file):
    working_dir = get_faasm_ini_value(ini_file, "Faasm", "working_dir")
    cluster_name = get_faasm_ini_value(ini_file, "Faasm", "cluster_name")
    compose_cmd = [
        "docker compose",
        "-p {}".format(cluster_name),
        "down",
    ]
    compose_cmd = " ".join(compose_cmd)
    run(compose_cmd, shell=True, check=True, cwd=working_dir)
