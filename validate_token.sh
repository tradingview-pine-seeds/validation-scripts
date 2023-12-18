#!/bin/bash

set -x

if [ -z "${ACTION_TOKEN}" ]
then
  echo $(color_message "Failed to find ACTION_TOKEN. Make sure that ACTION_TOKEN is set in the repository secrets." $RED)
  exit 1
fi

RESP=$(echo "${ACTION_TOKEN}" | gh auth login --with-token 2>&1)
if [ $? -ne 0 ]
then
    echo $(color_message "Authorization failed. Make sure that your ACTION_TOKEN is valid and not expired." $RED)
    exit 1
fi

if  [[ "$RESP" == *"error"* ]];
then
  echo $(color_message "Insufficient scope error. Provide ACTION_TOKEN with the repo, workflow, and admin:org scopes." $RED)
  echo "Insufficient scope error. Provide ACTION_TOKEN with the repo, workflow, and admin:org scopes."
  exit 1
fi

SCOPES=$(gh auth status  2>&1 | grep "scopes")
valid=true
if [[ "$SCOPES" != *"workflow"* ]]; then
  echo echo $(color_message "Insufficient scope error. Provide ACTION_TOKEN with the workflow scope." $RED)
  valid=false
fi

if [[ "$SCOPES" != *"admin:org"* ]]; then
  echo $(color_message "Insufficient scope error. Provide ACTION_TOKEN with the admin:org scope." $RED)
  valid=false
fi

if ! $valid ; then
  exit 1
fi

echo $(color_message "ACTION_TOKEN validation successful" $GRN)
