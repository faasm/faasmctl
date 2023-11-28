from faasmctl.util.batch import batch_exec_factory
from faasmctl.util.config import (
    get_faasm_ini_file,
    get_faasm_planner_host_port,
)
from faasmctl.util.docker import in_docker
from faasmctl.util.gen_proto.faabric_pb2 import BatchExecuteRequestStatus
from faasmctl.util.message import message_factory
from faasmctl.util.planner import prepare_planner_msg
from google.protobuf.json_format import MessageToDict, MessageToJson, Parse
from requests import post
from time import sleep


def invoke_wasm(
    msg_dict, num_messages=1, dict_out=False, ini_file=None, host_list=None
):
    """
    Main entrypoint to invoke an arbitrary message in a Faasm cluster

    Arguments:
    - msg_dict (dict): dict-like object to build a Message Protobuf from
    - num_messages (int): number of said messages to include in the BER
    - dict_out (bool): flag to indicate that we expect the result as a JSON
                       instead than as a Message class
    - host_list (array): list of (`num_message`s IPs) where to execute each
                         message. By providing a host list in advance, we
                         are bypassing the planner's scheduling.
                         WARNING: if the host_list breaks the planner's
                         state consistency, the planner will crash, so use
                         this optional argument at your own risk!
    - ini_file (str): path to the cluster's INI file

    Return:
    - The BERStatus result either in a Protobuf class or as a dict if dict_out
      is set
    """
    req = batch_exec_factory(msg_dict, num_messages)
    msg = prepare_planner_msg("EXECUTE_BATCH", MessageToJson(req, indent=None))

    if not ini_file:
        ini_file = get_faasm_ini_file()

    host, port = get_faasm_planner_host_port(ini_file, in_docker())
    url = "http://{}:{}".format(host, port)

    # Work out the number of messages to expect in the result basing on the
    # original message
    expected_num_messages = num_messages
    if "mpi_world_size" in msg_dict:
        expected_num_messages = msg_dict["mpi_world_size"]

    # If provided a host-list, preload the scheduling decision by sending
    # a BER with a rightly-populated messages.executedHost
    if host_list is not None:
        assert len(host_list) == expected_num_messages

        for _ in range(len(req.messages), expected_num_messages):
            req.messages.append(message_factory(msg_dict, req.appId))

        # We preload a scheduling decision by passing a BER with each group
        # index associated to one host in the host list
        for group_idx in range(len(req.messages)):
            req.messages[group_idx].groupIdx = group_idx
            req.messages[group_idx].executedHost = host_list[group_idx]
            group_idx += 1

        preload_msg = prepare_planner_msg(
            "PRELOAD_SCHEDULING_DECISION", MessageToJson(req, indent=None)
        )
        response = post(url, data=preload_msg, timeout=None)
        if response.status_code != 200:
            print(
                "Error preloading scheduling decision (code: {}): {}".format(
                    response.status_code, response.text
                )
            )
            raise RuntimeError("Error preloading scheduling decision!")

    result = invoke_and_await(url, msg, expected_num_messages)

    if dict_out:
        return MessageToDict(result)

    return result


def invoke_and_await(url, json_msg, expected_num_messages):
    """
    Invoke the given JSON message to the given URL and poll the planner to
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
                # FIXME: we will have to emit a warning eventually, for now
                # we pass
                # print("WARNING: app not registered in results")
                pass
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
