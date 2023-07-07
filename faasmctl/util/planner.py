from faasmctl.util.proto.planner_pb2 import HttpMessage
from google.protobuf.json_format import MessageToJson
from json import loads as json_loads
from json.decoder import JSONDecodeError
from requests import post
from time import sleep

PLANNER_JSON_MESSAGE_FAILED = {"dead": "beef"}

# ----------
# Util
# ----------


def prepare_planner_msg(msg_type, msg_body=None):
    http_message = HttpMessage()
    if msg_type == "RESET":
        http_message.type = HttpMessage.Type.RESET
    elif msg_type == "FLUSH_HOSTS":
        http_message.type = HttpMessage.Type.FLUSH_HOSTS
    elif msg_type == "FLUSH_EXECUTORS":
        http_message.type = HttpMessage.Type.FLUSH_EXECUTORS
    elif msg_type == "GET_CONFIG":
        http_message.type = HttpMessage.Type.GET_CONFIG
    elif msg_type == "GET_EXEC_GRAPH":
        http_message.type = HttpMessage.Type.GET_EXEC_GRAPH
    elif msg_type == "EXECUTE_BATCH":
        http_message.type = HttpMessage.Type.EXECUTE_BATCH
    elif msg_type == "EXECUTE_BATCH_STATUS":
        http_message.type = HttpMessage.Type.EXECUTE_BATCH_STATUS
    else:
        raise RuntimeError("Unrecognised HTTP message type: {}".format(msg_type))

    if msg_body:
        http_message.payloadJson = msg_body

    return MessageToJson(http_message, indent=None)


# ----------
# RESET
# ----------


def reset(host, port):
    """
    Reset the planner with an HTTP request. Reset clears the available hosts,
    and the scheduling state
    """
    url = "http://{}:{}".format(host, port)

    planner_msg = prepare_planner_msg("RESET")

    response = post(url, json=planner_msg, timeout=None)

    if response.status_code != 200:
        print(
            "Error resetting planner (code: {}): {}".format(
                response.status_code, response.text
            )
        )
        raise RuntimeError("Error resetting planner")


# ----------
# GET_APP_MESSAGES
# ----------


def get_app_messages(host, port, app_id):
    """
    Get all the messages recorded for an app
    """
    url = "http://{}:{}".format(host, port)
    # Currently we only need to set the app id to get the app messages
    msg = {
        "appId": app_id,
    }
    planner_msg = prepare_planner_msg("GET_APP_MESSAGES", msg)

    response = post(url, json=planner_msg, timeout=None)
    if response.status_code != 200:
        print(
            "Error getting app messages for app {} (code: {}): {}".format(
                app_id, response.status_code, response.text
            )
        )
        raise RuntimeError("Error posting GET_APP_MESSAGES")

    try:
        response_json = json_loads(response.text)
    except JSONDecodeError as e:
        print("Error deserialising JSON message: {}".format(e.msg))
        print("Actual message: {}".format(response.text))

    if "messages" not in response_json:
        return []

    return response_json["messages"]


def get_msg_result(host, port, msg):
    """
    Wait for a message result to be registered with the planner
    """
    url = "http://{}:{}".format(host, port)
    planner_status_msg = prepare_planner_msg("EXECUTE_STATUS", msg)
    status_response = post(url, json=planner_status_msg)

    while (
        status_response.status_code != 200
        or status_response.text.startswith("RUNNING")
    ):
        if not status_response.text:
            print(
                "Empty response text (status: {})".format(
                    status_response.status
                )
            )
            raise RuntimeError("Empty status response")
        elif (
            status_response.status_code >= 400
            or status_response.text.startswith("FAILED")
        ):
            print("Error running task: {}".format(status_response.status_code))
            print("Error message: {}".format(status_response.text))
            raise RuntimeError("Error running task!")

        sleep(2)
        status_response = post(url, json=planner_status_msg)

    try:
        result_json = json_loads(status_response.text)
    except JSONDecodeError as e:
        print("Error deserialising JSON message: {}".format(e.msg))
        print("Actual message: {}".format(status_response.text))

    return result_json


