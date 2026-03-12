#! /bin/bash

set -e

# Make sure we leave caller back from whence they called
current_dir="$(pwd)"
clean_up() {
    cd "$current_dir"
}
trap clean_up EXIT

# Get path to directory of this script
project_dir="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

source "${project_dir}/project_utils.sh"

if "$ht_conda_exe" list --name "$ht_conda_env_name" >/dev/null 2>&1
then
    echo ""
    echo "The project's conda environment '$ht_conda_env_name' already exists,"
    echo "so skipping the creation of the conda environment!"
    echo "If you would like to rebuild the project's conda environment,"
    echo "please remove it with the following command and then re-run this"
    echo "script:"
    echo "  $ht_conda_exe env remove -n $ht_conda_env_name"
    echo ""
else
    conda_env_path="${project_dir}/conda-env.yml"
    
    echo ""
    echo "Creating conda environment using command:"
    echo '  '"$ht_conda_exe" env create --name "$ht_conda_env_name" --file "$conda_env_path" --yes
    echo ""
    "$ht_conda_exe" env create --name "$ht_conda_env_name" --file "$conda_env_path" --yes
fi

echo "Cloning and building ecoevolity..."
(
    cd "$project_dir"
    "$ht_conda_exe" run -n "$ht_conda_env_name" git clone --recurse-submodules https://github.com/phyletica/ecoevolity.git
    cd ecoevolity
    "$ht_conda_exe" run -n "$ht_conda_env_name" git checkout -b project-env "$ht_ecoevolity_commit"
    "$ht_conda_exe" run -n "$ht_conda_env_name" ./build.sh --threads --prefix "$project_dir"
    echo "    Commit $ht_ecoevolity_commit of ecoevolity successfully built and installed"
)
echo ""
echo "Ecoevolity was successfully installed in './bin'"
echo "You can now remove the ecoevolity directory using the command:"
echo "    rm -rf ${project_dir}/ecoevolity"
