from faasmctl.util.config import get_faasm_ini_value
from faasmctl.util.deploy import generate_ini_file
from faasmctl.util.random import generate_gid
from os import environ
from os.path import isfile, join
from subprocess import run
from time import sleep


def get_compose_env_vars(faasm_checkout, mount_source):
    env = {}
    if mount_source:
        env["FAASM_BUILD_DIR"] = join(faasm_checkout, "dev/faasm/build")
        env["FAASM_BUILD_MOUNT"] = "/build/faasm"
        env["FAASM_CODE_MOUNT"] = "/usr/local/code/faasm"
        env["FAASM_CONAN_MOUNT"] = "/root/.conan"
        env["FAASM_LOCAL_MOUNT"] = "/usr/local/faasm"
        env["PLANNER_BUILD_MOUNT"] = env["FAASM_BUILD_MOUNT"]
    else:
        # FIXME: by using `./dev` in non-mounted clusters we make it impossible
        # to cleanly remove them (as ./dev is root-owned), so we can't rm -rf
        # the directory
        env["FAASM_BUILD_DIR"] = join(faasm_checkout, "dev/faasm/build")
        env["FAASM_BUILD_MOUNT"] = "/host_dev/build"
        env["FAASM_CODE_MOUNT"] = "/host_dev/code"
        env["FAASM_CONAN_MOUNT"] = "/host_dev/conan"
        env["FAASM_LOCAL_MOUNT"] = "/host_dev/faasm-local"
        env["PLANNER_BUILD_MOUNT"] = "/build/faabric/static"

    # Get Faasm version
    with open(join(faasm_checkout, "VERSION"), "r") as fh:
        faasm_ver = fh.read()
        faasm_ver = faasm_ver.strip()

    # Whitelist env. variables that we recognise
    if "WASM_VM" in environ:
        wasm_vm = environ["WASM_VM"]
        if wasm_vm == "sgx-sim":
            worker_img = "faasm/worker-sgx-sim:{}".format(faasm_ver)
            env["WASM_VM"] = "sgx"
            env["FAASM_CLI_IMAGE"] = "faasm/cli-sgx-sim:{}".format(faasm_ver)
            env["FAASM_WORKER_IMAGE"] = worker_img
        elif wasm_vm == "sgx":
            env["WASM_VM"] = "sgx"
            env["FAASM_CLI_IMAGE"] = "faasm/cli-sgx:{}".format(faasm_ver)
            env["FAASM_WORKER_IMAGE"] = "faasm/worker-sgx:{}".format(faasm_ver)

    if "FAASM_CLI_IMAGE" in environ:
        env["FAASM_CLI_IMAGE"] = environ["FAASM_CLI_IMAGE"]

    return env


def deploy_compose_cluster(faasm_checkout, workers, mount_source, ini_file):
    """
    Deploy a docker compose cluster

    Parameters:
    - faasm_checkout (str): path to the Faasm's source code checkout
    - workers (int): number of workers to deploy
    - mount_source (bool): flag to indicate whether we mount code/binaries
    - ini_file (str): path to the ini_file to generate (if selected)
    """
    env = get_compose_env_vars(faasm_checkout, mount_source)

    # Generate random compose project name
    env["COMPOSE_PROJECT_NAME"] = "faasm-{}".format(generate_gid())

    # Deploy the compose cluster
    cmd = [
        "docker compose up -d",
        "--scale worker={}".format(workers),
        "worker",
    ]
    cmd = " ".join(cmd)
    run(cmd, shell=True, check=True, cwd=faasm_checkout, env=env)

    # Finally, generate the faasm.ini file to interact with the cluster
    generate_ini_file(
        "compose",
        out_file=ini_file,
        name=env["COMPOSE_PROJECT_NAME"],
        cwd=faasm_checkout,
        mount_source=mount_source,
    )


def delete_compose_cluster(ini_file):
    """
    Delete a cluster running on docker compose

    Parameters:
    - ini_file (str): path to the ini_file generated by the deploy command
    """
    working_dir = get_faasm_ini_value(ini_file, "Faasm", "working_dir")
    cluster_name = get_faasm_ini_value(ini_file, "Faasm", "cluster_name")
    compose_cmd = [
        "docker compose",
        "-p {}".format(cluster_name),
        "down",
    ]
    compose_cmd = " ".join(compose_cmd)
    run(compose_cmd, shell=True, check=True, cwd=working_dir)


def run_compose_cmd(ini_file, cmd):
    cluster_name = get_faasm_ini_value(ini_file, "Faasm", "cluster_name")
    work_dir = get_faasm_ini_value(ini_file, "Faasm", "working_dir")
    mount_source = get_faasm_ini_value(ini_file, "Faasm", "mount_source")
    mount_source = mount_source == "True"

    compose_cmd = [
        "docker compose",
        "-p {}".format(cluster_name),
        cmd,
    ]
    compose_cmd = " ".join(compose_cmd)
    run(
        compose_cmd,
        shell=True,
        check=True,
        cwd=work_dir,
        env=get_compose_env_vars(work_dir, mount_source),
    )


def wait_for_venv(ini_file, cli):
    """
    When executing a command in a CLI container, the first time we start it
    we may run into a race condition between:
    (1) up-ing, exec-ing, and inv-oking a task in the container, and
    (2) ./bin/create_venv.sh installing all python venv dependencies
    This is only a problem when mounting the sources: containers ship with a
    fully fledged `./venv`, but not code checkouts. Thus when mounting the
    source the host version overwrites the container's `./venv`
    """
    # FIXME: we only need to wait for the venv even if we don't mount the
    # source for the clients because we ALWAYS mount ./clients/cpp, and this
    # needs to be fixed
    mount_source = get_faasm_ini_value(ini_file, "Faasm", "mount_source")
    mount_source = mount_source == "True"
    work_dir = get_faasm_ini_value(ini_file, "Faasm", "working_dir")
    if mount_source or cli != "faasm-cli":
        # Work out the right venv path
        venv_path = work_dir
        if cli != "faasm-cli":
            venv_path = join(venv_path, "clients", cli)
        venv_path = join(venv_path, "venv", "faasm_venv.BUILT")

        # Loop until the file exists
        while True:
            if isfile(venv_path):
                break

            print(
                "Waiting for python virtual environment to be ready "
                "at {} ...".format(venv_path)
            )
            sleep(3)
