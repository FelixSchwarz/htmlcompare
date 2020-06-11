#!/bin/sh

for D in build dist; do
    if [ -e "$D" ]; then
        trash "$D"
    fi
done

/usr/bin/python3 setup.py sdist bdist_wheel > /dev/null

RELEASE_VERSION=$(cat VERSION.txt)

gpg --local-user="0x77E0DB66" --detach-sign  -a dist/HTMLCompare-${RELEASE_VERSION}*.tar.gz
gpg --local-user="0x77E0DB66" --detach-sign  -a dist/HTMLCompare-${RELEASE_VERSION}*.whl

RELEASE_FILES=$(ls -1 dist/HTMLCompare-${RELEASE_VERSION}*)

echo twine upload "dist/HTMLCompare-${RELEASE_VERSION}*"
