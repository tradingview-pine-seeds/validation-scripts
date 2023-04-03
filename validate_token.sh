
if [ -z "${ACTION_TOKEN}" ]
then
  echo "Failed to find ACTION_TOKEN. Make sure that ACTION_TOKEN is set in the repository secrets."
  exit 1
fi

RESP=$(echo "${ACTION_TOKEN}" | gh auth login --with-token 2>&1)
if [ $? -ne 0 ]
then
    echo "Authorization failed. Make sure that your ACTION_TOKEN is valid and not expired."
    exit 1
fi

if  [[ "$RESP" == *"error"* ]];
then
  echo "Insufficient scope error. Provide ACTION_TOKEN with the repo, workflow, and admin:org scopes."
  exit 1
fi

SCOPES=$(gh auth status  2>&1 | grep "scopes")
valid=true
if [[ "$SCOPES" != *"workflow"* ]]; then
  echo "Insufficient scope error. Provide ACTION_TOKEN with the workflow scope."
  valid=false
fi

if [[ "$SCOPES" != *"admin:org"* ]]; then
  echo "Insufficient scope error. Provide ACTION_TOKEN with the admin:org scope."
  valid=false
fi

if ! $valid ; then
  exit 1
fi

echo "ACTION_TOKEN validation successful"
