#!/bin/bash

###################################################
######## LOAD USER-SPECIFIC CONFIG
###################################################

SOURCE=$(realpath  $(dirname "$BASH_SOURCE"))

USER_CONFIG_FILE=$(dirname $0)/.ccc_config.sh

# create config file if it does not exist
if [ ! -f "$USER_CONFIG_FILE" ]; then  
  cp "$SOURCE/config_user.sh.example" "$USER_CONFIG_FILE"
fi

# include user-specific settings
# shellcheck source=./config_user.sh
source "$USER_CONFIG_FILE"

# load utils
source $SOURCE/utils.sh