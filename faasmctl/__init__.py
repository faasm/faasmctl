# flake8: noqa

# Before instantiating the program, make sure we have generated the
# necessary protobuf files (or lazily generate them)
from subprocess import run
from os.path import dirname, join, realpath

PROJ_ROOT = dirname(dirname(realpath(__file__)))
cmd = "{}".format(join(PROJ_ROOT, "bin", "gen_proto_files.py"))
run(cmd, shell=True, check=True, cwd=PROJ_ROOT)


from . import tasks
from . import util
