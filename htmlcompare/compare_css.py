# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

from __future__ import absolute_import, print_function, unicode_literals

from operator import attrgetter

try:
    import tinycss2
    from tinycss2.ast import Declaration, NumberToken

    has_tinycss = True
except ImportError:
    has_tinycss = False


__all__ = ['compare_css']

def compare_css(expected_css, actual_css):
    if not has_tinycss:
        # without tinycss we can not really do much
        # An omitted "style" attribute is equal to style=""
        _e_css = expected_css.rstrip(';')
        _a_css = actual_css.rstrip(';')
        return (_a_css == _e_css)

    _e_css = normalize_css(expected_css)
    _a_css = normalize_css(actual_css)
    _e_css_str = tinycss2.serialize(_e_css)
    _a_css_str = tinycss2.serialize(_a_css)
    return _e_css_str == _a_css_str


def is_dimension(token):
    return (token.type == 'dimension')

def is_whitespace(token):
    return (token.type == 'whitespace')

def _strip_whitespace(all_tokens):
    tokens = []
    for token in all_tokens:
        if is_whitespace(token):
            continue
        tokens.append(token)
    return tokens

def _strip_zero_units(all_tokens):
    tokens = []
    for token in all_tokens:
        if is_dimension(token) and token.int_value == 0:
            token = NumberToken(token.source_line, token.source_column, token.value, token.int_value, token.representation)
        tokens.append(token)
    return tokens

def normalize_css(css_declaration_str):
    _decls = []
    for decl in tinycss2.parse_declaration_list(css_declaration_str, skip_comments=True, skip_whitespace=True):
        assert (decl.type == 'declaration'), decl
        tokens = _strip_whitespace(decl.value)
        tokens = _strip_zero_units(tokens)
        _decl = Declaration(
            line       = decl.source_line,
            column     = decl.source_column,
            name       = decl.name,
            lower_name = decl.lower_name,
            value      = tokens,
            important  = decl.important
        )
        _decls.append(_decl)

    sorted_decls = sorted(_decls, key=attrgetter('name'))
    return tuple(sorted_decls)

