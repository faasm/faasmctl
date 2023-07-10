from os.path import dirname, realpath

# When building the project's wheel only the `faasmctl` is included. Thus all
# imports in `faasmctl` need to be relative to `faasmctl` itself (not the git
# source). We also define a DEV proj root, for dev. related tasks
PROJ_ROOT = dirname(dirname(realpath(__file__)))
DEV_PROJ_ROOT = dirname(dirname(dirname(realpath(__file__))))
