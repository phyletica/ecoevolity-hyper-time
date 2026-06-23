#! /bin/bash

set -e

project_dir="../.."
output_dir="${project_dir}/gecko-ecoevolity-output"

source "${project_dir}/project_utils.sh"

for config_prefix in "geckos-combined" "geckos-combined-hyper-time"
do
    log_paths="$(find "$output_dir" -maxdepth 1 -name "run-??-threads-*-${config_prefix}-state-run-1.log")"
    gzipped_log_paths="$(find "$output_dir" -maxdepth 1 -name "run-??-threads-*-${config_prefix}-state-run-1.log.gz")"

    output_table_path="${output_dir}/pyco-sumchains-${config_prefix}-table.tsv"

    if [ -n "$gzipped_log_paths" ]
    then
        echo ""
        echo Running: "$ht_conda_exe" run -n "$ht_conda_env_name" pyco-sumchains $gzipped_log_paths \1\>"$output_table_path"
        echo ""
        "$ht_conda_exe" run -n "$ht_conda_env_name" pyco-sumchains $gzipped_log_paths 1>"$output_table_path"
    elif [ -n "$log_paths" ]
    then
        echo ""
        echo Running: "$ht_conda_exe" run -n "$ht_conda_env_name" pyco-sumchains $log_paths \1\>"$output_table_path"
        echo ""
        "$ht_conda_exe" run -n "$ht_conda_env_name" pyco-sumchains $log_paths 1>"$output_table_path"
    else
        echo "No state log files found for $config_prefix; Skipping!"
    fi
done
