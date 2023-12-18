from faasmctl.util.message import message_factory
from faasmctl.util.gen_proto.faabric_pb2 import BatchExecuteRequest
from faasmctl.util.random import generate_gid
from google.protobuf.json_format import ParseDict


def batch_exec_factory(req_dict, msg_dict, num_messages):
    req = ParseDict(req_dict, BatchExecuteRequest())
    req.appId = generate_gid()

    for _ in range(num_messages):
        req.messages.append(message_factory(msg_dict, req.appId))

    return req
