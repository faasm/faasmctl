from os import environ

FAASM_VERSION = "0.27.0"


def get_version():
    """
    Get the Faasm version to check-out the source from

    Faasmctl ships with a default Faasm version (`FAASM_VERSION` in this file)
    but it also supports overwriting its value by setting the env. variable
    FAASM_VERSION

    Returns:
    - A string with the corresponding Faasm version
    """
    if "FAASM_VERSION" in environ:
        return environ["FAASM_VERSION"]

    return FAASM_VERSION


# Define this constants after the above method to be able to use it
FAASM_DOCKER_REGISTRY = "faasm.azurecr.io"
FAASM_CLI_IMAGE = "{}/cli:{}".format(FAASM_DOCKER_REGISTRY, get_version())
