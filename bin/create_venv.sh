#!/bin/bash

set -e

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]:-${(%):-%x}}" )" >/dev/null 2>&1 && pwd )"
PROJ_ROOT=${THIS_DIR}/..

PIP=${VENV_PATH}/bin/pip3

function pip_cmd {
    source ${VENV_PATH}/bin/activate && ${PIP} "$@"
}

pushd ${PROJ_ROOT} >> /dev/null

if [ ! -d ${VENV_PATH} ]; then
    python3 -m venv ${VENV_PATH}
fi

pip_cmd install -U pip
pip_cmd install -r ${PROJ_ROOT}/dev_requirements.txt

popd >> /dev/null
