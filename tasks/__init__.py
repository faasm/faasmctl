from invoke import Collection

from . import format_code
from . import git

ns = Collection(
    format_code,
    git,
)
