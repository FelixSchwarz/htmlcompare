# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

from __future__ import absolute_import, print_function, unicode_literals

import sys

from .testutils import assert_same_html


__all__ = []

def htmlcompare_cli():
    if len(sys.argv) < 3:
        sys.stderr.write('usage: htmlcompare <EXPECTED> <ACTUAL>\n')
        sys.exit(1)
    expected_fn, actual_fn = sys.argv[1:3]
    with open(expected_fn, 'rb') as expected_fp:
        expected_html = expected_fp.read().decode('utf8')
    with open(actual_fn, 'rb') as actual_fp:
        actual_html = actual_fp.read().decode('utf8')
    try:
        assert_same_html(expected_html, actual_html, verbose=True)
    except AssertionError:
        raise
        sys.exit(10)
    print('HTML in both files is the same. :-)')

