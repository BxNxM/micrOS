#!/bin/bash

# Get command line arguments
CMD_ARGS=${*}
# Get current script path
MY_PATH="$(dirname "${BASH_SOURCE[0]}")"
# Create script global path variables
if [[ "${MY_PATH}" == "." || ${MY_PATH} = /* ]]
then
  venv_path="${MY_PATH}/env/venv"
  env_activate="${venv_path}/bin/activate"
  requirements="${MY_PATH}/env/requirements.txt"
  log_file="${MY_PATH}/micros.log"
else
  venv_path="./${MY_PATH}/env/venv"
  env_activate="./${venv_path}/bin/activate"
  requirements="./${MY_PATH}/env/requirements.txt"
  log_file="./${MY_PATH}/micros.log"
fi

# Calculate if pip install was done once
install_req=0

# Set command line colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

function console_log {
  message=$1
  echo -e "$message"
  echo -e "$message" >> "${log_file}"
}

function venv_create {
    # Check path is exists
    if [[ -d $(dirname "$venv_path") ]]
    then
        if [[ ! -d "$venv_path" ]]
        then
            console_log "${GREEN}    Create venv: $venv_path${NC}"
            python3 -m venv "${venv_path}"
            if [ $? -ne 0 ]; then
                echo -e "${RED}Cannot prepare python venv${NC}"
                exit 1
            fi
            "${venv_path}/bin/python3" -m pip install --upgrade pip
            install_req=1
        else
            install_req=0
        fi
    else
        console_log "${RED}    Invalid path: ${venv_path}${NC}"
    fi
}

function _trim {
  # Strip leading and trailing whitespace from a string
  local var="$*"
  var="${var#"${var%%[![:space:]]*}"}"   # remove leading whitespace characters
  var="${var%"${var##*[![:space:]]}"}"   # remove trailing whitespace characters
  echo -n "$var"
}


function fail_safe_pip_install {
    local req_txt_path="$1"
    local cannot_install_package=()

    while IFS= read -r line; do
        # Strip leading and trailing whitespace from the current line
        pip_package=$(_trim "$line")
        echo -e "Attempt to install: $pip_package"
        python3 -m pip install "$pip_package"
        if [ $? -ne 0 ]; then
            cannot_install_package+=("$pip_package")
        fi
    done < "$req_txt_path"

    # Dependency install check...
    if [ ${#cannot_install_package[@]} -gt 0 ]; then
        echo -e "\n\n======================== ${RED}DEPENDENCY WARNING${NC} =========================="
        echo -e "${RED}WARNING${NC}: cannot install package(s): ${cannot_install_package}"
        for failed_pack in "${cannot_install_package[@]}"; do
          # Check if "mpy-cross" is in unable-to-install list
          if [[ $failed_pack == *"mpy-cross"* ]]; then
            echo "---> ${RED}No mpy-cross available...${NC}"
          fi
        done
        echo -e "======================================================================\n\n"
    fi
}

function venv_requirements {
    if [[ -f "${requirements}" ]]
    then
        console_log "${GREEN}    Install requirements: ${requirements}${NC}"
        # python3 -m pip install -r "${requirements}"
        # failsafe package install:
        fail_safe_pip_install "${requirements}"
    else
        console_log "${RED}    No requirements file: ${requirements}${NC}"
    fi
}

#################################
#               VENV            #
#################################

# Create virtual environment
console_log "${GREEN}CREATE MICROS DEVTOOLKIT VIRTUAL ENVIRONMENT${NC}"
venv_create


# Check if venv already active & auto deactivate
if [[ -n "${VIRTUAL_ENV}" ]]
then
    . "deactivate"
fi

# Activate venv
console_log "${GREEN}ACTIVATE VIRTUAL ENVIRONMENT:${NC} ${env_activate}"
source "${env_activate}"

# Install requirements
if [[ -n "${VIRTUAL_ENV}" && "${install_req}" -eq 1 ]]
then
    console_log "${GREEN}    Install requirements: ${VIRTUAL_ENV}${NC}"
    venv_requirements
else
    console_log "    Venv already prepared and active: ${VIRTUAL_ENV}"
fi

#################################
#           DEVTOOLKIT          #
#################################

function help {
    echo -e "\n============================================================="
    echo -e "==                  HELP MSG FOR magic.bash                =="
    echo -e "============================================================="
    echo -e "env        :activate python virtual environment and exit"
    echo -e "gateway    :start micrOS gateway service over devToolKit.py"
    echo -e "sim        :start micrOS simulator on host OS"
    echo -e "gitclean   :cleans untracked files, with -f cleans ignored too"
    echo -e "<no param> :run devToolKit.py without params -> GUI"
    echo -e "distribute :create and distribute pip package"
    echo -e "install    :install micrOS DevToolKit with setup.py from repo\n"
}


# CMD ARGUMENT: env
if [[ -n "${CMD_ARGS[0]}" ]]
then

  if [[ "${CMD_ARGS[0]}" == "env" ]]
  then
      console_log "[env] Source env only, skip devToolKit start"
  elif [[ "${CMD_ARGS[0]}" == "install" ]]
    then
        echo -e "Install dev package from setup.py"
        pip3 install -e .
        exit 0
  elif [[ "${CMD_ARGS[0]}" == "gateway" ]]
  then
      # Start devToolKit.py gateway service
      console_log "[gateway] Source env and start rest api server aka gateway"
      if [[ "$OSTYPE" == "linux"* ]]
      then
          # TODO [!!!!] Raspbian workaround
          console_log "[gateway][!!!] Raspberry workaround: venc deactivate and use python3"
          deactivate
          python3 "${MY_PATH}/devToolKit.py" -gw | tee -a "${log_file}"
      else
          # Execution in virtual env
          python3 "${MY_PATH}/devToolKit.py" -gw | tee -a "${log_file}"
      fi
  elif [[ "${CMD_ARGS[0]}" == "gitclean" ]]
  then
      pushd "${MY_PATH}"
      console_log "[gitclean] Clean untracked files: git clean -fd"
      git clean -fd
      if [[ -n "${CMD_ARGS[1]}" && "${CMD_ARGS[1]}" == "all" ]]
      then
        console_log "\t[gitclean all] + gitignored files: git clean -fdx"
        git clean -fdx
      fi
      popd
  elif [[ "${CMD_ARGS[0]}" == "sim" ]]
  then
      console_log "[sim] Start micrOS simulator"
      if [[ "$OSTYPE" == "linux"* ]]
      then
          # TODO [!!!!] Raspbian workaround
          console_log "[simulator][!!!] Raspberry workaround: venc deactivate and use python3"
          deactivate
          python3 "${MY_PATH}/devToolKit.py" -sim
       else
          # Execution in virtual env
          python3 "${MY_PATH}/devToolKit.py" -sim
       fi
    elif [[ "${CMD_ARGS[0]}" == "--help" || "${CMD_ARGS[0]}" == "-h" || "${CMD_ARGS[0]}" == "help" ]]
    then
      help
    elif [[ "${CMD_ARGS[0]}" == "distribute" ]]
    then
        echo -e "Create a source distribution"
        if python3 setup.py sdist;
        then
            echo -e "Create a wheel distribution."
            if python3 setup.py bdist_wheel;
            then
                twine upload -u "__token__" -p "$(cat .pypi-secret)" dist/* --verbose
            fi
        fi
    fi
else
    help
    # Start devToolKit.py GUI
    console_log "Start devToolKit GUI: ${MY_PATH}/devToolKit.py"
    python3 "${MY_PATH}/devToolKit.py"
fi
