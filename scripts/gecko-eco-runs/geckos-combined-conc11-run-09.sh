#! /bin/bash

set -e

project_dir="../.."

source "${project_dir}/project_utils.sh"

run=09
nthreads=10
config_file_prefix="geckos-combined-conc11"

exe_path="${project_dir}/bin/ecoevolity"
config_path="${project_dir}/ecoevolity-configs/${config_file_prefix}.yml"

if [ ! -x "$exe_path" ]
then
    echo "ERROR: No executable '${exe_path}'."
    echo "       You probably need to run the project setup script."
    exit 1
fi

output_dir="${project_dir}/gecko-ecoevolity-output"

if [ ! -e "$output_dir" ]
then
    mkdir "$output_dir"
fi

prefix="${output_dir}/run-${run}-threads-${nthreads}-"
out_path="${prefix}${config_file_prefix}.out"

"$ht_conda_exe" run -n "$ht_conda_env_name" "$exe_path" \
    --seed $run \
    --nthreads "$nthreads" \
    --prefix "$prefix" \
    --relax-missing-sites \
    --relax-constant-sites \
    --relax-triallelic-sites \
    "$config_path" 1>"$out_path" 2>&1
