from faasmctl.util.config import get_faasm_ini_value, update_faasm_ini_value
from faasmctl.util.deploy import generate_ini_file
from faasmctl.util.docker import get_docker_tag
from faasmctl.util.faasm import FAASM_DOCKER_REGISTRY
from faasmctl.util.network import get_next_bindable_port
from faasmctl.util.random import generate_gid
from json import loads as json_loads
from os import environ, makedirs
from os.path import exists, isfile, join
from shutil import rmtree
from subprocess import run
from time import sleep

DEFAULT_FAASM_CAPTURE_STDOUT = "off"
DEFAULT_FAASM_OVERRIDE_CPU_COUNT = "8"


def get_compose_env_vars(faasm_checkout, mount_source, ini_file=None):
    """
    Get the env. variables to call `docker compose` with

    Faasm's docker compose file requires a number of envrionment variables to
    be set. Starting different services requires different env. variables, and
    the process is very error prone, so we automate it here.

    Arguments:
    - faasm_checkout (str): path to Faasm's source tree
    - mount_source (bool): whether we are mounting the source and binaries
    - ini_file (str): inidicate wether an ini_file has already been populated

    Returns:
    - A dictionary with the necessary env. variables
    """
    env = {}
    env["FAASM_DEPLOYMENT_TYPE"] = "compose"

    if mount_source:
        env["FAASM_BUILD_DIR"] = join(faasm_checkout, "dev/faasm/build")
        env["CONAN_CACHE_MOUNT_SOURCE"] = join(faasm_checkout, "dev/faasm/conan")
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
        env["CONAN_CACHE_MOUNT_SOURCE"] = join(faasm_checkout, "dev/faasm/conan")
        env["FAASM_BUILD_MOUNT"] = "/host_dev/build"
        env["FAASM_CODE_MOUNT"] = "/host_dev/code"
        env["FAASM_CONAN_MOUNT"] = "/host_dev/conan"
        env["FAASM_LOCAL_MOUNT"] = "/host_dev/faasm-local"
        env["PLANNER_BUILD_MOUNT"] = "/build/faabric/static"

    # Set network env. variables. Depending on wether the cluster has already
    # been initialised or not, we need to work out the next bindable port or
    # not
    env["PLANNER_DOCKER_PORT"] = "8080"
    if ini_file:
        env["PLANNER_HOST_PORT"] = get_faasm_ini_value(
            ini_file, "Faasm", "planner_port"
        )
    else:
        env["PLANNER_HOST_PORT"] = str(
            get_next_bindable_port(int(env["PLANNER_DOCKER_PORT"]))
        )
    env["MINIO_DOCKER_PORT"] = "9000"
    # The minio port we only need to set once at the begining
    if ini_file:
        env["MINIO_HOST_PORT"] = get_faasm_ini_value(ini_file, "Faasm", "minio_port")
    else:
        env["MINIO_HOST_PORT"] = str(
            get_next_bindable_port(int(env["MINIO_DOCKER_PORT"]))
        )
    env["UPLOAD_DOCKER_PORT"] = "8002"
    if ini_file:
        env["UPLOAD_HOST_PORT"] = get_faasm_ini_value(ini_file, "Faasm", "upload_port")
    else:
        env["UPLOAD_HOST_PORT"] = str(
            get_next_bindable_port(int(env["UPLOAD_DOCKER_PORT"]))
        )

    # Get Faasm version
    with open(join(faasm_checkout, "VERSION"), "r") as fh:
        faasm_ver = fh.read()
        faasm_ver = faasm_ver.strip()

    # Whitelist env. variables that we recognise
    if "FAASM_DEPLOYMENT_TYPE" in environ:
        env["FAASM_DEPLOYMENT_TYPE"] = environ["FAASM_DEPLOYMENT_TYPE"]

    # Work-out the WASM VM and the cli image based on the available env.
    # variables (and possible overwrites)
    if "FAASM_WASM_VM" in environ:
        wasm_vm = environ["FAASM_WASM_VM"]
        if wasm_vm == "sgx-sim":
            worker_img = "{}/worker-sgx-sim:{}".format(FAASM_DOCKER_REGISTRY, faasm_ver)
            env["FAASM_WASM_VM"] = "sgx"
            env["FAASM_CLI_IMAGE"] = "{}/cli-sgx-sim:{}".format(
                FAASM_DOCKER_REGISTRY, faasm_ver
            )
            env["FAASM_WORKER_IMAGE"] = worker_img
        elif wasm_vm == "sgx":
            env["FAASM_WASM_VM"] = "sgx"
            env["FAASM_CLI_IMAGE"] = "{}/cli-sgx:{}".format(
                FAASM_DOCKER_REGISTRY, faasm_ver
            )
            env["FAASM_WORKER_IMAGE"] = "{}/worker-sgx:{}".format(
                FAASM_DOCKER_REGISTRY, faasm_ver
            )
        else:
            env["FAASM_WASM_VM"] = wasm_vm

        # Work out the CLI image
        if "FAASM_CLI_IMAGE" in environ and "sgx" not in wasm_vm:
            env["FAASM_CLI_IMAGE"] = environ["FAASM_CLI_IMAGE"]

        if "FAASM_SGX_CLI_IMAGE" in environ and "sgx" in wasm_vm:
            env["FAASM_CLI_IMAGE"] = environ["FAASM_SGX_CLI_IMAGE"]
    else:
        # Even if no WASM_VM is set, pick the provided CLI image
        if "FAASM_CLI_IMAGE" in environ:
            env["FAASM_CLI_IMAGE"] = environ["FAASM_CLI_IMAGE"]

    env["FAASM_OVERRIDE_CPU_COUNT"] = DEFAULT_FAASM_OVERRIDE_CPU_COUNT
    if "FAASM_OVERRIDE_CPU_COUNT" in environ:
        env["FAASM_OVERRIDE_CPU_COUNT"] = environ["FAASM_OVERRIDE_CPU_COUNT"]

    env["FAASM_CAPTURE_STDOUT"] = DEFAULT_FAASM_CAPTURE_STDOUT
    if "FAASM_CAPTURE_STDOUT" in environ:
        env["FAASM_CAPTURE_STDOUT"] = environ["FAASM_CAPTURE_STDOUT"]

    if "CONAN_CACHE_MOUNT_SOURCE" in environ:
        env["CONAN_CACHE_MOUNT_SOURCE"] = environ["CONAN_CACHE_MOUNT_SOURCE"]

    return env


