#!/bin/bash
set -e

BRANCH_NAME="update_$(git log -n 1 --pretty=format:%H)"
git checkout -b ${BRANCH_NAME}
git push

export GROUP=${REPO_NAME}
python3 scripts/simple_data_check.py

scripts/close_pr_if_exists.sh

# echo ${GITHUB_TOKEN} | gh auth login --with-token

export GH_TOKEN=${GITHUB_TOKEN}
gh api -X POST /repos/tradingview-pine-seeds/${REPO_NAME}/pulls -f base="master" -f head="${REPO_OWNER}:${BRANCH_NAME}" -f title="Upload data"
