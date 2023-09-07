from invoke import Collection

from . import cli
from . import delete
from . import deploy
from . import flush
from . import invoke
from . import logs
from . import monitor
from . import restart
from . import status
from . import upload

task_ns = Collection(
    cli,
    delete,
    deploy,
    flush,
    invoke,
    logs,
    monitor,
    restart,
    status,
    upload,
)
