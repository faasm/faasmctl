from random import randint


def generate_gid():
    """
    Generate a random 6 digit integer
    """
    return randint(1000000000, 9999999999)
