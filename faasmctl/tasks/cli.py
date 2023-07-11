from faasmctl.util.backend import COMPOSE_BACKEND
from faasmctl.util.compose import run_compose_cmd
from faasmctl.util.config import (
    BACKEND_INI_STRING,
    get_faasm_ini_file,
    get_faasm_ini_value,
)
from invoke import task


def do_run_cmd(cli, cmd, ini_file):
    if not ini_file:
        ini_file = get_faasm_ini_file()

    backend = get_faasm_ini_value(ini_file, "Faasm", BACKEND_INI_STRING)
    if backend != COMPOSE_BACKEND:
        raise RuntimeError("Can only get a CLI shell for a cluster that is "
                           "running on a '{}' backend".format(COMPOSE_BACKEND))

    # First, start the container once to avoid recreating it multiple times
    up_cmd = "up -d --no-recreate {}".format(cli)
    run_compose_cmd(ini_file, up_cmd)

    # Second, actually run the requested command
    compose_cmd = [
        "exec",
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
    do_run_cmd("faasm", cmd, ini_file)


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
