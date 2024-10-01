from base64 import b64encode
from faasmctl.util.invoke import invoke_wasm
from faasmctl.util.planner import get_available_hosts
from faasmctl.util.results import (
    get_execution_time_from_message_results,
    get_return_code_from_message_results,
)
from invoke import task
from sys import exit
from time import time


@task(default=True)
def invoke(
    ctx,
    user,
    func,
    ini_file=None,
    cmdline=None,
    input_data=None,
    mpi_world_size=None,
    single_host=False,
    host_dist=None,
    output_format=None,
):
    """
    Invoke the execution of a user/func pair

    TODO: think how to enable all the possible command line values in a
    scalable way.
    """
    num_messages = 1
    req_dict = {"user": user, "function": func}
    msg_dict = {"user": user, "function": func}

    if cmdline is not None:
        msg_dict["cmdline"] = cmdline
    if input_data is not None:
        msg_dict["input_data"] = b64encode(input_data.encode("utf-8")).decode("utf-8")
    if mpi_world_size is not None:
        msg_dict["mpi_world_size"] = int(mpi_world_size)
    if single_host:
        req_dict["singleHostHint"] = single_host
    if host_dist:
        host_dist = host_dist.split(",")
        # Prepare a host distribution
        available_hosts = get_available_hosts()

        if len(host_dist) > len(available_hosts.hosts):
            print(
                "ERROR: requested execution among {} hosts but only {} "
                "available!".format(len(host_dist), len(available_hosts.hosts))
            )
            return 1

        # We assume that the available host list will always come in the same
        # order (for the same set of hosts)

        host_list = []
        for host in host_dist:
            host_ind = int(host.split(":")[0])
            num_in_host = int(host.split(":")[1])
            host_list += [available_hosts.hosts[host_ind].ip] * num_in_host
    else:
        host_list = None

    # Invoke WASM using main API function
    start_ts = time()
    result = invoke_wasm(
        msg_dict,
        num_messages=num_messages,
        req_dict=req_dict,
        ini_file=ini_file,
        host_list=host_list,
    )
    end_ts = time()

    # Pretty-print a summary of the execution

    user = result.messageResults[0].user
    function = result.messageResults[0].function
    output = result.messageResults[0].outputData
    ret_val = get_return_code_from_message_results(result)
    # Wall time is the time elapsed as measured from the calling python script
    wall_time = "{:.2f} s".format(end_ts - start_ts)
    # Exec time is the time the function actually executed inside Faasm
    exec_time = "{:.2f} s".format(
        get_execution_time_from_message_results(result, unit="s")
    )

    if output_format is not None:
        if output_format == "exec-time":
            print(exec_time[:-2])
            return 0

        if output_format == "wall-time":
            print(wall_time[-2])
            return 0

        if output_format == "start-end-ts":
            print(f"{start_ts},{end_ts}")
            return 0

    print("======================= Faasm Execution =========================")
    print("Function: \t\t\t{}/{}".format(user, function))
    print("Return value: \t\t\t{}".format(ret_val))
    print("Wall time: \t\t\t{}".format(wall_time))
    print("Execution time: \t\t{}".format(exec_time))
    print("-----------------------------------------------------------------")
    print("Output:\n{}".format(output))
    print("=================================================================")

    # Use sys/exit to propagate the error code to the bash process. If
    # execution fails, we want the bash process to have a non-zero exit code.
    # This is very helpful for testing environments like GHA
    exit(ret_val)
