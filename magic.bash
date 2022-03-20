#!/bin/bash

CMD_ARGS="${@}"
venv_path="./env/venv"
activate="${venv_path}/bin/activate"
requirements="./env/requirements.txt"
install_req=0

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color


function venv_create {
    # Set @ as the delimiter
    IFS='/'
    read -ra list <<< "$venv_path"

    if [[ -d "./${list[1]}" ]]
    then
        if [[ ! -d "${venv_path}" ]]
        then
            echo -e "${GREEN}Create venv: ./${list[1]}/${list[2]}${NC}"
            python3.8 -m venv "${venv_path}"
            "${venv_path}/bin/python3.8" -m pip install --upgrade pip
            install_req=1
        else
            install_req=0
        fi
    else
        echo -e "${RED}Invalid path: ${venv_path}${NC}"
    fi
}

function venv_requirements {
    if [[ -f "${requirements}" ]]
    then
        echo -e "${GREEN}Install requirements: ${requirements}${NC}"
        python3.8 -m pip install -r "${requirements}"
    else
        echo -e "${RED}No requirements file: ${requirements}${NC}"
    fi
}

#################################
#               VENV            #
#################################

echo -e "${GREEN}CREATE MICROS DEVTOOLKIT VIRTUAL ENVIRONMENT${NC}"
venv_create


# Check if venv already active
if [[ -n "${VIRTUAL_ENV}" ]]
then
    . "deactivate"
fi

# Activate venv
echo -e "${GREEN}ACTIVET VIRTUAL ENVIRONMENT: ${activate}${NC}"
. "${activate}"

# Install requirements
if [[ -n "${VIRTUAL_ENV}" && "${install_req}" -eq 1 ]]
then
    echo -e "${GREEN}Virtual env active: ${VIRTUAL_ENV}${NC}"
    venv_requirements
else
    echo -e "Venv setup skipped: ${VIRTUAL_ENV}"
fi

#################################
#           DEVTOOLKIT          #
#################################


# CMD ARGUMENT: env
if [[ -n ${CMD_ARGS[0]} && "${CMD_ARGS[0]}" == "env" ]]
then
    echo -e "Source env only, skip devToolKit load"
else
    # Start devToolKit.py
    echo -e "Start devToolKit"
    python3.8 devToolKit.py
fi

