# SPDX-License-Identifier: MIT

from typing import Optional

from htmlcompare.compare import compare_html
from htmlcompare.options import CompareOptions
from htmlcompare.result import ComparisonResult


__all__ = ['assert_different_html', 'assert_same_html']


def assert_same_html(
        expected_html: str,
        actual_html: str,
        verbose: bool = True,
        message: Optional[str] = None,
        options: Optional[CompareOptions] = None,
    ) -> None:
    """Assert that two HTML strings are semantically equal."""
    result = compare_html(expected_html, actual_html, options)
    if result:
        return

    diff = result.differences[0]
    if verbose:
        print(f'-expected: {diff.expected!r}')
        print(f'+actual:   {diff.actual!r}')

    error_msg = str(diff)
    if message is not None:
        error_msg += ' ' + message
    raise AssertionError(error_msg)


def assert_different_html(
    expected_html: str,
    actual_html: str,
    options: Optional[CompareOptions] = None,
) -> ComparisonResult:
    """Assert that two HTML strings are semantically different."""
    result = compare_html(expected_html, actual_html, options)
    if not result:
        return result
    raise AssertionError('expected different HTML but DOM is the same')
