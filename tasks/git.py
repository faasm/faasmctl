from invoke import task
from faasmctl.util.env import PROJ_ROOT
from faasmctl.util.version import get_version
from subprocess import run

VERSIONED_FILES = [
    "pyproject.toml",
    "README.md",
    "VERSION",
]


@task
def tag(ctx, force=False):
    """
    Creates git tag from the current tree
    """
    version = get_version()
    tag_name = "v{}".format(version)
    run(
        "git tag {} {}".format("--force" if force else "", tag_name),
        shell=True,
        check=True,
        cwd=PROJ_ROOT,
    )

    run(
        "git push {} origin {}".format("--force" if force else "", tag_name),
        shell=True,
        check=True,
        cwd=PROJ_ROOT,
    )


@task
def bump(ctx, patch=False, minor=False, major=False):
    """
    Bump the code version by --patch, --minor, or --major
    """
    old_ver = get_version()
    new_ver_parts = old_ver.split(".")

    if patch:
        idx = 2
    elif minor:
        idx = 1
    elif major:
        idx = 0
    else:
        raise RuntimeError("Must set one in: --[patch,minor,major]")

    new_ver_parts[idx] = str(int(new_ver_parts[idx]) + 1)
    new_ver = ".".join(new_ver_parts)

    for f in VERSIONED_FILES:
        sed_cmd = "sed -i 's/{}/{}/g' {}".format(old_ver, new_ver, f)
        run(sed_cmd, shell=True, check=True, cwd=PROJ_ROOT)
