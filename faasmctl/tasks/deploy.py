from faasmctl.util.compose import deploy_compose_cluster
from faasmctl.util.deploy import fetch_faasm_code
from invoke import task
from os.path import abspath


@task
def compose(ctx, workers=2, mount_source=None, clean=False, ini_file=None):
    """
    Deploy a Faasm cluster on docker compose
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
    else:
        # Otherwise, we will check out the code in a faasmctl-specific working
        # directoy
        mount_source = False
        faasm_checkout, faasm_ver = fetch_faasm_code(force=clean)

    deploy_compose_cluster(faasm_checkout, workers, mount_source, ini_file)
