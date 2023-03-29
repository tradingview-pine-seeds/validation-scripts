
if [ -z "${TOKEN}" ]
then
  echo "Unable to find ACTION_TOKEN. Please make sure that ACTION_TOKEN is set in the repository secrets"
  exit 1
fi

RESP=$(echo "${TOKEN}" | gh auth login --with-token 2>&1)
if [ -z $? ]
then
    echo "Authorization failed. Please check that your ACTION_TOKEN is valid and not expired."
    exit 1
fi

if  [[ "$RESP" == *"error"* ]];
then
  echo "ACTION_TOKEN has not enough scopes, please provide ACTION_TOKEN with repo, workflow and admin:org scopes"
  exit 1
fi

SCOPES=$(gh auth status  2>&1 | grep "scopes")
valid=true
if [[ "$SCOPES" == *"workflow"* ]]; then
  echo "Workflow scope is found in your ACTION_TOKEN"
  else
    echo "ACTION_TOKEN has no workflow scope, please provide ACTION_TOKEN with workflow scope"
    valid=false
fi

if [[ "$SCOPES" == *"admin:org"* ]]; then
  echo "Admin:org scope is found in your ACTION_TOKEN"
  else
    echo "ACTION_TOKEN has no admin:org scope, please provide ACTION_TOKEN with admin:org scope"
    valid=false
fi

if ! $valid ; then
  exit 1
fi
