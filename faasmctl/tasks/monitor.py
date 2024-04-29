from faasmctl.util.config import (
    get_faasm_ini_file,
    get_faasm_ini_value,
    get_faasm_planner_host_port,
)
from faasmctl.util.faasm import FAASM_CLI_IMAGE
from faasmctl.util.planner import get_available_hosts, get_in_fligh_apps
from invoke import task
from signal import SIGINT, signal
from subprocess import run
from sys import exit as sys_exit
from time import sleep

CTR_NAME_BASE = "faasm-is-migratable-workon"
NUM_APPS_PER_LINE = 3


def get_ctr_name():
    """
    Generate a unique container name to be able to monitor multiple cluster
    instances
    """
    backend = get_faasm_ini_value(get_faasm_ini_file(), "Faasm", "backend")

    if backend == "compose":
        return "{}-{}".format(
            CTR_NAME_BASE,
            get_faasm_ini_value(get_faasm_ini_file(), "Faasm", "cluster_name"),
        )

    # We assume that the planner IP will be unique across different k8s cluster
    # instances (we replace the dots by dashes as we want to generate a suitable
    # container name)
    slug_planner_ip = get_faasm_ini_value(
        get_faasm_ini_file(), "Faasm", "planner_host"
    ).replace(".", "-", 3)
    return "{}-{}".format(CTR_NAME_BASE, slug_planner_ip)


def stop_container():
    docker_cmd = "docker rm -f {}".format(get_ctr_name())
    out = run(docker_cmd, shell=True, capture_output=True)
    assert out.returncode == 0, "Error running docker (cmd: {}): {}".format(
        docker_cmd, out.stderr.decode("utf-8")
    )


def get_apps_to_be_migrated(
    planner_policy, registered_workers, in_flight_apps, worker_occupation
):
    """
    Helper method that, given the current worker occupation, works out all the
    apps that could be migrated if they checked for a migration opportunity
    """
    # Generate worker occupation file. For more details on the file format, see:
    # https://github.com/faasm/faabric/tree/main/src/planner/is_app_migratable.cpp
    file_suffix = get_ctr_name().removeprefix(CTR_NAME_BASE)
    worker_occupation_file_path = "/tmp/worker_occupation{}.csv".format(file_suffix)
    with open(worker_occupation_file_path, "w") as fh:
        fh.write("WorkerIp,Slots\n")
        try:
            for ip in worker_occupation:
                total_slots = [w for w in registered_workers.hosts if w.ip == ip][
                    0
                ].slots
                for i in range(len(worker_occupation[ip]), total_slots):
                    worker_occupation[ip].append("-1")

                fh.write("{},{}\n".format(ip, ",".join(worker_occupation[ip])))
        except IndexError:
            return []

    # Start container in the background
    docker_cmd = [
        "docker run -dt",
        "-v {}:{}".format(worker_occupation_file_path, worker_occupation_file_path),
        "--name {}".format(get_ctr_name()),
        FAASM_CLI_IMAGE,
    ]
    docker_cmd = " ".join(docker_cmd)
    out = run(docker_cmd, shell=True, capture_output=True)
    assert out.returncode == 0, "Error running docker (cmd: {}): {}".format(
        docker_cmd, out.stderr.decode("utf-8")
    )

    to_be_migrated_apps = []
    for app in in_flight_apps.apps:
        docker_cmd = [
            "docker exec",
            get_ctr_name(),
            "bash -c '/build/faasm/bin/is_app_migratable {} {} {}'".format(
                planner_policy, app.appId, worker_occupation_file_path
            ),
        ]
        docker_cmd = " ".join(docker_cmd)
        out = run(docker_cmd, shell=True, capture_output=True)
        if out.returncode == 1:
            # App can not be migrated
            continue
        elif out.returncode == 0:
            to_be_migrated_apps.append(app)
        else:
            # stop_container()
            # Survive downstream binary errors, but report a warning
            print(
                "WARNING: error checking if app {} can be migrated: {}".format(
                    app.appId, out.stderr.decode("utf-8")
                )
            )

    # Finally stop the container
    stop_container()

    return to_be_migrated_apps


# Keep track of the number of migrations when we started monitoring
orig_num_migrations = -1


