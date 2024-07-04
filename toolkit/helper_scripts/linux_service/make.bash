#!/bin/bash

SERVICE_NAME="micros-gw.service"
TEMPLATE_PATH="./template_${SERVICE_NAME}"
SYSTEMD_PATH="/lib/systemd/system/"

function check_service() {
  echo -e "Check service ${SERVICE_NAME}"
  sudo systemctl status "$SERVICE_NAME"
}

function validate_command() {
  local command_variants=("/usr/bin/python3 -m devToolKit")
  command_variants+=("/usr/bin/python3 -m devToolKit.py")
  command_variants+=("devToolKit.py")
  command_variants+=("/usr/bin/python3 /home/${USER}/micrOS/devToolKit.py")
  for cmd in "${command_variants[@]}"
  do
    cmd_help="${cmd} --light --help"
    $cmd_help >> "./setup.log"
    exitcode=$?
    if [[ $exitcode == 0 ]]
    then
      # Valid command
      echo -e "VALID command: ${cmd} | ${exitcode}" >> "./setup.log"
      echo "${cmd}"
      break
    else
      echo -e "INVALID command: ${cmd} | ${exitcode}" >> "./setup.log"
    fi
  done
}

function prepare_template() {
  read -sp "Set gateway password: " password
  while [[ -z "$password" ]]; do
    echo -e ""
    read -sp "Set gateway password: " password
  done

  local target="./${SERVICE_NAME}"
  local user="$USER"
  local command=$(validate_command)
  if [[ -z "$command" ]]; then
    echo -e "Cannot find valid command... check setup.log"
    exit 1
  fi
  local replace_user="s/<user>/${user}/g"
  local replace_password="s/<password>/${password}/g"
  local replace_command="s/<command>/${command} --light -gw/g"

  echo -e "PREPARE ${target}: replace <user> <password> <command>"
  cat "${TEMPLATE_PATH}" | sed "$replace_user" | sed "$replace_password" | sed "$replace_command" > "./${target}"
}

function create_service() {
  echo -e "sudo cp micros-gw.service /lib/systemd/system/"
  sudo cp micros-gw.service /lib/systemd/system/
  if [[ $? != 0 ]]; then
    echo -e "|- error"
    exit 1
  fi
  echo -e "sudo systemctl start micros-gw.service"
  sudo systemctl start micros-gw.service
  if [[ $? != 0 ]]; then
    echo -e "|- error"
    exit 1
  fi
  echo -e "sudo systemctl enable micros-gw.service"
  sudo systemctl enable micros-gw.service
  if [[ $? != 0 ]]; then
    echo -e "|- error"
    exit 1
  fi
  echo -e "sudo systemctl status micros-gw.service"
  sudo systemctl status micros-gw.service
  if [[ $? != 0 ]]; then
    echo -e "|- error"
    exit 1
  fi
}


function main() {
  echo -e "Init service install LOG" > "./setup.log"
  if [[ -d "${SYSTEMD_PATH}" ]]
  then
    echo -e "=== ${SERVICE_NAME} ==="
    local exists=$(ls -1 "${SYSTEMD_PATH}" | grep "${SERVICE_NAME}")
    if [ -n "${exists}" ]
    then
      echo -e "|-- already exists"
      check_service
    else
      echo -e "|-- not exists"
      prepare_template
      create_service
    fi
  else
    echo -e "SYSTEMD PATH NOT FOUND: ${SYSTEMD_PATH}"
    exit 1
  fi
}

### CALL MAIN ###
main
exit 0