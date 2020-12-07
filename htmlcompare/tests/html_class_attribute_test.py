# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

from __future__ import absolute_import, print_function, unicode_literals

from unittest.case import TestCase

from .. import assert_different_html, assert_same_html


class HTMLClassAttributeTest(TestCase):
    def test_ignores_ordering_of_css_classes(self):
        assert_same_html(
            '<div class="foo bar" />',
            '<div class="bar foo" />')
        assert_different_html(
            '<div class="foo bar" />',
            '<div class="foobar" />')

    def test_ignores_whitespace_inside_class_attribute(self):
        assert_same_html('<div class="foo   bar" />', '<div class=" foo bar  " />')
        assert_same_html('<div class="foo	bar" />', '<div class="foo bar" />')

    def test_treats_absent_class_same_as_empty_class_declaration(self):
        assert_same_html('<div class="" />', '<div />')
        # also add a tab to ensure the code covers different types of whitespace
        assert_same_html('<div class="  	  " />', '<div />')

