from faasmctl.util.gen_proto.faabric_pb2 import Message
from faasmctl.util.random import generate_gid


def message_factory(user, func, app_id=None):
    if not app_id:
        app_id = generate_gid()

    msg = Message()
    msg.user = user
    msg.function = func
    msg.appId = app_id
    msg.id = generate_gid()

    return msg
