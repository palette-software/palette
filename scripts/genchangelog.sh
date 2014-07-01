#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage: `basename $0` <package> <version>" >&2
    exit -1
fi

DEBFULLNAME="Palette Software, Inc."
DEBEMAIL=build@palette-software.com
NOW=`date -R`

cat <<EOF
$1 ($2) UNRELEASED; urgency=low

  * Initial release.

 -- $DEBFULLNAME <$DEBEMAIL>  $NOW

EOF
