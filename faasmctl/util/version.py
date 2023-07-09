from faasmctl.util.env import PROJ_ROOT
from os.path import join


def read_version_from_file(filename):
    with open(filename, "r") as fh:
        version = fh.read()
        version = version.strip()
    return version


def get_version():
    ver_file = join(PROJ_ROOT, "VERSION")
    return read_version_from_file(ver_file)


def get_faasm_version():
    ver_file = join(PROJ_ROOT, "FAASM_VERSION")
    return read_version_from_file(ver_file)
