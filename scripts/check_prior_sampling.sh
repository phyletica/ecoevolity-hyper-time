#! /bin/bash

set -e

source ../project_utils.sh

# The uniform prior on divergence times with a uniform hyper prior on the max
# parameter is difficult to sample with MCMC without any data, so we need a
# large burnin and thinning of the MCMC samples.
for config_path in ../ecoevolity-configs/dpp-conc-hypergamma-4-10-time-hyper*.yml
do
    echo "Checking prior sampling for '$(basename $config_path)'..."
    "$ht_conda_exe" run -n hyper-time pyco-eco-vet-prior \
        --seed 123 \
        --ecoevolity-dir ../bin \
        --number-of-runs 400 \
        --number-of-procs 8 \
        --burnin 801 \
        --step 6 \
        --sparse-pop-size-plotting \
        --output-dir ../prior-sampling-output \
        "$config_path"
done 1>check_prior_sampling.sh.out 2>&1