def print_planner_resources(policy):
    """
    Helper method to visualise the state of the planner
    """
    host, port = get_faasm_planner_host_port(get_faasm_ini_file())

    def color_text(color, text="X"):
        num1 = str(color)
        return f"\033[38;5;{num1}m{text}\033[0;0m"

    def print_line(host_msg, worker_occupation, next_evicted_vm_ips=[]):
        is_evicted = host_msg.ip in next_evicted_vm_ips

        line = "{}\t".format(host_msg.ip)
        if is_evicted:
            line = "{}\t".format(color_text(1, text=host_msg.ip))

        used_slots = host_msg.usedSlots
        occupation = (
            worker_occupation[host_msg.ip] if host_msg.ip in worker_occupation else []
        )
        if used_slots != len(occupation):
            # TODO: FIXME: this is a symptom of a problem!!
            print(
                "Expected {} used slots for host {} but got {}!".format(
                    used_slots,
                    host_msg.ip,
                    len(occupation),
                )
            )
            # This may happen sometime due to some funny race condition,
            # wait to recover in the next heart beat
            return
        for i in range(host_msg.slots):
            if i < used_slots:
                line += " [{}]".format(color_text(occupation[i]))
            else:
                line += " [ ]"
        print(line)

    def get_app_color(app, policy):
        user_id = 0
        try:
            user_id = app.subType
        except AttributeError:
            pass

        # We only care about user ids if we are using the COMPACT (multi-tenant)
        # policy
        if policy != "compact":
            return app.appId % 256

        return (user_id * 10) % 256

    def print_apps_legend(in_flight_apps):
        num_apps_per_line = NUM_APPS_PER_LINE
        line = ""
        for i, app in enumerate(in_flight_apps.apps):
            app_color = get_app_color(app, policy)
            app_text = color_text(app_color, "App ID: {}".format(app.appId))
            if i == 0:
                line = app_text
            elif i % num_apps_per_line == 0:
                print(line)
                line = app_text
            else:
                line += "\t{}".format(app_text)
        print(line)

    def print_migration_opportunities(apps_to_be_migrated):
        num_apps_per_line = NUM_APPS_PER_LINE
        line = ""
        for i, app in enumerate(apps_to_be_migrated):
            app_color = get_app_color(app, policy)
            app_text = color_text(app_color, "App ID: {}".format(app.appId))
            if i == 0:
                line = app_text
            elif i % num_apps_per_line == 0:
                print(line)
                line = app_text
            else:
                line += "\t{}".format(app_text)
        print(line)

    def print_frozen_apps(frozen_apps):
        num_apps_per_line = NUM_APPS_PER_LINE
        line = ""
        for i, app in enumerate(frozen_apps):
            app_color = get_app_color(app, policy)
            app_text = color_text(app_color, "App ID: {}".format(app.appId))
            if i == 0:
                line = app_text
            elif i % num_apps_per_line == 0:
                print(line)
                line = app_text
            else:
                line += "\t{}".format(app_text)
        print(line)

    header = "============== PLANNER RESOURCES ==============="
    divide = "------------------------------------------------"
    div_mg = "*********** MIGRATION OPPORTUNITIES ************"
    div_fa = "***************** FROZEN APPS ******************"
    div_al = "************* APP ID COLOR LEGEND **************"
    footer = "================================================"

    # -------------
    # Process data
    # -------------

    global orig_num_migrations

    # Work out the worker occupation
    in_flight_apps = get_in_fligh_apps()
    worker_occupation = {}
    worker_occupation_ids = {}
    for app in in_flight_apps.apps:
        app_color = get_app_color(app, policy)
        for ip in app.hostIps:
            if ip not in worker_occupation:
                worker_occupation[ip] = []
                worker_occupation_ids[ip] = []
            worker_occupation[ip].append(app_color)
            worker_occupation_ids[ip].append(str(app.appId))

    # Work-out the number of migrations
    if orig_num_migrations < 0:
        orig_num_migrations = in_flight_apps.numMigrations

    # Work-out the forzen apps
    next_evicted_vm_ips = in_flight_apps.nextEvictedVmIps
    frozen_apps = [app for app in in_flight_apps.frozenApps]

    # Work out the existing migration opportunities
    registered_workers = get_available_hosts()
    apps_to_be_migrated = get_apps_to_be_migrated(
        policy, registered_workers, in_flight_apps, worker_occupation_ids
    )

    # -------------
    # Print all information
    # -------------

    print(header)
    # Print registered worker occupation
    for worker in registered_workers.hosts:
        print_line(worker, worker_occupation, next_evicted_vm_ips)

    # Print migration opportunities (if any)
    if len(apps_to_be_migrated) > 0:
        print(divide)
        print(div_mg)
        print(divide)
        print_migration_opportunities(apps_to_be_migrated)

    # Print frozen apps (if any)
    if len(frozen_apps) > 0:
        print(divide)
        print(div_fa)
        print(divide)
        print_frozen_apps(frozen_apps)

    # Print app-to-color legend (if any)
    if len(in_flight_apps.apps) > 0:
        print(divide)
        print(div_al)
        print(divide)
        print_apps_legend(in_flight_apps)

    # Print number of migrations
    num_migrations = in_flight_apps.numMigrations - orig_num_migrations
    if num_migrations > 0:
        print(divide)
        print("Num migrations: {}".format(num_migrations))
        print(divide)

    # Print footer
    print(footer)


def signal_handler(sig, frame):
    """
    Make sure container is not running when we press Ctrl-C
    """
    stop_container()
    sys_exit(0)


@task
def planner(ctx, policy="bin-pack", poll_period_sec=2):
    """
    Monitor the in-flight apps and host occupation in the planner
    """
    signal(SIGINT, signal_handler)
    while True:
        print_planner_resources(policy)
        sleep(poll_period_sec)
