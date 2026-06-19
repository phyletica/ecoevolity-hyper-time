#! /bin/bash

set -e

# Make sure we leave caller back from whence they called
current_dir="$(pwd)"
clean_up() {
    cd "$current_dir"
}
trap clean_up EXIT

# Get path to directory of this script
script_dir="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
project_dir="$(dirname "$script_dir")"
bin_dir="${project_dir}/bin"
data_dir="${project_dir}/data"
config_dir="${project_dir}/ecoevolity-configs"
mu_rates_path="${data_dir}/mutation_rates.yml"

config_converter="${script_dir}/convert_eco_config.py"
mu_rate_getter="${script_dir}/get_gecko_mutation_rates.py"

source "${project_dir}/project_utils.sh"

if [ ! -e "$mu_rates_path" ]
then
    "$ht_conda_exe" run -n "$ht_conda_env_name" python "$mu_rate_getter" "$mu_rates_path"
fi

gekgo_zip_url='https://zenodo.org/records/5162085/files/phyletica/gekgo-v2.0.0.zip'
gekgo_dest_dir="${project_dir}/gekgo-v2.0.0"
gekgo_zip_path="${gekgo_dest_dir}.zip"

if [ ! -e "$gekgo_dest_dir" ]
then
    if [ ! -e "$gekgo_zip_path" ]
    then
        echo "Downloading gekgo project archive..."
        curl -L -o "$gekgo_zip_path" "$gekgo_zip_url"
    fi

    echo "Extracting gekgo project archive..."
    unzip -q "$gekgo_zip_path" -d "$gekgo_dest_dir"
fi

gekgo_dir_name="$(ls "$gekgo_dest_dir")"
gekgo_dir="${gekgo_dest_dir}/${gekgo_dir_name}"

eco_config_dir="${gekgo_dir}/data/genomes/msg/ecoevolity-configs"
eco_align_dir="${gekgo_dir}/data/genomes/msg/alignments"

config_names=(
    "cyrtodactylus-rate200.yml"
    "gekko-rate200.yml"
)

for conf_name in "${config_names[@]}"
do
    echo "Converting nex to yml for \"$conf_name\""
    "${bin_dir}/nex2yml" --relax-missing-sites --relax-triallelic-sites "${eco_config_dir}/${conf_name}"

    echo "Moving yaml data files into data directory..."
    mv "${eco_align_dir}/"*.yml "$data_dir"

    out_conf_name="${conf_name/-rate200/-hyper-time}"

    echo "Converting config file into config directory..."
    sed -e "s/alignments/data/g" -e "s/\.nex/\.nex\.yml/g" "${eco_config_dir}/${conf_name}" | \
        "$ht_conda_exe" run -n "$ht_conda_env_name" python "$config_converter" \
        > "${config_dir}/${out_conf_name}"
done

echo ""
echo "Gecko data successfully downloaded and converted"
echo "You can now remove the downloaded data archive using this command:"
echo "    rm -r $gekgo_dest_dir $gekgo_zip_path"
echo ""
