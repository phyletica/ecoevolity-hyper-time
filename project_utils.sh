#! /bin/bash

ht_ecoevolity_commit="c933f15b"

ht_conda_env_name="hyper-time"

ht_conda_exe="conda"

if command -v micromamba >/dev/null 2>&1
then
    ht_conda_exe="micromamba"
elif command -v mamba >/dev/null 2>&1
then
    ht_conda_exe="mamba"
fi
