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


def get_faasm_upload_host_port(ini_file, in_docker=False):
    if in_docker:
        host = get_faasm_ini_value(ini_file, "Faasm", "upload_host_in_docker")
        port = get_faasm_ini_value(ini_file, "Faasm", "upload_port_in_docker")
    else:
        host = get_faasm_ini_value(ini_file, "Faasm", "upload_host")
        port = get_faasm_ini_value(ini_file, "Faasm", "upload_port")

    return host, port


def get_faasm_planner_host_port(ini_file, in_docker=False):
    if in_docker:
        host = get_faasm_ini_value(ini_file, "Faasm", "planner_host_in_docker")
        port = get_faasm_ini_value(ini_file, "Faasm", "planner_port_in_docker")
    else:
        host = get_faasm_ini_value(ini_file, "Faasm", "planner_host")
        port = get_faasm_ini_value(ini_file, "Faasm", "planner_port")

    return host, port
