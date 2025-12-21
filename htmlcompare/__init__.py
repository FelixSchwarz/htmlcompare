# SPDX-License-Identifier: MIT

from htmlcompare.compare import Difference, compare_html
from htmlcompare.options import CompareOptions
from htmlcompare.result import ComparisonResult
from htmlcompare.testutils import assert_different_html, assert_same_html


__all__ = [
    'compare_html',
    'Difference',
    'CompareOptions',
    'ComparisonResult',
    'assert_different_html',
    'assert_same_html',
]
