from faasmctl.util.gen_proto.faabric_pb2 import Message
from faasmctl.util.random import generate_gid
from google.protobuf.json_format import ParseDict


def message_factory(msg_dict, app_id=None):
    if not app_id:
        app_id = generate_gid()

    msg = ParseDict(msg_dict, Message())
    msg.appId = app_id
    msg.id = generate_gid()

    return msg
