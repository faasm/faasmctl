#!/usr/bin/env python3

from os import environ, listdir, makedirs
from os.path import dirname, exists, join, realpath
from shutil import rmtree
from sys import argv
from subprocess import run

FAASMCTL_ROOT = dirname(dirname(realpath(__file__)))

# Unfortunately, we need to duplicate this constants here as we need to be
# able to run this file in standalone mode, as if the proto files are not
# generated, some imports in `faasmctl` will fail
GEN_PROTO_DIR = join(FAASMCTL_ROOT, "util", "gen_proto")
FAASM_CLI_IMAGE = "faasm.azurecr.io/cli"

PROTO_FILES = [
    "faabric_pb2.py",
    "planner_pb2.py",
]


# We can not import faasmctl here
def get_faasm_version():
    ver_file = join(FAASMCTL_ROOT, "util", "faasm.py")
    cmd = "cat {} | grep 'FAASM_VERSION =' | cut -d' ' -f3".format(ver_file)
    version = (
        run(cmd, shell=True, check=True, capture_output=True)
        .stdout.decode("utf-8")
        .strip()[1:-1]
    )

    return version


def gen_proto_files(clean=False):
    """
    Generate python proto files to interact with the Faasm cluster
    """
    if clean:
        rmtree(GEN_PROTO_DIR)

    if not exists(GEN_PROTO_DIR):
        makedirs(GEN_PROTO_DIR)

    pb_files = [f for f in listdir(GEN_PROTO_DIR) if f.endswith("pb2.py")]
    pb_files.sort()

    if pb_files == PROTO_FILES:
        return

    if "FAASM_VERSION" in environ:
        faasm_ver = environ["FAASM_VERSION"]
    else:
        faasm_ver = get_faasm_version()

    print("Generating Faasm (v{}) protobuf files...".format(faasm_ver))
    tmp_ctr_name = "faasm_gen_proto"
    cm = "docker run -d -i --name {} {}:{}".format(
        tmp_ctr_name, FAASM_CLI_IMAGE, faasm_ver
    )
    run(cm, shell=True, check=True)

    # Find the right protoc binary
    docker_exec_prefix = "docker exec {}".format(tmp_ctr_name)
    find_protoc_cmd = "{} bash -c 'find ~/.conan -name protoc'".format(
        docker_exec_prefix
    )
    protoc_bin = (
        run(find_protoc_cmd, shell=True, capture_output=True)
        .stdout.decode("utf-8")
        .split("\n")
    )
    p_bin = [p_bin for p_bin in protoc_bin if "build_subfolder" in p_bin]
    p_bin = p_bin[0].strip()

    # Generate python protobuf files
    code_dir = "/usr/local/code/faasm/faabric"
    protoc_cmd = [
        p_bin,
        "--proto_path={}".format(code_dir),
        "--python_out={}".format(code_dir),
        "{}/src/planner/planner.proto".format(code_dir),
        "{}/src/proto/faabric.proto".format(code_dir),
    ]
    protoc_cmd = " ".join(protoc_cmd)
    docker_cmd = "{} bash -c '{}'".format(docker_exec_prefix, protoc_cmd)
    run(docker_cmd, shell=True, check=True)

    # Finally, copy the generated protobuf files to the desired location
    for proto_file in PROTO_FILES:
        if "planner" in proto_file:
            proto_ctr_path = join(code_dir, "src", "planner", proto_file)
        else:
            proto_ctr_path = join(code_dir, "src", "proto", proto_file)
        proto_faasmctl_path = join(GEN_PROTO_DIR, proto_file)

        docker_cp_cmd = "docker cp {}:{} {}".format(
            tmp_ctr_name, proto_ctr_path, proto_faasmctl_path
        )
        run(docker_cp_cmd, shell=True, check=True)

    # Delete container
    run("docker rm -f {}".format(tmp_ctr_name), shell=True, check=True)
    print("Done generating protobuf files!")


if __name__ == "__main__":
    clean = len(argv) == 2 and argv[1] == "--clean"
    gen_proto_files(clean)
