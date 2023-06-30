from invoke import Program
from faasmctl.tasks import task_ns
from faasmctl.util.version import get_version


def main():
    program = Program(
        name="faasmctl",
        binary="faasmctl",
        binary_names=["faasmctl"],
        namespace=task_ns,
        version=get_version(),
    )
    program.run()
