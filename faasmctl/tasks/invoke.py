from faasmctl.util.invoke import invoke_wasm
from invoke import task


@task(default=True)
def invoke(ctx, user, func, ini_file=None):
    """
    Invoke the execution of a user/func pair

    TODO: think how to enable all the possible command line values in a
    scalable way.
    """
    # TODO: work out the number of messages
    num_messages = 1
    msg_dict = {"user": user, "function": func}

    # Invoke WASM using main API function
    result = invoke_wasm(msg_dict, num_messages, ini_file)

    # We print the outputData of the first message for backwards compatibility.
    # We could eventually change this behaviour
    print(result.messageResults[0].outputData)
