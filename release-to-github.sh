#!/bin/bash

#if [ "Xmaster" != "X$TRAVIS_BRANCH" ]; then echo "Current branch is $TRAVIS_BRANCH. We are deploying only from the master branch"; exit 0; fi
# THIS IS A TEMPORARY CHECK FOR THIS BRANCH!!!
if [ "Xorigin/cen-13/ci-alternative" != "X$TRAVIS_BRANCH" ]; then echo "Current branch is $TRAVIS_BRANCH. We are deploying only from the origin/cen-13/ci-alternative branch temporarily."; exit 0; fi
if [ "X" != "X$TRAVIS_TAG" ]; then echo "Tags are auto-committed by deploys, so this is already a result of a deploy. Skip deploy this time."; exit 0; fi
if [ "X" == "X$GITHUB_TOKEN" ]; then echo "Need GITHUB_TOKEN environment variable"; exit 10; fi
if [ "X" == "X$HOME" ]; then echo "Need HOME environment variable"; exit 10; fi

# echo "Uploading new version to Github..."
# git push --force "https://$GITHUB_TOKEN@github.com/$OWNER/$PACKAGE.git" HEAD:master --tags
# if [ $? -ne 0 ]; then echo "uploading new version failed"; exit 10; fi

echo "Creating Github realase..."
RELEASE_ID=`curl -H "Authorization: token $GITHUB_TOKEN" -d "{\"tag_name\": \"$PALETTE_VERSION\", \"name\": \"Palette Center\"}" "https://api.github.com/repos/$OWNER/$PACKAGE/releases"| ./jsawk "return this.id"`
if [ $? -ne 0 ]; then echo "creating new release failed"; exit 10; fi
echo $RELEASE_ID

echo "Uploading Github realase asset..."
curl --progress-bar \
     -H "Content-Type: application/octet-stream" \
     -H "Authorization: token $GITHUB_TOKEN" \
     --retry 3 \
     --data-binary @$PCKG_FILE \
     "https://uploads.github.com/repos/$OWNER/$PACKAGE/releases/$RELEASE_ID/assets?name=$PCKG_FILE"
if [ $? -ne 0 ]; then echo "uploading release asset failed"; exit 10; fi
