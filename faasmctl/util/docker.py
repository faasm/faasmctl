from os import environ
from os.path import join

IN_DOCKER_ENV_VARS = [
    "CPP_DOCKER",
    "FAASM_DOCKER",
]


def in_docker():
    """
    Work-out wether we are being called from inside a docker container

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


def get_docker_tag(faasm_checkout, image_name):
    """
    Given an image name, get the docker tag from the `.env` file in Faasm's
    source

    Parameters:
    - faasm_checkout (str): path to the local checkout of Faasm
    - image_name (str): image name to find. Must be one in
                        {CPP,FAASM,PYTHON}_CLI_IMAGE

    Returns:
    - A string with the corresponding docker image tag
    """
    env_file_path = join(faasm_checkout, ".env")
    with open(env_file_path, "r") as fh:
        env_file = fh.readlines()
        env_file = [line.strip() for line in env_file]

    # Get the actual image tag by finding the right line in the file. We are
    # unncesserily loading all the lines, but we don't care
    image_tag = [line.split("=")[1] for line in env_file if line.startswith(image_name)]
    assert len(image_tag) == 1
    image_tag = image_tag[0]

    return image_tag
