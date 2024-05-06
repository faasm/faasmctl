from faasmctl.util.config import get_faasm_ini_file, get_faasm_planner_host_port
from faasmctl.util.gen_proto.planner_pb2 import (
    AvailableHostsResponse,
    GetInFlightAppsResponse,
    HttpMessage,
    SetEvictedVmIpsRequest,
)
from google.protobuf.json_format import MessageToJson, Parse
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
    elif msg_type == "FLUSH_AVAILABLE_HOSTS":
        http_message.type = HttpMessage.Type.FLUSH_AVAILABLE_HOSTS
    elif msg_type == "FLUSH_EXECUTORS":
        http_message.type = HttpMessage.Type.FLUSH_EXECUTORS
    elif msg_type == "FLUSH_SCHEDULING_STATE":
        http_message.type = HttpMessage.Type.FLUSH_SCHEDULING_STATE
    elif msg_type == "GET_AVAILABLE_HOSTS":
        http_message.type = HttpMessage.Type.GET_AVAILABLE_HOSTS
    elif msg_type == "GET_CONFIG":
        http_message.type = HttpMessage.Type.GET_CONFIG
    elif msg_type == "GET_EXEC_GRAPH":
        http_message.type = HttpMessage.Type.GET_EXEC_GRAPH
    elif msg_type == "GET_IN_FLIGHT_APPS":
        http_message.type = HttpMessage.Type.GET_IN_FLIGHT_APPS
    elif msg_type == "EXECUTE_BATCH":
        http_message.type = HttpMessage.Type.EXECUTE_BATCH
    elif msg_type == "EXECUTE_BATCH_STATUS":
        http_message.type = HttpMessage.Type.EXECUTE_BATCH_STATUS
    elif msg_type == "PRELOAD_SCHEDULING_DECISION":
        http_message.type = HttpMessage.Type.PRELOAD_SCHEDULING_DECISION
    elif msg_type == "SET_NEXT_EVICTED_VM":
        http_message.type = HttpMessage.Type.SET_NEXT_EVICTED_VM
    elif msg_type == "SET_POLICY":
        http_message.type = HttpMessage.Type.SET_POLICY
    else:
        raise RuntimeError("Unrecognised HTTP msg type: {}".format(msg_type))

    if msg_body:
        http_message.payloadJson = msg_body

    return MessageToJson(http_message, indent=None)


def reset(expected_num_workers=None, verbose=False):
    """
    Reset the planner with an HTTP request

    Reset clears the available hosts, flushes the workers and clears the
    scheduling state

    - expected_num_workers (int): optional parameter indicating the number of
      workers the user expects to be registered with the planner. If provided,
      after reset we will wait until enough workers have registered themselves
      with the planner
    """
    host, port = get_faasm_planner_host_port(get_faasm_ini_file())
    url = "http://{}:{}".format(host, port)

    planner_msg = prepare_planner_msg("RESET")

    response = post(url, data=planner_msg, timeout=None)

    if response.status_code != 200:
        print(
            "Error resetting planner (code: {}): {}".format(
                response.status_code, response.text
            )
        )
        raise RuntimeError("Error resetting planner")

    if expected_num_workers:
        wait_for_workers(expected_num_workers, verbose=verbose)


# ----------
# Host Membership Getters/Setters
# ----------


def get_available_hosts():
    """
    Get the list of available hosts
    """
    host, port = get_faasm_planner_host_port(get_faasm_ini_file())
    url = "http://{}:{}".format(host, port)
    planner_msg = prepare_planner_msg("GET_AVAILABLE_HOSTS")

    response = post(url, data=planner_msg, timeout=None)
    if response.status_code != 200:
        print(
            "Error resetting planner (code: {}): {}".format(
                response.status_code, response.text
            )
        )
        raise RuntimeError("Error resetting planner")

    available_hosts = Parse(response.text, AvailableHostsResponse())
    return available_hosts


def wait_for_workers(expected_num_workers, verbose=False):
    """
    Wait for a number of workers to be registered with the planner

    This method polls the planner over HTTP querying for the number of
    registered workers, and returns when the number matches a user-provided
    value. This method is useful to wait for the planner to be ready after
    reset.

    Arguments:
    - expected_num_workers (int): the number of workers to wait for
    """
    poll_period = 2
    while True:
        available_hosts = get_available_hosts()

        if len(available_hosts.hosts) == expected_num_workers:
            break

        if verbose:
            print(
                "Waiting for workers to register with planner ({}/{})...".format(
                    len(available_hosts.hosts), expected_num_workers
                )
            )

        sleep(poll_period)


# ----------
# Scheduling State Getters/Setters
# ----------


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


def set_next_evicted_host(host_ips):
    host, port = get_faasm_planner_host_port(get_faasm_ini_file())
    url = "http://{}:{}".format(host, port)

    evicted_vm_ips = SetEvictedVmIpsRequest()
    evicted_vm_ips.vmIps.extend(host_ips)

    planner_msg = prepare_planner_msg(
        "SET_NEXT_EVICTED_VM", MessageToJson(evicted_vm_ips, indent=None)
    )
    response = post(url, data=planner_msg, timeout=None)

    if response.status_code != 200:
        print(
            "Error setting next evicted host 'ips: {}' (code: {}): {}".format(
                host_ips, response.status_code, response.text
            )
        )
        raise RuntimeError("Error setting next evicted host")


def set_planner_policy(policy):
    host, port = get_faasm_planner_host_port(get_faasm_ini_file())
    url = "http://{}:{}".format(host, port)
    planner_msg = prepare_planner_msg("SET_POLICY", policy)

    response = post(url, data=planner_msg, timeout=None)

    if response.status_code != 200:
        print(
            "Error setting planner policy '{}' (code: {}): {}".format(
                policy, response.status_code, response.text
            )
        )
        raise RuntimeError("Error setting planner policy")
