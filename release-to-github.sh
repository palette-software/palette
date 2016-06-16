#!/bin/bash

#if [ "Xmaster" != "X$TRAVIS_BRANCH" ]; then echo "Current branch is $TRAVIS_BRANCH. We are deploying only from the master branch"; exit 0; fi
# THIS IS A TEMPORARY CHECK FOR THIS BRANCH!!!
if [ "Xorigin/cen-13/ci-alternative" != "X$TRAVIS_BRANCH" ]; then echo "Current branch is $TRAVIS_BRANCH. We are deploying only from the origin/cen-13/ci-alternative branch temporarily."; exit 0; fi
if [ "X" != "X$TRAVIS_TAG" ]; then echo "Tags are auto-committed by deploys, so this is already a result of a deploy. Skip deploy this time."; exit 0; fi
if [ "X" == "X$GITHUB_TOKEN" ]; then echo "GITHUB_TOKEN environment variable is not set!"; exit 10; fi
if [ "X" == "X$HOME" ]; then echo "HOME environment variable is not set!"; exit 10; fi

# echo "Uploading new version to Github..."
# git push --force "https://$GITHUB_TOKEN@github.com/$OWNER/$PACKAGE.git" HEAD:master --tags
# if [ $? -ne 0 ]; then echo "uploading new version failed"; exit 10; fi

echo "Creating Github realase..."
GITHUB_RESPONSE=`curl -H "Authorization: token $GITHUB_TOKEN" -d "{\"tag_name\": \"$PALETTE_VERSION\", \"name\": \"Palette Center\"}" "https://api.github.com/repos/$OWNER/$PACKAGE/releases"`
# Parse the release ID from the the GitHub response.
# NOTE: This is an ugly workaround, because we didn't manage to get jsawk working on Travis machines.
echo "GitHub response: $GITHUB_RESPONSE"
echo `grep --version` 
ID_LINE=`echo "${GITHUB_RESPONSE}" | grep '^\s\s"id":\s\d*'` 
echo "ID_LINE=$ID_LINE"
ID_STRING=`echo "${ID_LINE}" | cut -d' ' -f 4`
echo "ID_STRING=$ID_STRING"
RELEASE_ID=`echo $ID_STRING | cut -d',' -f 1`
echo "RELEASE_ID=$RELEASE_ID"
if [ $? -ne 0 ]; then echo "Creating new release failed"; exit 10; fi
echo $RELEASE_ID
if [ "X" == "X$RELEASE_ID" ]; then echo "Release ID was not found in GitHub response"; exit 10; fi

echo "Uploading Github realase asset..."
curl --progress-bar \
     -H "Content-Type: application/octet-stream" \
     -H "Authorization: token $GITHUB_TOKEN" \
     --retry 3 \
     --data-binary @$PCKG_FILE \
     "https://uploads.github.com/repos/$OWNER/$PACKAGE/releases/$RELEASE_ID/assets?name=$PCKG_FILE"
if [ $? -ne 0 ]; then echo "Uploading release asset failed"; exit 10; fi
