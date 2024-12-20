#!/bin/bash

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
DEBUG_PRINT=true


function debug_print {
  msg="${1}"
  if [[ "${DEBUG_PRINT}" == "true" ]]
  then
    echo -e "${msg}"
  fi

}

function collect_sys_analysis_resources() {
  analysis_workdir="${SCRIPT_DIR}/analysis_workdir"
  # Prepare workdir
  if [[ -d "${analysis_workdir}" ]]
  then
    echo -e "[prepare] Delete: rm -r ${analysis_workdir}"
    rm -r "${analysis_workdir}"
  fi
  echo -e "[prepare] Create work dir: mkdir ${analysis_workdir}"
  mkdir "${analysis_workdir}"

  # Go to the repository's root directory -  get changes
  pushd "${SCRIPT_DIR}/../../../"
  changes_cnt=0
  git log --pretty=format:"%H %s" -- micrOS/release_info/micrOS_ReleaseInfo/system_analysis_sum.json \
  | while read commit_hash commit_message; do
      # Extract the version from the JSON
      version=$(echo "$analysis_content" | jq -r '.summary.version')
      # Create target path
      save_version_json="$analysis_workdir/$version.json"
      save_version_meta="$analysis_workdir/$version.meta"
      debug_print "[${changes_cnt}] Change in system_analysis_sum.json - Commit: $commit_hash\n\t${commit_message}\n\tSave to $save_version_json
"
      analysis_content=$(git show "$commit_hash:micrOS/release_info/micrOS_ReleaseInfo/system_analysis_sum.json")
      echo "${analysis_content}" > "$save_version_json"
      echo "${commit_hash}: ${commit_message}" > "$save_version_meta"
      debug_print "\n==============================\n"
      let changes_cnt+=1
  done
  popd
}


function visualize {
    debug_print "Generate visualization pdf"
    pushd "${SCRIPT_DIR}"
    python "${SCRIPT_DIR}/visualize_summary.py"
    exitcode=$?
    popd

    if [[ "$exitcode" == "0" ]]
    then
        open "${SCRIPT_DIR}/timeline_visualization.pdf"
    fi
}

############### MAIN #################
if ! command -v git &> /dev/null; then
  echo "Error: git is not installed."
  exit 1
fi
if ! command -v jq &> /dev/null; then
  echo "Error: jq is not installed."
  exit 1
fi

collect_sys_analysis_resources
visualize

