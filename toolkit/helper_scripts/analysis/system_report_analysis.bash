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
      analysis_content=$(git show "$commit_hash:micrOS/release_info/micrOS_ReleaseInfo/system_analysis_sum.json")
      version=$(echo "$analysis_content" | jq -r '.summary.version')
      if [[ -z "$version" ]]; then
        debug_print "Version extraction failed or is empty.: $commit_hash\n\t$commit_message\n\t????????\n$analysis_content"
        continue
      fi
      # Create target path
      save_version_json="$analysis_workdir/$version.json"
      save_version_meta="$analysis_workdir/$version.meta"
      debug_print "[${changes_cnt}] Change in system_analysis_sum.json - Commit: $commit_hash\n\t${commit_message}\n\tSave to $save_version_json"
      echo "${analysis_content}" > "$save_version_json"
      echo "${commit_hash}: ${commit_message}" > "$save_version_meta"
      debug_print "\n==============================\n"
      let changes_cnt+=1
  done
  save_release_versions="$analysis_workdir/release_versions.info"
  release_versions=($(git tag --sort=-creatordate | grep '^v'))
  echo "${release_versions[*]}" > "$save_release_versions"
  echo -e "Official releases: ${release_versions[@]} >save> $save_release_versions"
  popd
}

function get_contributions {

    echo -e "Get contributors and contribution scores"
    pushd "${SCRIPT_DIR}"
    python3 contributors.py
    exitcode=$?
    popd

    if [[ "$exitcode" == "0" ]]
    then
        echo -e "\tOK"
    else
        echo -e "\tNOK"
    fi
}

function get_system_test_metrics {
  # REPOROOT/micrOS/release_info/micrOS_ReleaseInfo/devices_system_metrics.json
  METRICS_PATH="${SCRIPT_DIR}/../../../micrOS/release_info/micrOS_ReleaseInfo/devices_system_metrics.json"
  if [ -e "$METRICS_PATH" ]
  then
    echo -e "COPY metrics to work analysis_workdir: $METRICS_PATH"
    pushd "${SCRIPT_DIR}"
    cp "$METRICS_PATH" "./analysis_workdir"
    popd
  else
    echo -e "NO SYS METRICS WAS FOUND: $METRICS_PATH"
  fi

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

# Data collection
collect_sys_analysis_resources
get_contributions
get_system_test_metrics

# Visualize data
visualize
