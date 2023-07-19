from faasmctl.util.compose import run_compose_cmd, wait_for_venv
from faasmctl.util.config import (
    BACKEND_INI_STRING,
    get_faasm_ini_file,
    get_faasm_ini_value,
)
from faasmctl.util.docker import get_docker_tag
from invoke import task
from os.path import abspath
from subprocess import run


def do_run_cmd(cli, cmd, ini_file):
    if not ini_file:
        ini_file = get_faasm_ini_file()

    backend = get_faasm_ini_value(ini_file, "Faasm", BACKEND_INI_STRING)
    if backend == "compose":
        # To run a command in a `compose` backend, we fist start the CLI
        # container in dettached mode (if it does not exist yet) and then we
        # exec into it, copying the ini file
        up_cmd = "up -d --no-recreate {}".format(cli)
        run_compose_cmd(ini_file, up_cmd)

        # Second, copy the the ini file inside the container
        ini_file = abspath(ini_file)
        ini_file_ctr_path = "/tmp/faasm.ini"
        cp_cmd = "cp {} {}:{}".format(ini_file, cli, ini_file_ctr_path)
        run_compose_cmd(ini_file, cp_cmd)

        # Third, wait for the virtual environment to be ready if we need to. We
        # only need to wait for the virtual environment if we are either
        # mounting the source, or using one of the clients
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

    elif backend == "k8s":
        # Using a CLI container with a cluster that runs on a `k8s` backend is
        # only supported to upload functions from the CPP or Python container.
        # As such we: (i) disable cli.faasm calls on a `k8s` backend, and (ii)
        # use a standalone container to execute the command that we remove
        # immediately after (without mounting any files)
        ini_file_ctr_path = "/tmp/faasm.ini"
        work_dir = get_faasm_ini_value(ini_file, "Faasm", "working_dir")

        if cli == "cpp":
            image_tag = get_docker_tag(work_dir, "CPP_CLI_IMAGE")
        elif cli == "python":
            image_tag = get_docker_tag(work_dir, "PYTHON_CLI_IMAGE")
        else:
            raise RuntimeError("Can't call cli.faasm on a `k8s` cluster!")

        docker_cmd = [
            "docker run --rm",
            "-v {}:{}".format(ini_file, ini_file_ctr_path),
            "-e FAASM_INI_FILE={}".format(ini_file_ctr_path),
            "-it" if not cmd else "",
            image_tag,
            "bash" if not cmd else cmd,
        ]
        docker_cmd = " ".join(docker_cmd)

        run(docker_cmd, shell=True)

    else:
        raise RuntimeError("Unrecognised backend: {}".format(backend))


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
