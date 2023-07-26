from faasmctl.util.config import get_faasm_planner_host_port
from faasmctl.util.gen_proto.planner_pb2 import HttpMessage
from google.protobuf.json_format import MessageToJson
from requests import post

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
    elif msg_type == "GET_CONFIG":
        http_message.type = HttpMessage.Type.GET_CONFIG
    elif msg_type == "GET_EXEC_GRAPH":
        http_message.type = HttpMessage.Type.GET_EXEC_GRAPH
    elif msg_type == "EXECUTE_BATCH":
        http_message.type = HttpMessage.Type.EXECUTE_BATCH
    elif msg_type == "EXECUTE_BATCH_STATUS":
        http_message.type = HttpMessage.Type.EXECUTE_BATCH_STATUS
    else:
        raise RuntimeError("Unrecognised HTTP msg type: {}".format(msg_type))

    if msg_body:
        http_message.payloadJson = msg_body

    return MessageToJson(http_message, indent=None)


# ----------
# RESET
# ----------


def reset():
    """
    Reset the planner with an HTTP request. Reset clears the available hosts,
    and the scheduling state
    """
    host, port = get_faasm_planner_host_port()
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
