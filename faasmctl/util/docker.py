from os import environ

IN_DOCKER_ENV_VARS = [
    "CPP_DOCKER",
    "FAASM_DOCKER",
]


def in_docker():
    """
    faasmctl can be invoked both from outside and inside a docker container.
    When invoked from inside a docker container, faasmctl can only be used to
    interact with a cluster running on docker compose. In that case, we need to
    use a different IP for the services in the cluster. Fortunately, Faasm
    sets certain env. vars when running inside a container. This function
    checks for them and returns True if successful
    """
    for env_var in IN_DOCKER_ENV_VARS:
        if env_var in environ and environ[env_var] == "on":
            return True

    return False
