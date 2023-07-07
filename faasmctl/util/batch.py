# TODO: somehow generate proto files in faasmctl (right now they are copied in)
from faasmctl.util.message import message_factory
from faasmctl.util.proto.faabric_pb2 import BatchExecuteRequest
from faasmctl.util.random import generate_gid


# This method replicates the batchExecFactory in faabric/src/util/batch.cpp
def batch_exec_factory(user, func, num_messages):
    req = BatchExecuteRequest()
    req.appId = generate_gid()

    for _ in range(num_messages):
        # new_msg = req.messages.add()
        # new_msg = message_factory(user, func, req.appId)
        req.messages.append(message_factory(user, func, req.appId))

    return req
