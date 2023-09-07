from faasmctl.util.config import get_faasm_ini_file, get_faasm_planner_host_port
from faasmctl.util.gen_proto.planner_pb2 import GetInFlightAppsResponse
from faasmctl.util.planner import get_available_hosts, prepare_planner_msg
from google.protobuf.json_format import Parse
from invoke import task
from requests import post
from time import sleep


def get_in_fligh_apps():
    host, port = get_faasm_planner_host_port(get_faasm_ini_file())
    url = "http://{}:{}".format(host, port)
    planner_msg = prepare_planner_msg("GET_IN_FLIGHT_APPS")

    response = post(url, data=planner_msg, timeout=None)

    if response.status_code != 200:
        print(
            "Error getting in flight apps (code: {}): {}".format(
                response.status_code, response.text
            )
        )
        raise RuntimeError("Error getting in flight apps")

    in_flight_apps = Parse(response.text, GetInFlightAppsResponse())

    return in_flight_apps


def print_planner_resources():
    """
    Helper method to visualise the state of the planner
    """
    host, port = get_faasm_planner_host_port(get_faasm_ini_file())

    def color_text(color, text="X"):
        num1 = str(color)
        return f"\033[38;5;{num1}m{text}\033[0;0m"

    def print_line(host_msg, worker_occupation):
        line = "{}\t".format(host_msg.ip)
        used_slots = host_msg.usedSlots
        occupation = (
            worker_occupation[host_msg.ip] if host_msg.ip in worker_occupation else []
        )
        if used_slots != len(occupation):
            print(
                "Expected {} used slots for host {} but got {}!".format(
                    used_slots,
                    host_msg["ip"],
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

    def print_apps_legend(in_flight_apps):
        num_apps_per_line = 2
        line = ""
        for i, app in enumerate(in_flight_apps.apps):
            app_color = app.appId % 256
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
    footer = "================================================"

    in_flight_apps = get_in_fligh_apps()
    worker_occupation = {}
    for app in in_flight_apps.apps:
        app_color = app.appId % 256
        for ip in app.hostIps:
            if ip not in worker_occupation:
                worker_occupation[ip] = []
            worker_occupation[ip].append(app_color)

    registered_workers = get_available_hosts()
    print(header)
    # Print registered worker occupation
    for worker in registered_workers.hosts:
        print_line(worker, worker_occupation)
    print(divide)
    # Print app-to-color legend
    print_apps_legend(in_flight_apps)
    print(footer)


@task
def planner(ctx, poll_period_sec=2):
    """
    Monitor the in-flight apps and host occupation in the planner
    """
    while True:
        print_planner_resources()
        sleep(poll_period_sec)
