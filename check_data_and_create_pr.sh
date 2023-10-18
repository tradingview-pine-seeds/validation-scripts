#!/bin/bash

# setted by GitHub
set -e
set +o pipefail

bash scripts/validate_token.sh

# checkout fork repo (via temp dir as current dir is not emply and it does't allow to check out repo in it)
git clone "https://${REPO_OWNER}:${ACTION_TOKEN}@github.com/${REPO_OWNER}/${REPO_NAME}.git" temp
mv temp/* .
mv temp//.git* .
rmdir temp

set +e
set +o pipefail
# remove unused branches before creating new
git checkout master
git branch --list | cat
merged_branches=$(git branch -r --merged | grep "update_*" -c)
nomerged_branches=$(git branch --no-merged | grep "update_*" -c)
total_branches=$(($merged_branches+$nomerged_branches))

# delete all merged and unmerged remote `update_*` branches
if [[ $total_branches > 0 ]]
then
    git branch -r --merged | grep "update_*" | cut -d "/" -f 2 | xargs git push --delete origin
    git branch --no-merged | grep "update_*" | xargs -I % bash -c 'git branch -D %; git push --delete origin %';
else
    echo "No temporary branch to remove"
fi

set -e
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
set +e
export GH_TOKEN=${ACTION_TOKEN}
gh api -X POST /repos/tradingview-pine-seeds/${REPO_NAME}/pulls -f base="master" -f head="${REPO_OWNER}:${PR_BRANCH_NAME}" -f title="Upload data" > /dev/null 2>&1
