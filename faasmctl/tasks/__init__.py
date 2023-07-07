from invoke import Collection

from . import flush
from . import invoke

task_ns = Collection(
    flush,
    invoke,
)
