#!/bin/sh

trash build dist
python3 setup.py sdist bdist_wheel
gpg --local-user="0x77E0DB66" --detach-sign  -a dist/*.tar.gz
gpg --local-user="0x77E0DB66" --detach-sign  -a dist/*.whl
