from random import randint


def generate_gid():
    """
    Generate a random 6 digit integer
    """
    return randint(100000, 999999)
