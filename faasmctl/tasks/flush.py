from faasmctl.util.flush import flush_hosts, flush_workers
from invoke import task


@task()
def hosts(ctx):
    """
    Flush the list of registered and available hosts in the Faasm cluster
    """
    flush_hosts()


@task()
def workers(ctx):
    """
    Flush the state and wasm files cached in each worker
    """
    flush_workers()


@task()
def all(ctx):
    """
    Flush functions, state and shared files from all workers
    """
    # First flush the workers
    workers(ctx)

    # Last flush the available host list (note that after this call no other
    # flushing works, as the planner is unaware of any hosts in the cluster)
    hosts(ctx)
