from invoke import Collection

from . import flush

task_ns = Collection(
    flush,
)
