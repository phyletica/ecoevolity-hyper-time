#! /bin/bash

set -e

label_array=()
convert_labels_to_array() {
    local concat=""
    local t=""
    label_array=()

    for word in $@
    do
        local len=`expr "$word" : '.*"'`

        [ "$len" -eq 1 ] && concat="true"

        if [ "$concat" ]
        then
            t+=" $word"
        else
            word=${word#\"}
            word=${word%\"}
            label_array+=("$word")
        fi

        if [ "$concat" -a "$len" -gt 1 ]
        then
            t=${t# }
            t=${t#\"}
            t=${t%\"}
            label_array+=("$t")
            t=""
            concat=""
        fi
    done
}

project_dir="../.."
output_dir="${project_dir}/gecko-ecoevolity-output"
sumco_exe_path="${project_dir}/bin/sumcoevolity"

source "${project_dir}/project_utils.sh"

config_prefices=(
    "geckos-combined"
    "geckos-combined-hyper-time"
)
burnin_values=(
    101
    101
)

labels='-l "Bohol0" "Bohol"
-l "CamiguinSur0" "Camiguin Sur"
-l "root-Bohol0" "Bohol-Camiguin Sur Root"
-l "Palawan1" "Palawan"
-l "Kinabalu1" "Borneo"
-l "root-Palawan1" "Palawan-Borneo Root"
-l "Samar2" "Samar"
-l "Leyte2" "Leyte"
-l "root-Samar2" "Samar-Leyte Root"
-l "Luzon3" "Luzon 1"
-l "BabuyanClaro3" "Babuyan Claro"
-l "root-Luzon3" "Luzon-Babuyan Claro Root"
-l "Luzon4" "Luzon 2"
-l "CamiguinNorte4" "Camiguin Norte"
-l "root-Luzon4" "Luzon-Camiguin Norte Root"
-l "Polillo5" "Polillo"
-l "Luzon5" "Luzon 3"
-l "root-Polillo5" "Polillo-Luzon Root"
-l "Panay6" "Panay"
-l "Negros6" "Negros"
-l "root-Panay6" "Panay-Negros Root"
-l "Sibuyan7" "Sibuyan"
-l "Tablas7" "Tablas"
-l "root-Sibuyan7" "Sibuyan-Tablas Root"
-l "BabuyanClaro8" "Babuyan Claro"
-l "Calayan8" "Calayan"
-l "root-BabuyanClaro8" "Babuyan Claro-Calayan Root"
-l "SouthGigante9" "S. Gigante"
-l "NorthGigante9" "N. Gigante"
-l "root-SouthGigante9" "S. Gigante-N. Gigante Root"
-l "Lubang11" "Lubang"
-l "Luzon11" "Luzon"
-l "root-Lubang11" "Lubang-Luzon Root"
-l "MaestreDeCampo12" "Maestre De Campo"
-l "Masbate12" "Masbate"
-l "root-MaestreDeCampo12" "Maestre De Campo-Masbate Root"
-l "Panay13" "Panay 1"
-l "Masbate13" "Masbate"
-l "root-Panay13" "Panay-Masbate Root"
-l "Negros14" "Negros"
-l "Panay14" "Panay 2"
-l "root-Negros14" "Negros-Panay Root"
-l "Sabtang15" "Sabtang"
-l "Batan15" "Batan"
-l "root-Sabtang15" "Sabtang-Batan Root"
-l "Romblon16" "Romblon"
-l "Tablas16" "Tablas"
-l "root-Romblon16" "Romblon-Tablas Root"
-l "CamiguinNorte17" "Camiguin Norte"
-l "Dalupiri17" "Dalupiri"
-l "root-CamiguinNorte17" "Camiguin Norte-Dalupiri Root"'

convert_labels_to_array $labels

for i in "${!config_prefices[@]}"
do
    config_prefix="${config_prefices[i]}"
    burnin="${burnin_values[i]}"
    config_path="${project_dir}/ecoevolity-configs/${config_prefix}.yml"

    log_paths="$(find "$output_dir" -maxdepth 1 -name "run-??-threads-*-${config_prefix}-state-run-1.log")"
    gzipped_log_paths="$(find "$output_dir" -maxdepth 1 -name "run-??-threads-*-${config_prefix}-state-run-1.log.gz")"

    if [ -z "$log_paths" ]
    then
        if [ -n "$gzipped_log_paths" ]
        then
            gzip -d -k $gzipped_log_paths
            log_paths="$(find "$output_dir" -maxdepth 1 -name "run-??-threads-*-${config_prefix}-state-run-1.log")"
        else
            echo "No state log files found for $config_prefix; Skipping!"
            continue
        fi
    fi
    if [ -z "$log_paths" ]
    then
        echo "Problem decompressing gzipped stated log files for $config_prefix; Skipping!"
        continue
    fi

    "$ht_conda_exe" run -n "$ht_conda_env_name" pyco-sumtimes \
        -f -b "$burnin" "${label_array[@]}" \
        --violin \
        -p "${output_dir}/pyco-sumtimes-${config_prefix}-" \
        $log_paths

    sumco_out_path="${output_dir}/sumcoevolity-${config_prefix}-sumcoevolity-results-nevents.txt"

    if [ ! -e "$sumco_out_path" ]
    then
        "$ht_conda_exe" run -n "$ht_conda_env_name" "$sumco_exe_path" \
            -b "$burnin" \
            -n 1000000 \
            -p "${output_dir}/sumcoevolity-${config_prefix}-" \
            -c "$config_path" \
            $log_paths
    fi

    "$ht_conda_exe" run -n "$ht_conda_env_name" pyco-sumevents \
        -f -p "${output_dir}/pyco-sumevents-${config_prefix}-" \
        "$sumco_out_path"
done
