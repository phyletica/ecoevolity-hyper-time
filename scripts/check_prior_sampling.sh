#! /bin/bash

set -e

source ../project_utils.sh

for config_path in ../ecoevolity-configs/dpp-conc-hypergamma-4-10-time-hyper*.yml
do
    echo "Checking prior sampling for '$(basename $config_path)'..."
    "$ht_conda_exe" run -n hyper-time python check_prior_sampling.py \
        --seed 123 \
        --ecoevolity-dir ../bin \
        --number-of-runs 20 \
        --number-of-procs 8 \
        --output-dir ../prior-sampling-output \
        "$config_path"
done 1>check_prior_sampling.sh.out 2>&1
