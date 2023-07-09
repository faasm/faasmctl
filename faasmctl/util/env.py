from os.path import dirname, join, realpath

PROJ_ROOT = dirname(dirname(dirname(realpath(__file__))))

FAASMCTL_DIR = join(PROJ_ROOT, "faasmctl")
UTIL_DIR = join(FAASMCTL_DIR, "util")
GEN_PROTO_DIR = join(UTIL_DIR, "gen_proto")
