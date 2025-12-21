# SPDX-License-Identifier: MIT

from unittest import skip, TestCase

from .. import assert_different_html, assert_same_html


class HTMLStyleAttributeTest(TestCase):
    def test_can_ignore_empty_style_attribute(self):
        assert_different_html('<div style="color: red" />', '<div />')
        assert_same_html('<div style="" />', '<div />')
        # also check "EmptyTag"
        assert_same_html('<img style="">', '<img>')

    def test_can_ignore_additional_semicolon_in_style(self):
        assert_same_html('<div style="color: red;" />', '<div style="color: red" />')
        # also check "EmptyTag"
        assert_same_html('<img style="color: red;">', '<img style="color: red" >')

    def test_ignores_ordering_of_style_declarations(self):
        assert_same_html(
            '<div style="color: red; font-weight: bold" />',
            '<div style="font-weight:bold; color: red" />')

    def test_can_ignore_dimension_unit_if_value_is_0(self):
        assert_same_html('<div style="width: 0px" />', '<div style="width: 0" />')
        assert_same_html('<div style="width: 0px" />', '<div style="width: 0pt" />')
        assert_different_html('<div style="width: 1px" />', '<div style="width: 1" />')

    @skip('shorthand hex color matching not yet implemented')
    def test_can_handle_shorthand_hex_colors(self):
        assert_same_html('<div style="color: #f60" />', '<div style="color: #ff6600" />')
