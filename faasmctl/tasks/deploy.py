from faasmctl.util.compose import delete_compose_cluster
from faasmctl.util.config import get_faasm_ini_file, get_faasm_ini_value
from faasmctl.util.deploy import fetch_faasm_code, generate_ini_file
from faasmctl.util.random import generate_gid
from invoke import task
from os import environ
from os.path import join
from subprocess import run


@task
def compose(ctx, workers=2, mount_source=None, clean=False, ini_file=None):
    """
    Deploy a Faasm cluster on docker compose
    """
    # First, check-out the Faasm source if necessary
    if mount_source:
        if clean:
            print(
                "WARNING: using the --clean flag with --mount_source "
                "env. variable is disabled, as local changes could be "
                "erased!"
            )
        faasm_checkout, faasm_ver = fetch_faasm_code(
            faasm_source=mount_source, force=False
        )
    else:
        # Otherwise, we will check out the code in a faasmctl-specific working
        # directoy
        faasm_checkout, faasm_ver = fetch_faasm_code(force=clean)

    env = {}
    if mount_source:
        env["FAASM_BUILD_DIR"] = join(faasm_checkout, "dev/faasm/build")
        env["FAASM_BUILD_MOUNT"] = "/build/faasm"
        env["FAASM_CODE_MOUNT"] = "/usr/local/code/faasm"
        env["FAASM_CONAN_MOUNT"] = "/root/.conan"
        env["FAASM_LOCAL_MOUNT"] = "/usr/local/faasm"
        env["PLANNER_BUILD_MOUNT"] = env["FAASM_BUILD_MOUNT"]

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
    )


@task
def delete(ctx, ini_file=None):
    """
    Delete a running Faasm cluster by passing the path to the --ini-file
    """
    if not ini_file:
        ini_file = get_faasm_ini_file()

    backend = get_faasm_ini_value(ini_file, "Faasm", "backend")
    if backend == "compose":
        delete_compose_cluster(ini_file)
    else:
        raise RuntimeError("Unsupported backend: {}".format(backend))
