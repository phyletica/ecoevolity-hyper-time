#! /bin/bash

set -e

source ../project_utils.sh

config_path="../ecoevolity-configs/dpp-conc-hypergamma-4-10-time-hyperexp-02-pairs-20-sites-20000.yml"

echo "Checking prior sampling for '$(basename $config_path)'..."
"$ht_conda_exe" run -n hyper-time pyco-eco-vet-prior \
    --seed 1 \
    --ecoevolity-dir ../bin \
    --number-of-runs 40 \
    --number-of-procs 8 \
    --burnin 501 \
    --step 4 \
    --sparse-pop-size-plotting \
    --output-dir ../prior-sampling-output \
    "$config_path"

config_path="../ecoevolity-configs/dpp-conc-hypergamma-4-10-time-hyperunif-02-pairs-20-sites-20000.yml"

# The uniform prior on divergence times with a uniform hyper prior on the max
# parameter is difficult to sample with MCMC without any data, so we need a
# large burnin and thinning of the MCMC samples.
echo ""
echo "Checking prior sampling for '$(basename $config_path)'..."
"$ht_conda_exe" run -n hyper-time pyco-eco-vet-prior \
    --seed 1 \
    --ecoevolity-dir ../bin \
    --number-of-runs 200 \
    --number-of-procs 8 \
    --burnin 1001 \
    --step 10 \
    --sparse-pop-size-plotting \
    --output-dir ../prior-sampling-output \
    "$config_path"
