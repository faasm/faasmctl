# TODO: somehow generate proto files in faasmctl (right now they are copied in)
from faasmctl.util.message import message_factory
from faasmctl.util.gen_proto.faabric_pb2 import BatchExecuteRequest
from faasmctl.util.random import generate_gid


# This method replicates the batchExecFactory in faabric/src/util/batch.cpp
def batch_exec_factory(user, func, num_messages):
    req = BatchExecuteRequest()
    req.appId = generate_gid()

    for _ in range(num_messages):
        req.messages.append(message_factory(user, func, req.appId))

    return req
