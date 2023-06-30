from invoke import task


@task(default=True)
def all(ctx):
    """
    Flush functions, state and shared files from all workers
    """
    return 1
