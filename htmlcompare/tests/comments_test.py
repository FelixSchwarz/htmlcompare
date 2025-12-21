# SPDX-License-Identifier: MIT

from unittest import TestCase

from .. import assert_same_html


class CommentsTest(TestCase):
    def test_ignores_comments_by_default(self):
        actual_html = '<div><!-- baz -->foo</div>'
        expected_html = actual_html
        assert_same_html(expected_html, actual_html, verbose=False)

        actual_html = '<div>foo</div>'
        assert_same_html(expected_html, actual_html, verbose=False)

        actual_html = '<div>foo<!-- baz --></div>'
        assert_same_html(expected_html, actual_html, verbose=False)

        expected_html = '<div>foo</div>'
        assert_same_html(expected_html, actual_html, verbose=False)

