from faasmctl.util.backend import COMPOSE_BACKEND
from faasmctl.util.compose import run_compose_cmd, wait_for_venv
from faasmctl.util.config import (
    BACKEND_INI_STRING,
    get_faasm_ini_file,
    get_faasm_ini_value,
)
from invoke import task
from os.path import abspath


def do_run_cmd(cli, cmd, ini_file):
    if not ini_file:
        ini_file = get_faasm_ini_file()

    backend = get_faasm_ini_value(ini_file, "Faasm", BACKEND_INI_STRING)
    if backend != COMPOSE_BACKEND:
        raise RuntimeError(
            "Can only get a CLI shell for a cluster that is "
            "running on a '{}' backend".format(COMPOSE_BACKEND)
        )

    # First, start the container once to avoid recreating it multiple times
    up_cmd = "up -d --no-recreate {}".format(cli)
    run_compose_cmd(ini_file, up_cmd)

    # Second, copy the the ini file inside the container
    ini_file = abspath(ini_file)
    ini_file_ctr_path = "/tmp/faasm.ini"
    cp_cmd = "cp {} {}:{}".format(ini_file, cli, ini_file_ctr_path)
    run_compose_cmd(ini_file, cp_cmd)

    # Third, wait for the virtual environment to be ready if we need to. We
    # only need to wait for the virtual environment if we are either mounting
    # the source, or using one of the clients
    wait_for_venv(ini_file, cli)

    # Lastly, actually run the requested command
    compose_cmd = [
        "exec",
        "-e FAASM_INI_FILE={}".format(ini_file_ctr_path),
        "-it" if not cmd else "",
        cli,
        "bash" if not cmd else cmd,
    ]
    compose_cmd = " ".join(compose_cmd)
    run_compose_cmd(ini_file, compose_cmd)


@task
def faasm(ctx, cmd=None, ini_file=None):
    """
    Run a command in the Faasm CLI container

    By default, if --cmd is set to None, we will get a shell into the
    container. If the --cmd argument is set, we execute the cmd string

    Parameters:
    - cmd (str): command to run in the CLI container
    - ini_file (str): path to the cluster's INI file
    """
    do_run_cmd("faasm-cli", cmd, ini_file)


@task
def cpp(ctx, cmd=None, ini_file=None):
    """
    Run a command in the CPP CLI container

    By default, if --cmd is set to None, we will get a shell into the
    container. If the --cmd argument is set, we execute the cmd string

    Parameters:
    - cmd (str): command to run in the CLI container
    - ini_file (str): path to the cluster's INI file
    """
    do_run_cmd("cpp", cmd, ini_file)


@task
def python(ctx, cmd=None, ini_file=None):
    """
    Run a command in the Python CLI container

    By default, if --cmd is set to None, we will get a shell into the
    container. If the --cmd argument is set, we execute the cmd string

    Parameters:
    - cmd (str): command to run in the CLI container
    - ini_file (str): path to the cluster's INI file
    """
    do_run_cmd("python", cmd, ini_file)
