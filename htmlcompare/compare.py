# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

from __future__ import absolute_import, print_function, unicode_literals

from collections import namedtuple
import re

import html5lib

from .compare_css import compare_css


__all__ = ['CompareResult', 'Difference', 'compare_html']

Difference = namedtuple('Difference', ('expected', 'actual',))

_CompareResult = namedtuple('CompareResult', ('is_equal', 'differences'))

class CompareResult(_CompareResult):
    def __bool__(self):
        return self.is_equal
    # Python 2 compatibility
    __nonzero__ = __bool__


def is_comment(token):
    return (token['type'] == 'Comment')

def is_whitespace(token):
    return (token['type'] == 'SpaceCharacters')

def is_equal(expected, actual):
    if expected == actual:
        return True

    if expected['type'] not in ('StartTag', 'EmptyTag'):
        return False
    elif actual['type'] not in ('StartTag', 'EmptyTag'):
        return False

    _e = expected.copy()
    _a = actual.copy()
    # value in _e['data'] is OrderedDict (Python 3.7/htmllib 1.0.1). When
    # comparing two OrderedDict instances ordering of keys does matter (*duh*)
    # but it should not matter when comparing HTML.
    # Creating a new "dict" instance does two things:
    #  - copy attribute data (should be done anyway, do not modify inputs)
    #  - convert OrderedDict to dict - for the latter ordering of keys does NOT matter
    _e_attrs = dict(_e.pop('data'))
    _a_attrs = dict(_a.pop('data'))
    if _e != _a:
        # items different somewhere other than attributes
        return False

    _e_style = _e_attrs.pop((None, 'style'), '')
    _a_style = _a_attrs.pop((None, 'style'), '')
    is_same_style = compare_css(_e_style, _a_style)
    if not is_same_style:
        return False

    _e_css_class = _e_attrs.pop((None, 'class'), '')
    _a_css_class = _a_attrs.pop((None, 'class'), '')
    e_css_classes = set(re.split(r'\s+', _e_css_class.strip()))
    a_css_classes = set(re.split(r'\s+', _a_css_class.strip()))
    has_same_css_classes = (e_css_classes == a_css_classes)
    if not has_same_css_classes:
        return False

    return (_e_attrs == _a_attrs)


def compare_html(expected_html, actual_html):
    expected_document = html5lib.parse(expected_html, namespaceHTMLElements=False)
    TreeWalker = html5lib.getTreeWalker('etree')
    expected_stream = tuple(TreeWalker(expected_document))

    actual_document = html5lib.parse(actual_html, namespaceHTMLElements=False)
    TreeWalker = html5lib.getTreeWalker('etree')
    actual_stream = tuple(TreeWalker(actual_document))

    differences = None
    tags = []
    actual = list(actual_stream)
    for expected in expected_stream:
        if is_whitespace(expected):
            continue
        while actual and (is_whitespace(actual[0]) or is_comment(actual[0])):
            actual.pop(0)

        is_style_block = (expected['type'] == 'Characters') and tags and (tags[-1] == 'style')
        if expected['type'] == 'StartTag':
            tag_name = expected["name"]
            tags.append(tag_name)
        elif expected['type'] == 'EndTag':
            last_item = tags[-1]
            # just handle the simplest possible case
            assert last_item == expected["name"]
            tags.pop()
        elif is_comment(expected):
            # later: compare conditional comments?
            continue
        elif expected['type'] == 'EmptyTag':
            # tag without closing tag (e.g. "<meta>")
            pass

        if is_equal(expected, actual[0]):
            actual.pop(0)
            continue
        elif is_style_block:
            # LATER: compare CSS
            actual.pop(0)
            continue
        elif is_comment(expected):
            # LATER: compare (conditional) comments
            actual.pop(0)
            continue

        actual_item = actual[0]
        if expected['type'] in ('StartTag', 'EmptyTag', 'Characters'):
            differences = [
                Difference(expected=expected, actual=actual_item)
            ]
        else:
            assert False, 'should not reach this...'
        break

    is_same = not bool(differences)
    return CompareResult(is_same, differences=differences)

