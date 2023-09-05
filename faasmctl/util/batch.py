from faasmctl.util.message import message_factory
from faasmctl.util.gen_proto.faabric_pb2 import BatchExecuteRequest
from faasmctl.util.random import generate_gid


def batch_exec_factory(msg_dict, num_messages):
    req = BatchExecuteRequest()
    req.appId = generate_gid()
    req.user = msg_dict["user"]
    req.function = msg_dict["function"]

    for _ in range(num_messages):
        req.messages.append(message_factory(msg_dict, req.appId))

    return req
