#!/bin/bash

echo "${TOKEN}" | gh auth login --with-token > /dev/null 2>&1
if [ -z $? ]
then
    echo "Authorization failed. Update ACTION_TOKEN in the repository secrets."
    exit 1
fi

EXISTING_PRS=$(gh api -X GET /repos/tradingview-pine-seeds/"$REPO_NAME"/pulls)
if [ "$EXISTING_PRS" != "[]" ]; then
    NUMBER_OF_PRS=$(echo "$EXISTING_PRS" | jq length)
    if [ "$NUMBER_OF_PRS" != 1 ]; then
        echo "There is more than one PR open. To resolve the issue, contact pine.seeds@tradingview.com with the Pine Seeds Issue subject."
        exit 1
    fi
    BASE_LABEL=$(echo "$EXISTING_PRS" | jq -r ".[0].base.label")
    if [ "$BASE_LABEL" != "tradingview-pine-seeds:master" ]; then
        echo "base = $BASE_LABEL is incorrect"
        exit 1
    fi
    HEAD_LABEL=$(echo "$EXISTING_PRS" | jq -r ".[0].head.label")
    if [ "${HEAD_LABEL%:*}" != "$REPO_OWNER" ]; then
        echo "head = $HEAD_LABEL is incorrect"
        exit 1
    fi
    NUM=$(echo "$EXISTING_PRS" | jq -r ".[0].number")
    gh --repo tradingview-pine-seeds/"$REPO_NAME" pr close "$NUM"
fi
