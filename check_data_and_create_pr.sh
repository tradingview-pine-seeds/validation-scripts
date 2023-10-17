#!/bin/bash
set -e

bash scripts/validate_token.sh

# checkout fork repo (via temp dir as current dir is not emply and it does't allow to check out repo in it)
git clone "https://${REPO_OWNER}:${ACTION_TOKEN}@github.com/${REPO_OWNER}/${REPO_NAME}.git" temp
mv temp/* .
mv temp//.git* .
rmdir temp


# remove unused branches before creating new
git checkout master
# delete merged and unmerged remote branches
git branch --merged | egrep -v "(^\*|master)" | xargs -I % sh -c 'git branch -D %; git push --delete origin %';
git branch --no-merged | egrep -v "(^\*|master)" | xargs -I % sh -c 'git branch -D %; git push --delete origin %';

# create a new branch for update
git checkout master
PR_BRANCH_NAME="update_$(git log -n 1 --pretty=format:%H)"
git checkout -b ${PR_BRANCH_NAME} > /dev/null 2>&1
git push --set-upstream origin ${PR_BRANCH_NAME} > /dev/null 2>&1

# check data in update
export GROUP=${REPO_NAME}
python3 scripts/simple_data_check.py

# close previous PR if it exists
bash scripts/close_pr_if_exists.sh

# create new PR
export GH_TOKEN=${ACTION_TOKEN}
gh api -X POST /repos/tradingview-pine-seeds/${REPO_NAME}/pulls -f base="master" -f head="${REPO_OWNER}:${PR_BRANCH_NAME}" -f title="Upload data" > /dev/null 2>&1
