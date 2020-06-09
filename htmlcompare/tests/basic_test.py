# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

from __future__ import absolute_import, print_function, unicode_literals

from unittest.case import TestCase

from .. import assert_different_html, assert_same_html


class BasicTest(TestCase):
    def test_can_compare_single_tag(self):
        assert_same_html('<div></div>', '<div></div>')

    def test_can_compare_trivial_html(self):
        expected_html = '''<html>
        <body>
            Foo bar
        </body>
        </html>'''

        actual_html = '''
        <html><body>
         Foo bar</body></html>
        '''
        assert_same_html(expected_html, actual_html)

    def test_can_detect_different_tags(self):
        expected_html = '<foo />'
        actual_html   = '<bar />'
        assert_different_html(expected_html, actual_html)

    def test_can_detect_different_attributes(self):
        expected_html = '<div style="color: green" />'
        actual_html = '<div style="color: red" />'
        assert_different_html(expected_html, actual_html)

