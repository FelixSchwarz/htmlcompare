# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

from __future__ import absolute_import, print_function, unicode_literals

from collections import namedtuple

import html5lib


__all__ = ['CompareResult', 'Difference', 'compare_html']

Difference = namedtuple('Difference', ('expected', 'actual',))

_CompareResult = namedtuple('CompareResult', ('is_equal', 'differences'))

class CompareResult(_CompareResult):
    def __bool__(self):
        return self.is_equal
    # Python 2 compatibility
    __nonzero__ = __bool__


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
    _e_attrs = _e.pop('data').copy()
    _a_attrs = _a.pop('data').copy()
    if _e != _a:
        # items different somewhere other than attributes
        return False

    # An omitted "style" attribute is equal to style=""
    _e_style = _e_attrs.pop((None, 'style'), '').rstrip(';')
    _a_style = _a_attrs.pop((None, 'style'), '').rstrip(';')
    if _e_style != _a_style:
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
    for item in expected_stream:
        while actual and is_whitespace(actual[0]):
            actual.pop(0)
        if is_whitespace(item):
            continue

        is_style_block = (item['type'] == 'Characters') and tags and (tags[-1] == 'style')
        if item['type'] == 'StartTag':
            tag_name = item["name"]
            tags.append(tag_name)
        elif item['type'] == 'EndTag':
            last_item = tags[-1]
            # just handle the simplest possible case
            assert last_item == item["name"]
            tags.pop()
        elif item['type'] == 'Comment':
            # later: compare conditional comments?
            pass
        elif item['type'] == 'EmptyTag':
            # tag without closing tag (e.g. "<meta>")
            pass

        if is_equal(item, actual[0]):
            actual.pop(0)
            continue
        elif is_style_block:
            # LATER: compare CSS
            actual.pop(0)
            continue
        elif item['type'] == 'Comment':
            # LATER: compare (conditional) comments
            actual.pop(0)
            continue

        actual_item = actual[0]
        if item['type'] in ('StartTag', 'EmptyTag', 'Characters'):
            differences = [
                Difference(expected=item, actual=actual_item)
            ]
        else:
            assert False, 'should not reach this...'
        break

    is_same = not bool(differences)
    return CompareResult(is_same, differences=differences)

