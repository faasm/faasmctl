from faasmctl.util.compose import delete_compose_cluster
from faasmctl.util.config import get_faasm_ini_file, get_faasm_ini_value
from faasmctl.util.deploy import fetch_faasm_code, generate_ini_file
from faasmctl.util.random import generate_gid
from invoke import task
from os import environ
from os.path import join
from subprocess import run


@task
def compose(ctx, workers=2, dev=False, clean=False, ini_file=None):
    """
    Deploy a Faasm cluster on docker compose
    """
    # First, check-out the Faasm source if necessary
    if "FAASM_SOURCE_DIR" in environ:
        if clean:
            print("WARNING: using the --clean flag with a FAASM_SOURCE_DIR "
                  "env. variable is disabled, as local changes could be "
                  "erased!")
        faasm_checkout, faasm_ver = fetch_faasm_code(faasm_source=environ["FAASM_SOURCE_DIR"], force=False)
    else:
        if dev:
            print("WARNING: using the --dev flag to start a development "
                  "cluster is only supported if you set the FAASM_SOURCE_DIR"
                  " env. variable. For more information check the deployment"
                  " documentation on ./docs/deploy.md")
            dev = False
        faasm_checkout, faasm_ver = fetch_faasm_code(force=clean)

    compose_env = {}
    if dev:
        compose_env["FAASM_BUILD_DIR"] = join(faasm_checkout, "dev/faasm/build")
        compose_env["FAASM_BUILD_MOUNT"] = "/build/faasm"
        compose_env["FAASM_CODE_MOUNT"] = "/usr/local/code/faasm"
        compose_env["FAASM_CONAN_MOUNT"] = "/root/.conan"
        compose_env["FAASM_LOCAL_MOUNT"] = "/usr/local/faasm"
        compose_env["PLANNER_BUILD_MOUNT"] = compose_env["FAASM_BUILD_MOUNT"]

    # Whitelist env. variables that we recognise
    if "WASM_VM" in environ:
        wasm_vm = environ["WASM_VM"]
        if wasm_vm == "sgx-sim":
            compose_env["WASM_VM"] = "sgx"
            compose_env["FAASM_CLI_IMAGE"] = "faasm/cli-sgx-sim:{}".format(faasm_ver)
            compose_env["FAASM_WORKER_IMAGE"] = "faasm/worker-sgx-sim:{}".format(faasm_ver)
        elif wasm_vm == "sgx":
            compose_env["WASM_VM"] = "sgx"
            compose_env["FAASM_CLI_IMAGE"] = "faasm/cli-sgx:{}".format(faasm_ver)
            compose_env["FAASM_WORKER_IMAGE"] = "faasm/worker-sgx:{}".format(faasm_ver)

    # Generate random compose project name
    compose_env["COMPOSE_PROJECT_NAME"] = "faasm-{}".format(generate_gid())

    # Deploy the compose cluster
    cmd = [
        "docker compose up -d",
        "--scale worker={}".format(workers),
        "worker",
    ]
    cmd = " ".join(cmd)
    run(cmd, shell=True, check=True, cwd=faasm_checkout, env=compose_env)

    # Finally, generate the faasm.ini file to interact with the cluster
    generate_ini_file(
        "compose",
        out_file=ini_file,
        name=compose_env["COMPOSE_PROJECT_NAME"],
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
