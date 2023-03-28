#!/bin/bash
set -e

git clone "https://github.com/tradingview-pine-seeds/validation-scripts.git" scripts

export TOKEN={GITHUB_TOKEN}
bash scripts/validate_token.sh

git clone "https://github.com/${REPO_OWNER}/${REPO_NAME}.git" .
git checkout master
PR_BRANCH_NAME="update_$(git log -n 1 --pretty=format:%H)"
git checkout -b ${PR_BRANCH_NAME} > /dev/null 2>&1
git push --set-upstream origin ${PR_BRANCH_NAME} > /dev/null 2>&1

export GROUP=${REPO_NAME}
python3 scripts/simple_data_check.py

scripts/close_pr_if_exists.sh

export GH_TOKEN=${GITHUB_TOKEN}
gh api -X POST /repos/tradingview-pine-seeds/${REPO_NAME}/pulls -f base="master" -f head="${REPO_OWNER}:${PR_BRANCH_NAME}" -f title="Upload data"
