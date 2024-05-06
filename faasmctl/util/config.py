from configparser import ConfigParser
from os import environ
from os.path import exists

BACKEND_INI_STRING = "backend"


def get_faasm_ini_file():
    """
    Try to read faasm's ini file from the environment, fail otherwise
    """
    if "FAASM_INI_FILE" not in environ:
        raise RuntimeError("No FAASM_INI_FILE env. variable detected!")

    return environ["FAASM_INI_FILE"]


def get_faasm_ini_value(ini_file, section, key):
    if not exists(ini_file):
        raise RuntimeError("Did not find faasm config at: {}".format(ini_file))

    config = ConfigParser()
    config.read(ini_file)
    return config[section].get(key, "")


def update_faasm_ini_value(ini_file, section, key, new_value):
    if not exists(ini_file):
        raise RuntimeError("Did not find faasm config at: {}".format(ini_file))

    config = ConfigParser()
    config.read(ini_file)
    config[section][key] = new_value

    with open(ini_file, "w") as fh:
        config.write(fh)


def get_faasm_upload_host_port(ini_file, in_docker=False):
    backend = get_faasm_ini_value(ini_file, "Faasm", "backend")
    if backend == "compose" and in_docker:
        host = get_faasm_ini_value(ini_file, "Faasm", "upload_host_in_docker")
        port = get_faasm_ini_value(ini_file, "Faasm", "upload_port_in_docker")
    else:
        host = get_faasm_ini_value(ini_file, "Faasm", "upload_host")
        port = get_faasm_ini_value(ini_file, "Faasm", "upload_port")

    return host, port


def get_faasm_planner_host_port(ini_file, in_docker=False):
    backend = get_faasm_ini_value(ini_file, "Faasm", "backend")
    if backend == "compose" and in_docker:
        host = get_faasm_ini_value(ini_file, "Faasm", "planner_host_in_docker")
        port = get_faasm_ini_value(ini_file, "Faasm", "planner_port_in_docker")
    else:
        host = get_faasm_ini_value(ini_file, "Faasm", "planner_host")
        port = get_faasm_ini_value(ini_file, "Faasm", "planner_port")

    return host, port


def get_faasm_worker_names(ini_file=None):
    if not ini_file:
        ini_file = get_faasm_ini_file()

    names = get_faasm_ini_value(ini_file, "Faasm", "worker_names")
    names = [p.strip() for p in names.split(",") if p.strip()]

    return names


def get_faasm_worker_ips(ini_file=None):
    if not ini_file:
        ini_file = get_faasm_ini_file()

    ips = get_faasm_ini_value(ini_file, "Faasm", "worker_ips")
    ips = [p.strip() for p in ips.split(",") if p.strip()]

    return ips
