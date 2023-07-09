from faasmctl.util.batch import batch_exec_factory
from faasmctl.util.config import (
    get_faasm_ini_file,
    get_faasm_planner_host_port,
)
from faasmctl.util.gen_proto.faabric_pb2 import BatchExecuteRequestStatus
from faasmctl.util.planner import prepare_planner_msg
from google.protobuf.json_format import MessageToJson, Parse
from requests import post
from time import sleep


def invoke_wasm(msg_dict, num_messages=1, ini_file=None):
    """
    Main entrypoint to invoke an arbitrary message in a Faasm cluster
    """
    req = batch_exec_factory(msg_dict, num_messages)
    msg = prepare_planner_msg("EXECUTE_BATCH", MessageToJson(req, indent=None))

    if not ini_file:
        ini_file = get_faasm_ini_file()

    host, port = get_faasm_planner_host_port(ini_file)
    url = "http://{}:{}".format(host, port)

    result = invoke_and_await(url, msg, num_messages)

    return result


def invoke_and_await(url, json_msg, expected_num_messages):
    """
    Invokke the given JSON message to the given URL and poll the planner to
    wait for the response
    """
    poll_period = 2

    # The first invocation returns an appid to poll for the message
    response = post(url, data=json_msg, timeout=None)
    if response.status_code != 200:
        print(
            "POST request failed (code: {}): {}".format(
                response.status_code, response.text
            )
        )

    ber_status = Parse(response.text, BatchExecuteRequestStatus())
    ber_status.expectedNumMessages = expected_num_messages

    json_msg = prepare_planner_msg(
        "EXECUTE_BATCH_STATUS", MessageToJson(ber_status, indent=None)
    )
    while True:
        # Sleep at the begining, so that the app is registered as in-flight
        sleep(poll_period)

        response = post(url, data=json_msg, timeout=None)
        if response.status_code != 200:
            # FIXME: temporary workaround while the planner does not control
            # batch scheduling (and thus doesn't keep track of the apps in
            # flight). We may query for an app result before it is finished.
            # In this case, by default, the planner endpoint fails. But it is
            # not an error (it will be in the future)
            if response.text == "App not registered in results":
                print("WARNING: app not registered in results")
            else:
                print(
                    "POST request failed (code: {}): {}".format(
                        response.status_code, response.text
                    )
                )
                break
        else:
            # FIXME: we can remove this else when the previous FIXME is fixed,
            # and reduce a level of indentation in the following three lines
            ber_status = Parse(response.text, BatchExecuteRequestStatus())
            if ber_status.finished:
                break

    return ber_status
