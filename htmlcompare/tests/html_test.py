# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

from __future__ import absolute_import, print_function, unicode_literals

from unittest.case import skipIf as skip_if, TestCase

from .. import assert_different_html, assert_same_html
from ..compare_css import has_tinycss


class HTMLTest(TestCase):
    def test_can_ignore_empty_style_attribute(self):
        assert_different_html('<div style="color: red" />', '<div />')
        assert_same_html('<div style="" />', '<div />')
        # also check "EmptyTag"
        assert_same_html('<img style="">', '<img>')

    def test_can_ignore_additional_semicolon_in_style(self):
        assert_same_html('<div style="color: red;" />', '<div style="color: red" />')
        # also check "EmptyTag"
        assert_same_html('<img style="color: red;">', '<img style="color: red" >')

    @skip_if(not has_tinycss, reason='test requires tinycss2')
    def test_ignores_ordering_of_style_declarations(self):
        assert_same_html(
            '<div style="color: red; font-weight: bold" />',
            '<div style="font-weight:bold; color: red" />')

