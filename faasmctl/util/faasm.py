from faasmctl.util.version import get_faasm_version as get_version

FAASM_DOCKER_REGISTRY = "faasm.azurecr.io"
FAASM_CLI_IMAGE = "{}/cli:{}".format(FAASM_DOCKER_REGISTRY, get_version())
