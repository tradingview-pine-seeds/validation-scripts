#!/bin/bash

echo "${ACTION_TOKEN}" | gh auth login --with-token > /dev/null 2>&1
if [ -z $? ]
then
    echo $(color_message "Authorization failed. Update ACTION_TOKEN in the repository secrets." $RED)
    exit 1
fi

EXISTING_PRS=$(gh api -X GET /repos/tradingview-pine-seeds/"$REPO_NAME"/pulls)
if [ "$EXISTING_PRS" != "[]" ]; then
    NUMBER_OF_PRS=$(echo "$EXISTING_PRS" | jq length)
    if [ "$NUMBER_OF_PRS" != 1 ]; then
        echo $(color_message "There is more than one PR open. To resolve the issue, contact pine.seeds@tradingview.com with the Pine Seeds Issue subject." $RED)
        exit 1
    fi
    BASE_LABEL=$(echo "$EXISTING_PRS" | jq -r ".[0].base.label")
    if [ "$BASE_LABEL" != "tradingview-pine-seeds:master" ]; then
        echo $(color_message "base = $BASE_LABEL is incorrect" $RED)
        exit 1
    fi
    HEAD_LABEL=$(echo "$EXISTING_PRS" | jq -r ".[0].head.label")
    OWNER="${HEAD_LABEL%:*}"
    if [ "${OWNER}" != "$REPO_OWNER" ]; then
        echo $(color_message "head = $HEAD_LABEL is incorrect" $RED)
        exit 1
    fi
    NUM=$(echo "$EXISTING_PRS" | jq -r ".[0].number")
    gh --repo tradingview-pine-seeds/"$REPO_NAME" pr close "$NUM"
    BRANCH="${HEAD_LABEL#*:}"
    gh api -X DELETE "repos/${OWNER}/${REPO_NAME}/git/refs/heads/${BRANCH}"
fi
