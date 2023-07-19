from socket import (
    AF_INET,
    SOCK_STREAM,
    error as socket_error,
    socket,
)

LOCALHOST_IP = "127.0.0.1"


def get_next_bindable_port(start_port):
    """
    Helper method to know what's the next available port to bind to

    When deploying more than one compose cluster using Faasm, a common problem
    we run into is the ports we expose to the host. Services like upload, or
    planner need to expose certain ports to the host. That being said, we
    can't bind to, and expose, the same port multiple times. Instead, we
    pick the next port that is bindable in the host, and use that to interact
    with the cluster.

    Parameters:
    - start_port (int): port to start checking for bindable addresses from

    Returns:
    - First port greater or equal than start_port that we can bind listen to
    """
    bind_port = start_port
    while True:
        s = socket(AF_INET, SOCK_STREAM)
        try:
            s.bind((LOCALHOST_IP, bind_port))
            s.close()
            break
        except socket_error:
            bind_port += 1

    return bind_port
