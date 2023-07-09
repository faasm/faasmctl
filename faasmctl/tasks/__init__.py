from invoke import Collection

from . import flush
from . import invoke
from . import upload

task_ns = Collection(
    flush,
    invoke,
    upload,
)
