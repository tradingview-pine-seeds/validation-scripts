#!/bin/bash
set -e

PR_BRANCH_NAME="update_$(git log -n 1 --pretty=format:%H)"
git checkout -b ${PR_BRANCH_NAME} > /dev/null 2>&1

git push --set-upstream origin ${PR_BRANCH_NAME} > /dev/null 2>&1

export GROUP=${REPO_NAME}
python3 scripts/simple_data_check.py

scripts/close_pr_if_exists.sh

export GH_TOKEN=${GITHUB_TOKEN}
gh api -X POST /repos/tradingview-pine-seeds/${REPO_NAME}/pulls -f base="master" -f head="${REPO_OWNER}:${PR_BRANCH_NAME}" -f title="Upload data"
