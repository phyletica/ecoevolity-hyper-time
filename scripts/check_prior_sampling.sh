#! /bin/bash

set -e

source ../project_utils.sh

"$ht_conda_exe" run -n hyper-time python check_prior_sampling.py \
    --seed 123
    --ecoevolity-dir ../bin \
    --number-of-runs 20 \
    --number-of-procs 8 \
    --output-dir ../prior-sampling-output \
    ../ecoevolity-configs/dpp-conc-hypergamma-4-10-time-hyperexp-02-pairs-20-sites-20000.yml 1>check_prior_sampling.sh.out 2>&1
