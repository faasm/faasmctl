from base64 import b64encode
from faasmctl.util.invoke import invoke_wasm
from invoke import task


@task(default=True)
def invoke(
    ctx, user, func, ini_file=None, cmdline=None, input_data=None, mpi_world_size=None
):
    """
    Invoke the execution of a user/func pair

    TODO: think how to enable all the possible command line values in a
    scalable way.
    """
    num_messages = 1
    msg_dict = {"user": user, "function": func}

    if cmdline is not None:
        msg_dict["cmdline"] = cmdline
    if input_data is not None:
        msg_dict["input_data"] = b64encode(input_data.encode("utf-8")).decode("utf-8")
    if mpi_world_size is not None:
        msg_dict["mpi_world_size"] = int(mpi_world_size)

    # Invoke WASM using main API function
    result = invoke_wasm(msg_dict, num_messages, ini_file)

    # We print the outputData of the first message for backwards compatibility.
    # We could eventually change this behaviour
    print(result.messageResults[0].outputData)
