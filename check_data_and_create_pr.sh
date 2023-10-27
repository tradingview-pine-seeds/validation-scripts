#!/bin/bash
set -e

bash scripts/validate_token.sh

# checkout fork repo (via temp dir as current dir is not emply and it does't allow to check out repo in it)
git clone "https://${REPO_OWNER}:${ACTION_TOKEN}@github.com/${REPO_OWNER}/${REPO_NAME}.git" temp
mv temp/* .
mv temp//.git* .
rmdir temp


# check GH PR limit 3k files changing
# if [[ -z "${FROM_COMMIT}" ]]; then
#     FROM_COMMIT=$(git rev-list --max-parents=0 HEAD)
#     TO_COMMIT="HEAD"
# fi

git config diff.renameLimit 999999
#CHANGED_DATA_FILES=$(git diff --name-only --diff-filter=AM "$FROM_COMMIT".."$TO_COMMIT" | grep csv)
CHANGED_DATA_FILES=${git diff --name-only ${{ github.event.before }} ${{ github.event.after }} | wc -l}
if [["$CHANGED_DATA_FILES" -gt 3000 ]]; then
    echo "More then 3000 files added/changed. Please, push commit with changes less than in 3000 files"
    exit(1)
fi


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
