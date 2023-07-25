from faasmctl.util.compose import (
    deploy_compose_cluster,
    populate_host_sysroot,
    run_compose_cmd,
)
from faasmctl.util.deploy import fetch_faasm_code
from faasmctl.util.k8s import DEFAULT_KUBECONFIG_PATH, deploy_k8s_cluster
from invoke import task
from os import environ
from os.path import abspath


@task
def compose(ctx, workers=2, mount_source=None, clean=False, ini_file=None):
    """
    Deploy a Faasm cluster on docker compose

    Parameters:
    - workers (int): number of workers to deploy
    - mount_source (str): path to the Faasm's source code checkout
    - clean (bool): flag to indicate whether we clean cached checkouts
    - ini_file (str): path to the ini_file to generate (if selected)

    Returns:
    - (str): path to the generated ini_file
    """
    # First, check-out the Faasm source if necessary
    if mount_source:
        mount_source = abspath(mount_source)
        if clean:
            print(
                "WARNING: using the --clean flag with --mount_source "
                "env. variable is disabled, as local changes could be "
                "erased!"
            )
        faasm_checkout, faasm_ver = fetch_faasm_code(
            faasm_source=mount_source, force=False
        )
        mount_source = True

        # If mounting the source code, we need to populate the host's
        # sysroot to mount it into the containers
        populate_host_sysroot(faasm_checkout)
    else:
        # Otherwise, we will check out the code in a faasmctl-specific working
        # directoy
        mount_source = False
        faasm_checkout, faasm_ver = fetch_faasm_code(force=clean)

    return deploy_compose_cluster(faasm_checkout, workers, mount_source, ini_file)


@task
def dist_tests(ctx, mount_source=None, ini_file=None):
    """
    Deploy a development Faasm cluster to run distributed tests

    Parameters:
    - mount_source (str): path to the Faasm's source code checkout
    - ini_file (str): output path for the generated ini_file (def: faasm.ini)
    """
    if not mount_source:
        raise RuntimeError(
            "When deploying a dist-tests cluster, you need to"
            " specify the --mount-source"
        )

    # First, deploy the compose cluster with 0 workers (this generates the
    # right ini file, and picks up the correct env. variables)
    out_ini_file = compose(
        ctx, workers=0, mount_source=mount_source, clean=False, ini_file=ini_file
    )

    # Second, start the dist-test-server
    run_compose_cmd(out_ini_file, "up -d dist-test-server")


@task
def k8s(ctx, workers=2, context=None, ini_file=None):
    """
    Deploy a Faasm cluster on k8s

    Parameters:
    - workers (int): number of workers to deploy
    - context (str): path to the k8s config to use (defaults to ~/.kube/config)
    - ini_file (str): path to the ini_file to generate (if selected)

    Returns:
    - (str): path to the generated ini_file
    """
    # First, check-out the Faasm source if necessary (we need it for the k8s
    # deployment files, eventually we could publish them as helm charts)
    faasm_checkout, faasm_ver = fetch_faasm_code()

    if context:
        context = abspath(context)
    elif "KUBECONFIG" in environ:
        context = abspath(environ["KUBECONFIG"])
    else:
        context = DEFAULT_KUBECONFIG_PATH

    return deploy_k8s_cluster(context, faasm_checkout, workers, ini_file)