def deploy_compose_cluster(faasm_checkout, workers, mount_source, ini_file):
    """
    Deploy a docker compose cluster

    Parameters:
    - faasm_checkout (str): path to the Faasm's source code checkout
    - workers (int): number of workers to deploy
    - mount_source (bool): flag to indicate whether we mount code/binaries
    - ini_file (str): path to the ini_file to generate (if selected)

    Returns:
    - (str): path to the generated ini_file
    """
    env = get_compose_env_vars(faasm_checkout, mount_source)

    # Generate random compose project name
    env["COMPOSE_PROJECT_NAME"] = "faasm-{}".format(generate_gid())

    # In a compose cluster with SGX in HW mode, we need to manually set-up
    # the AESMD volume and socket for remote attestation (in a k8s deployment
    # on AKS, this is done automatically for us)
    is_sgx_deployment = "FAASM_WASM_VM" in env and env["FAASM_WASM_VM"] == "sgx"
    is_hw_mode = (
        "FAASM_WORKER_IMAGE" in env
        and "worker-sgx-sim" not in env["FAASM_WORKER_IMAGE"]
    )
    must_start_sgx_aesmd = is_sgx_deployment and is_hw_mode

    if must_start_sgx_aesmd:
        docker_cmd = [
            "docker",
            "volume create",
            "--driver local",
            "--opt type=tmpfs",
            "--opt device=tmpfs",
            "--opt o=rw",
            "aesmd-socket",
        ]
        docker_cmd = " ".join(docker_cmd)
        run(docker_cmd, shell=True, check=True)

        env["SGX_DEVICE_MOUNT_DIR"] = "/dev/sgx"

    # Deploy the compose cluster (0 workers <=> cli-only cluster)
    cmd = [
        "docker compose up -d",
        "--scale worker={}".format(workers) if int(workers) > 0 else "",
        "aesmd" if must_start_sgx_aesmd else "",
        "worker" if int(workers) > 0 else "faasm-cli",
    ]
    cmd = " ".join(cmd)
    run(cmd, shell=True, check=True, cwd=faasm_checkout, env=env)

    # Finally, generate the faasm.ini file to interact with the cluster
    return generate_ini_file(
        "compose",
        out_file=ini_file,
        name=env["COMPOSE_PROJECT_NAME"],
        cwd=faasm_checkout,
        mount_source=mount_source,
        planner_host_port=env["PLANNER_HOST_PORT"],
        planner_docker_port=env["PLANNER_DOCKER_PORT"],
        minio_host_port=env["MINIO_HOST_PORT"],
        minio_docker_port=env["MINIO_DOCKER_PORT"],
        upload_host_port=env["UPLOAD_HOST_PORT"],
        upload_docker_port=env["UPLOAD_DOCKER_PORT"],
        worker_names=get_container_names_from_compose(
            faasm_checkout, env["COMPOSE_PROJECT_NAME"]
        ),
        worker_ips=get_container_ips_from_compose(
            faasm_checkout, env["COMPOSE_PROJECT_NAME"]
        ),
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


def run_compose_cmd(ini_file, cmd, capture_out=False):
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

    compose_env = get_compose_env_vars(work_dir, mount_source, ini_file)
    if capture_out:
        return (
            run(
                compose_cmd,
                shell=True,
                capture_output=True,
                cwd=work_dir,
                env=compose_env,
            )
            .stdout.decode("utf-8")
            .strip()
        )

    run(
        compose_cmd,
        shell=True,
        check=True,
        cwd=work_dir,
        env=compose_env,
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


# TODO: make this method callable for when things go sideways
def populate_host_sysroot(faasm_checkout, clean=False):
    """
    Populate the host's sysroot under `./dev/faasm-local` to be shared by
    all containers in a compose cluster with mounted-in binaries and code
    """
    dirs_to_copy = {
        "FAASM_CLI_IMAGE": ["runtime_root"],
        "CPP_CLI_IMAGE": ["llvm-sysroot", "native", "toolchain"],
        "PYTHON_CLI_IMAGE": [
            "python3.8",
            # We are specific about which bits to copy from the llvm-sysroot
            # for the python functions. Overwriting all the sysroot with the
            # one tracked in the CPython image is unneccessary
            join("llvm-sysroot", "lib", "wasm32-wasi-threads", "libpython3.8.a"),
            join("llvm-sysroot", "include", "wasm32-wasi-threads", "python3.8"),
        ],
    }

    # TODO: should we make this variable configurable?
    host_sysroot_path = join(faasm_checkout, "dev", "faasm-local")

    if clean:
        rmtree(host_sysroot_path)

    if exists(host_sysroot_path):
        return

    makedirs(host_sysroot_path)

    def copy_from_ctr_to_host(image_tag, dir_path):
        """
        Helper method to copy data from the sysroot inside a docker container
        into the host's mounted (and shared) sysroot
        """
        ctr_path = join("/usr/local/faasm", dir_path)
        host_path = join(host_sysroot_path, dir_path)

        # Start a temporary ctr to copy from (capture output to silence
        # verbose logging)
        tmp_ctr = "cp_sysroot_ctr"
        run_cmd = "docker run -d --name {} {}".format(tmp_ctr, image_tag)
        run(run_cmd, shell=True, capture_output=True)

        # Do the actual copy
        try:
            print("Populating {} from {}:{}".format(host_path, image_tag, ctr_path))
            cp_cmd = "docker cp {}:{} {}".format(tmp_ctr, ctr_path, host_path)
            run(cp_cmd, shell=True, check=True)
        except Exception as e:
            print("Caught exception copying: {}".format(e))

        # Delete the tmp container unconditionally (capture output to silence
        # verbose logging)
        del_cmd = "docker rm -f {}".format(tmp_ctr)
        run(del_cmd, shell=True, capture_output=True)

    for image in dirs_to_copy:
        image_tag = get_docker_tag(faasm_checkout, image)

        for dir_path in dirs_to_copy[image]:
            copy_from_ctr_to_host(image_tag, dir_path)


def get_container_names_from_compose(faasm_checkout, cluster_name):
    # Unfortunately, we can't use run_compose_cmd here yet because we need the
    # ini_file for that, but we need this method to generate it
    compose_cmd = [
        "docker compose",
        "-p {}".format(cluster_name),
        "ps --format json",
    ]
    compose_cmd = " ".join(compose_cmd)

    json_str_array = (
        run(compose_cmd, shell=True, capture_output=True, cwd=faasm_checkout)
        .stdout.decode("utf-8")
        .strip()
        .split("\n")
    )

    json_array = [json_loads(json_str) for json_str in json_str_array]

    return [c["Name"] for c in json_array if c["Service"] == "worker"]


def get_container_ips_from_compose(faasm_checkout, cluster_name):
    container_ips = []
    container_names = get_container_names_from_compose(faasm_checkout, cluster_name)
    for c in container_names:
        ip_cmd = [
            "docker inspect -f",
            "'{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}'",
            c,
        ]
        ip_cmd = " ".join(ip_cmd)
        c_ip = (
            run(
                ip_cmd,
                shell=True,
                check=True,
                capture_output=True,
            )
            .stdout.decode("utf-8")
            .strip()
        )
        container_ips.append(c_ip)
    return container_ips


def restart_ctr_by_name(ini_file, ctr_names):
    all_ctr_names = get_faasm_ini_value(ini_file, "Faasm", "worker_names").split(",")

    if not all([ctr_name in all_ctr_names for ctr_name in ctr_names]):
        print(
            "Requested to restart a ctr list "
            "({}) not a subset of the worker list: {}".format(ctr_names, all_ctr_names)
        )
        raise RuntimeError("Unrecognised container name!")

    docker_cmd = "docker restart {}".format(" ".join(ctr_names))
    out = run(docker_cmd, shell=True, capture_output=True)
    assert out.returncode == 0, "Error restarting docker container: {}".format(
        out.stderr
    )

    # Update the container names and ips
    faasm_checkout = get_faasm_ini_value(ini_file, "Faasm", "working_dir")
    cluster_name = get_faasm_ini_value(ini_file, "Faasm", "cluster_name")

    # Ge the names and the ips directly from docker as the ones in the INI
    # file are now stale after the restart
    new_ctr_names = get_container_names_from_compose(faasm_checkout, cluster_name)
    new_ctr_ips = get_container_ips_from_compose(faasm_checkout, cluster_name)

    update_faasm_ini_value(ini_file, "Faasm", "worker_names", ",".join(new_ctr_names))
    update_faasm_ini_value(ini_file, "Faasm", "worker_ips", ",".join(new_ctr_ips))
