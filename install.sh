#!/usr/bin/env bash
set -e
cd $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
SRC_FILE="callback_plugins/codekipple_concise.py"

if ! command -v ansible >/dev/null 2>&1; then
    echo Ansible not found in path
    exit 1
fi

MODULE_PATH="$(command ansible --version|grep 'python module location ='|cut -d'=' -f2)"

if [[ ! -f "$SRC_FILE" ]]; then
    echo Invalid Source File $SRC_FILE
    exit 2
fi

DEST_PATH="$MODULE_PATH/plugins/callback"

cp_cmd="cp -v $SRC_FILE $DEST_PATH/."
eval $cp_cmd
