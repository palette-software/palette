#!/bin/bash

if [ "X" == "X$GITHUB_TOKEN" ]; then echo "Need GITHUB_TOKEN environment variable"; exit 10; fi
if [ "X" == "X$HOME" ]; then echo "Need HOME environment variable"; exit 10; fi

# echo "Uploading new version to Github..."
# git push --force "https://$GITHUB_TOKEN@github.com/$OWNER/$PACKAGE.git" HEAD:master --tags
# if [ $? -ne 0 ]; then echo "uploading new version failed"; exit 10; fi

echo "Creating Github realase..."
RELEASE_ID=`curl -H "Authorization: token $GITHUB_TOKEN" -d "{\"tag_name\": \"$PALETTE_VERSION\", \"name\": \"Palette Center\"}" "https://api.github.com/repos/$OWNER/$PACKAGE/releases"| jsawk "return this.id"`
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
