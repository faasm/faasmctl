from faasmctl.util.planner import prepare_planner_msg
from faasmctl.util.gen_proto.faabric_pb2 import BatchExecuteRequestStatus
from google.protobuf.json_format import MessageToJson, Parse
from requests import post
from time import sleep


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

    # TODO: poll
    json_msg = prepare_planner_msg(
        "EXECUTE_BATCH_STATUS", MessageToJson(ber_status, indent=None)
    )
    while True:
        # Sleep at the begining, so that the app is registered
        sleep(poll_period)

        response = post(url, data=json_msg, timeout=None)
        if response.status_code != 200:
            print(
                "POST request failed (code: {}): {}".format(
                    response.status_code, response.text
                )
            )
            break

        ber_status = Parse(response.text, BatchExecuteRequestStatus())
        if ber_status.finished:
            break

    return ber_status
