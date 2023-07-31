from datetime import datetime
from faasmctl.util.env import FAASM_SOURCE_DIR
from faasmctl.util.faasm import get_version as get_faasm_version
from faasmctl.util.network import LOCALHOST_IP
from os import makedirs
from os.path import abspath, exists, join
from shutil import rmtree
from subprocess import CalledProcessError, run


def _check_version_mismatch(checkout_path):
    # Check if there's a mismatch between the checked-out code version and
    # faasmctl's pinned faasm version
    with open(join(checkout_path, "VERSION"), "r") as fh:
        faasm_ver = fh.read()
        faasm_ver = faasm_ver.strip()
    if faasm_ver != get_faasm_version():
        print(
            "WARNING: mismatch between the checked-out version and"
            " faasmctl's pinned faasm version ({} != {}) using {}".format(
                faasm_ver, get_faasm_version(), faasm_ver
            )
        )

    return faasm_ver


def fetch_faasm_code(faasm_source=None, force=False):
    """
    Check-out the Faasm tag
    """
    checkout_path = (
        faasm_source if faasm_source else join(FAASM_SOURCE_DIR, get_faasm_version())
    )
    must_checkout = force or not exists(checkout_path)

    if not must_checkout:
        faasm_ver = _check_version_mismatch(checkout_path)
        return checkout_path, faasm_ver

    # Ensure a clean clone directory
    rmtree(checkout_path, ignore_errors=True)
    makedirs(checkout_path, exist_ok=True)

    print("Checking out Faasm v{} to {}".format(get_faasm_version(), checkout_path))
    git_cmd = [
        "git clone",
        "--branch v{}".format(get_faasm_version()),
        "https://github.com/faasm/faasm",
        checkout_path,
    ]
    git_cmd = " ".join(git_cmd)
    try:
        run(git_cmd, shell=True, check=True)
    except CalledProcessError as e:
        # FIXME: fix this behaviour in faasm caused by the `./dev` directory
        # being root-owned
        if e.returncode == 128:
            tmp_fix = "sudo rm -rf {}".format(checkout_path)
            print(
                "ERROR: we were not able to clean the checkout dir. This is"
                " probably due to an issue in Faasm where some directories "
                "in a compose cluster are root-owned (in the container). "
                "Try running the following:\n{}".format(tmp_fix)
            )
            raise RuntimeError("Error. Try running:\n{}".format(tmp_fix))

    # FIXME: allow a purely detached faasm checkout. Right now, cpp's code
    # source is _always_ mounted from clients/cpp, and so is clients/python,
    # and transitively clients/python/third-party/cpp
    git_cmd = "git submodule update --init"
    run(git_cmd, shell=True, check=True, cwd=checkout_path)
    git_cmd = "git submodule update --init ./third-party/cpp"
    run(git_cmd, shell=True, check=True, cwd=join(checkout_path, "clients", "python"))

    faasm_ver = _check_version_mismatch(checkout_path)

    return checkout_path, faasm_ver


def generate_ini_file(backend, out_file, **kwargs):
    if backend == "compose":
        if "name" not in kwargs or "cwd" not in kwargs:
            raise RuntimeError("Not enough compose arguments provided!")
        cluster_name = kwargs["name"]
        working_dir = kwargs["cwd"]

        upload_ip = LOCALHOST_IP
        upload_port = kwargs["upload_host_port"]
        planner_ip = LOCALHOST_IP
        planner_port = kwargs["planner_host_port"]
        worker_names = kwargs["worker_names"]
        worker_ips = kwargs["worker_ips"]
    elif backend == "k8s":
        working_dir = kwargs["cwd"]
        k8s_config = kwargs["k8s_config"]
        k8s_namespace = kwargs["k8s_namespace"]

        upload_ip = kwargs["upload_ip"]
        upload_port = kwargs["upload_port"]
        planner_ip = kwargs["planner_ip"]
        planner_port = kwargs["planner_port"]
        worker_names = kwargs["worker_names"]
        worker_ips = kwargs["worker_ips"]
    else:
        raise RuntimeError("Backend {} not supported!".format(backend))

    if not out_file:
        out_file = "./faasm.ini"

    print("Generating Faasm INI file at: {}".format(out_file))
    with open(out_file, "w") as fh:
        fh.write("[Faasm]\n")

        # This comment line can't be outside of the Faasm section
        fh.write("# Auto-generated at {}\n".format(datetime.now()))

        fh.write("backend = {}\n".format(backend))
        fh.write("working_dir = {}\n".format(working_dir))
        if backend == "compose":
            fh.write("mount_source = {}\n".format(kwargs["mount_source"]))
        elif backend == "k8s":
            fh.write("k8s_config = {}\n".format(k8s_config))
        if backend == "compose":
            fh.write("cluster_name = {}\n".format(cluster_name))
        elif backend == "k8s":
            fh.write("k8s_namespace = {}\n".format(k8s_namespace))
        fh.write("upload_host = {}\n".format(upload_ip))
        if backend == "compose":
            fh.write("upload_host_in_docker = upload\n")
        fh.write("upload_port = {}\n".format(upload_port))
        if backend == "compose":
            fh.write(
                "upload_port_in_docker = {}\n".format(kwargs["upload_docker_port"])
            )
        fh.write("planner_host = {}\n".format(planner_ip))
        if backend == "compose":
            fh.write("planner_host_in_docker = planner\n")
        if backend == "compose":
            fh.write("minio_port = {}\n".format(kwargs["minio_host_port"]))
            fh.write("minio_port_in_docker = {}\n".format(kwargs["minio_docker_port"]))
        fh.write("planner_port = {}\n".format(planner_port))
        if backend == "compose":
            fh.write(
                "planner_port_in_docker = {}\n".format(kwargs["planner_docker_port"])
            )
        fh.write("worker_names = {}\n".format(",".join(worker_names)))
        fh.write("worker_ips = {}\n".format(",".join(worker_ips)))

    with open(out_file, "r") as fh:
        print(fh.read())

    return abspath(out_file)
