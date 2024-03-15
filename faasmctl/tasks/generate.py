from invoke import task
from os.path import join
from subprocess import run
from faasmctl.util.env import PROJ_ROOT


@task
def proto(ctx):
    """
    (Re)generate the Python protobuf files necessary to interact with Faasm
    """
    gen_proto_bin = join(PROJ_ROOT, "bin", "gen_proto_files.py")
    gen_cmd = "python3 {} --clean".format(gen_proto_bin)
    run(gen_cmd, shell=True, check=True)
