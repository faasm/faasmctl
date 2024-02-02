from base64 import b64encode
from faasmctl.util.invoke import invoke_wasm
from faasmctl.util.planner import get_available_hosts
from invoke import task


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
        req_dict["singleHost"] = single_host
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
    result = invoke_wasm(
        msg_dict,
        num_messages=num_messages,
        req_dict=req_dict,
        ini_file=ini_file,
        host_list=host_list,
    )

    # We print the outputData of the first message for backwards compatibility.
    # We could eventually change this behaviour
    print(result.messageResults[0].outputData)
