from faasmctl.util.batch import batch_exec_factory
from faasmctl.util.config import (
    get_faasm_ini_file,
    get_faasm_planner_host_port,
)
from faasmctl.util.invoke import invoke_and_await
from faasmctl.util.planner import prepare_planner_msg
from google.protobuf.json_format import MessageToJson
from invoke import task
from requests import post


@task(default=True)
def invoke(ctx, user, func, ini_file=None):
    """
    Invoke the execution of a user/func pair

    TODO: think how to enable all the possible command line values in a
    scalable way.
    UPDATE: maybe support passing a dict that we parse into a protobuf
    """
    # TODO: work out the number of messages
    num_messages = 1
    req = batch_exec_factory(user, func, num_messages)
    json_msg = prepare_planner_msg("EXECUTE_BATCH", MessageToJson(req, indent=None))

    if not ini_file:
        ini_file = get_faasm_ini_file()

    host, port = get_faasm_planner_host_port(ini_file)
    url = "http://{}:{}".format(host, port)

    result = invoke_and_await(url, json_msg, num_messages)

    # We print the outputData of the first message for backwards compatibility.
    # We could eventually change this behaviour
    print(result.messageResults[0].outputData)
