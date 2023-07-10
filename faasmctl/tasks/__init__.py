from invoke import Collection

from . import deploy
from . import flush
from . import invoke
from . import upload

task_ns = Collection(
    deploy,
    flush,
    invoke,
    upload,
)
