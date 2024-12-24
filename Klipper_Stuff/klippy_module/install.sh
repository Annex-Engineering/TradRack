#!/bin/bash

set -e

branch=${1:-main}
module_dir=Klipper_Stuff/klippy_module
script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
repo_source=https://github.com/Annex-Engineering/TradRack.git
repo_dir=trad_rack_klippy_module

if [[ "$script_dir" == *$module_dir ]]; then
    cd $script_dir
    git checkout $branch
    git pull
else
    cd ~
    git clone --filter=blob:none --no-checkout $repo_source $repo_dir
    cd $repo_dir
    git sparse-checkout set --cone
    git checkout $branch
    git sparse-checkout set $module_dir
    cd $module_dir
fi

find * -name '*.py' -exec ln -sf $PWD/{} ~/klipper/klippy/extras/{} \;
