git filter-branch --env-filter '
NEW_NAME="myron93h"
NEW_EMAIL="myron93harberbwt@hotmail.com"

if [ "$GIT_COMMITTER_EMAIL" != "$NEW_EMAIL" ]
then
    export GIT_COMMITTER_NAME="$NEW_NAME"
    export GIT_COMMITTER_EMAIL="$NEW_EMAIL"
fi
if [ "$GIT_AUTHOR_EMAIL" != "$NEW_EMAIL" ]
then
    export GIT_AUTHOR_NAME="$NEW_NAME"
    export GIT_AUTHOR_EMAIL="$NEW_EMAIL"
fi
' --tag-name-filter cat -- --branches --tags

