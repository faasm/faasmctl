from faasmctl.util.env import PROJ_ROOT
from os.path import join


def get_version():
    def read_version_from_file(filename):
        with open(filename, "r") as fh:
            version = fh.read()
            version = version.strip()
        return version

    ver_file = join(PROJ_ROOT, "VERSION")
    return read_version_from_file(ver_file)
