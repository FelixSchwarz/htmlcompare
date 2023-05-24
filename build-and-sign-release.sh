#!/bin/sh

for D in build dist; do
    if [ -e "$D" ]; then
        trash "$D"
    fi
done

PROJECT_NAME=HTMLCompare
MOD_NAME="${PROJECT_NAME}"

/usr/bin/python3 -c "import build" 2>/dev/null
if [ "$?" != 0 ]; then
    echo "Python 'build' module not found."
    echo "\$ sudo dnf install python3-build"
    exit 1
fi
/usr/bin/python3 -m build --sdist --wheel

trash build

RELEASE_VERSION=$(cat VERSION.txt)

GPG_KEY="0xC26F9D8BBFAFF155"

gpg2 --local-user="${GPG_KEY}" --detach-sign  -a dist/${MOD_NAME}-${RELEASE_VERSION}*.tar.gz
gpg2 --local-user="${GPG_KEY}" --detach-sign  -a dist/${MOD_NAME}-${RELEASE_VERSION}*.whl

RELEASE_FILES=$(ls -1 dist/${MOD_NAME}-${RELEASE_VERSION}*)

echo twine upload "dist/${MOD_NAME}-${RELEASE_VERSION}*"
