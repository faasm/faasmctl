# Faasm CTL [![Tests](https://github.com/faasm/faasmctl/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/faasm/faasmctl/actions/workflows/tests.yml)

`faasmctl` is a command line script to deploy, manage, and interact with a
running [Faasm](https://github.com/faasm/faasm) cluster.

## Install

To install `faasmctl` you need a working `pip` (virtual-)environment. Then:

```bash
pip install faasmctl==0.1.0
```

## Usage

`faasmctl` aggregates tasks related to deploying, managing, and interacting
with running Faasm clusters. You can list all the available tasks with a
short description using:

```bash
faasmctl -l
```

## Development

To hack around, and develop `faasmctl` itself, you just need to activate the
development virtual environment:

```bash
source ./bin/workon.sh
inv -l
```