def get_app_result(host, port, app_id, app_size, verbose=False):
    """
    Wait for all messages in an app identified by `app_id` to have finished.
    We will wait for a total of `app_size` messages
    """
    # First, poll the planner until all messages are registered with the app
    registered_msgs = get_app_messages(host, port, app_id)
    while len(registered_msgs) != app_size:
        if verbose:
            print(
                "Waiting for messages to be registered with app "
                "{} ({}/{})".format(app_id, len(registered_msgs), app_size)
            )
        sleep(2)
        registered_msgs = get_app_messages(host, port, app_id)

    if verbose:
        print(
            "All messages registerd with app {} ({}/{})".format(
                app_id, len(registered_msgs), app_size
            )
        )
    # Now, for each message, wait for it to be completed
    results = []
    app_has_failed = False
    for i, msg in enumerate(registered_msgs):
        if verbose:
            print(
                "Polling message {} (app: {}, {}/{})".format(
                    msg["id"], app_id, i + 1, len(registered_msgs)
                )
            )
        # Poll for all the messages even if some of them have failed to ensure
        # a graceful recovery of the error
        try:
            result_json = get_msg_result(host, port, msg)
            results.append(result_json)
        # TODO: define a custom error like MessageExecuteFailure
        except RuntimeError:
            app_has_failed = True
            results.append(PLANNER_JSON_MESSAGE_FAILED)

    # If some messages in the app have actually failed, raise an error once
    # we have all of them
    # TODO: define a better error
    if app_has_failed:
        raise RuntimeError("App failed")

    return results


# ----------
# GET_AVAILABLE_HOSTS
# ----------


def get_registered_workers(host, port):
    """
    Get the set of workers registered with the planner
    """
    url = "http://{}:{}".format(host, port)
    planner_msg = prepare_planner_msg("GET_AVAILABLE_HOSTS")

    response = post(url, json=planner_msg, timeout=None)

    if response.status_code != 200:
        print(
            "Error waiting for workers (code: {}): {}".format(
                response.status_code, response.text
            )
        )
        raise RuntimeError("Error waiting for workers")

    try:
        response_json = json_loads(response.text)
    except JSONDecodeError as e:
        print("Error deserialising JSON message: {}".format(e.msg))
        print("Actual message: {}".format(response.text))

    if "hosts" not in response_json:
        return None

    return response_json["hosts"]


# ----------
# GET_IN_FLIGHT_APPS
# ----------


def get_in_fligh_apps(host, port):
    url = "http://{}:{}".format(host, port)
    planner_msg = prepare_planner_msg("GET_IN_FLIGHT_APPS")

    response = post(url, json=planner_msg, timeout=None)

    if response.status_code != 200:
        print(
            "Error getting in flight apps (code: {}): {}".format(
                response.status_code, response.text
            )
        )
        raise RuntimeError("Error getting in flight apps")

    try:
        response_json = json_loads(response.text)
    except JSONDecodeError as e:
        print("Error deserialising JSON message: {}".format(e.msg))
        print("Actual message: {}".format(response.text))

    if "apps" not in response_json:
        return []

    return response_json["apps"]


def print_planner_resources(host, port):
    """
    Helper method to visualise the state of the planner
    """

    def color_text(color, text="X"):
        num1 = str(color)
        return f"\033[38;5;{num1}m{text}\033[0;0m"

    def print_line(host_msg, worker_occupation):
        line = "{}\t".format(host_msg["ip"])
        used_slots = host_msg["usedSlots"] if "usedSlots" in host_msg else 0
        occupation = (
            worker_occupation[host_msg["ip"]]
            if host_msg["ip"] in worker_occupation
            else []
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
        for i in range(host_msg["slots"]):
            if i < used_slots:
                line += " [{}]".format(color_text(occupation[i]))
            else:
                line += " [ ]"
        print(line)

    def print_apps_legend(in_flight_apps):
        num_apps_per_line = 2
        line = ""
        for i, app in enumerate(in_flight_apps):
            app_color = app["appId"] % 256
            app_text = color_text(app_color, "App ID: {}".format(app["appId"]))
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

    in_flight_apps = get_in_fligh_apps(host, port)
    worker_occupation = {}
    for app in in_flight_apps:
        app_color = app["appId"] % 256
        for ip in app["hostIps"]:
            if ip not in worker_occupation:
                worker_occupation[ip] = []
            worker_occupation[ip].append(app_color)

    registered_workers = get_registered_workers(host, port)
    print(header)
    # Print registered worker occupation
    for worker in registered_workers:
        print_line(worker, worker_occupation)
    print(divide)
    # Print app-to-color legend
    print_apps_legend(in_flight_apps)
    print(footer)
