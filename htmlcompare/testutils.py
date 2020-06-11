# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

from __future__ import absolute_import, print_function, unicode_literals

from . import compare_html


__all__ = ['assert_different_html', 'assert_same_html']

def stringify_token(token):
    if token['type'] in ('StartTag', 'EmptyTag'):
        attrs = []
        for attr_key, attr_value in token['data'].items():
            ns, key = attr_key
            attrs.append('%s="%s"' % (key, attr_value))
        attr_str = (' ' if attrs else '') + ' '.join(attrs)
        return '<%s%s>' % (token["name"], attr_str)
    elif token['type'] == 'EndTag':
        return '</%s>' % (token["name"], )
    elif token['type'] == 'Characters':
        return '%s' % token['data']
    raise NotImplementedError(token['type'])

def assert_same_html(expected_html, actual_html, verbose=True):
    result = compare_html(expected_html, actual_html)
    if result:
        return
    diff = result.differences[0]
    expected_str = stringify_token(diff.expected)
    actual_str = stringify_token(diff.actual)
    if verbose:
        print('-' + expected_str)
        print('+' + actual_str)
    error_msg = '%s != %s' % (expected_str, actual_str)
    assert expected_str == actual_str, error_msg

def assert_different_html(expected_html, actual_html):
    result = compare_html(expected_html, actual_html)
    if not result:
        return result
    raise AssertionError('expected different HTML but DOM is the same')

