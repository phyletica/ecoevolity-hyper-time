#! /bin/bash

set -e

source ../project_utils.sh

"$ht_conda_exe" run -n "$ht_conda_env_name" pyco-eco-analyze-sims \
    --ecoevolity-dir ../bin \
    --number-of-procs 40 \
    ../exp-hyperprior-sim-study/simulation-data.json \
    1>exp-hp-sim-study-analyze-sims.sh.out 2>&1
