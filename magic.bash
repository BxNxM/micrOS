#!/bin/bash

#########################################################
#                       magic.bash                      #
#                                                       #
#       Development environment generator               #
#       - python virtual environment: ./env/venv        #
#       - bash and zsh support                          #
#       - for more info: ./magic.bash -h                #
#       - create venv only: source magic.bash env       #
#########################################################


# Ensure compatibility with both Bash and Zsh
if [ -n "$ZSH_VERSION" ]; then
  # Enable Bash-like zero-based indexing in Zsh
  setopt KSH_ARRAYS
fi

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

# Set command line colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color
NEW_ENV=false

function console_log {
  message=$1
  echo -e "$message"
  echo -e "$message" >> "${log_file}"
}

function venv_create {
    # Check venv path is exists and dir - if nodir then create venv
    if [[ ! -d "$venv_path" ]]
    then
        console_log "${GREEN}\t\tCreate VENV: ${venv_path}${NC}"
        python3 -m venv "${venv_path}"
        if [ $? -ne 0 ]; then
          echo -e "${RED}\t\tCannot prepare python VENV${NC}"
          exit 1
        fi
        "${venv_path}/bin/python3" -m pip install --upgrade pip
        NEW_ENV=true
    else
        console_log "${GREEN}\t\tVENV already exists: ${venv_path}${NC}"
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
        if [[ "${NEW_ENV}" == "true" ]]; then
          console_log "${GREEN}\t\tInstall requirements: ${requirements}${NC}"
          # python3 -m pip install -r "${requirements}"
          # failsafe package install:
          fail_safe_pip_install "${requirements}"
        else
          console_log "${GREEN}\t\tRequirements was already installed.${NC}"
        fi
    else
        console_log "${RED}\t\tNo requirements file: ${requirements}${NC}"
    fi
}


function venv_recreate {
  if [[ -d "$venv_path" ]]; then
    echo -e "[i] RECREATE VENV"
    rm -r "$venv_path"
  fi
}

#################################
#               VENV            #
#################################

function venv_main {
  # Create virtual environment
  console_log "${GREEN}MICROS DEVTOOLKIT VIRTUAL ENVIRONMENT${NC}"

  # Check if venv already active if not do actions... activate
  if [[ -n "${VIRTUAL_ENV}" ]]; then
    console_log "\t\tVenv already prepared and active: ${VIRTUAL_ENV}"
  else
    console_log "${GREEN}CREATE VIRTUAL ENVIRONMENT:${NC}"
    venv_create
    console_log "${GREEN}ACTIVATE VIRTUAL ENVIRONMENT:${NC} ${env_activate}"
    source "${env_activate}"
    console_log "${GREEN}INSTALL REQUIREMENTS:${NC} ${env_activate}"
    venv_requirements
  fi
}

#################################
#           DEVTOOLKIT          #
#################################

function help {
    echo -e "\n============================================================="
    echo -e "==                  HELP MSG FOR magic.bash                =="
    echo -e "============================================================="
    echo -e "env        :activate python virtual environment and exit"
    echo -e "recreate   :delete /env/venv and recreate venv based on requirements.txt"
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
  echo -e "params: ${CMD_ARGS}"

  # Check recreation is requested or not - optional cleanup
  if [[ "${CMD_ARGS[0]}" == "recreate" ]]
  then
    venv_recreate
  fi

  # Call virtual environment creation main function
  venv_main

  # Additional magic.bash commands
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
    venv_main
    help
    # Start devToolKit.py GUI
    console_log "Start devToolKit GUI: ${MY_PATH}/devToolKit.py"
    python3 "${MY_PATH}/devToolKit.py"
fi
