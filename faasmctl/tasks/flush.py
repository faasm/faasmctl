from invoke import task

FAABRIC_MSG_TYPE_FLUSH = 3


@task(default=True)
def all(ctx):
    """
    Flush functions, state and shared files from all workers
    """
    host, port = get_invoke_host_port()
    msg = {
        "type": FAABRIC_MSG_TYPE_FLUSH,
    }

    url = "http://{}:{}".format(host, port)
    return 1
