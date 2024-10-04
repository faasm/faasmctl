# Faasm CTL [![Tests](https://github.com/faasm/faasmctl/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/faasm/faasmctl/actions/workflows/tests.yml) ![PyPI](https://img.shields.io/pypi/v/faasmctl)

`faasmctl` is a command line script to deploy, manage, and interact with a
running [Faasm](https://github.com/faasm/faasm) cluster.

## Install

To install `faasmctl` you need a working `pip` (virtual-)environment. Then:

```bash
pip install faasmctl==0.47.1
```

## Usage

`faasmctl` aggregates tasks related to deploying, managing, and interacting
with running Faasm clusters. You can list all the available tasks with a
short description using:

```bash
faasmctl -l
```

## Further Reading

For any further reading, check the [`docs`](./docs) directory.
