# SPDX-License-Identifier: MIT

from operator import attrgetter

import tinycss2
from tinycss2.ast import AtRule, Declaration, NumberToken, QualifiedRule


__all__ = ['compare_css', 'compare_stylesheet']

def compare_css(expected_css, actual_css):
    _e_css = normalize_css(expected_css)
    _a_css = normalize_css(actual_css)
    _e_css_str = tinycss2.serialize(_e_css)
    _a_css_str = tinycss2.serialize(_a_css)
    return _e_css_str == _a_css_str


def compare_stylesheet(expected_css, actual_css):
    _e_css_str = tinycss2.serialize(normalize_stylesheet(expected_css))
    _a_css_str = tinycss2.serialize(normalize_stylesheet(actual_css))
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
            token = NumberToken(
                token.source_line,
                token.source_column,
                token.value,
                token.int_value,
                token.representation,
            )
        tokens.append(token)
    return tokens

def normalize_css(css_declaration_str):
    _decls = []
    _css_decls = tinycss2.parse_declaration_list(
        css_declaration_str, skip_comments=True, skip_whitespace=True
    )
    for decl in _css_decls:
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


def normalize_stylesheet(css_str):
    """Normalize a CSS stylesheet (with selectors and rules) for comparison.

    Unlike normalize_css() which handles declaration lists (for style attributes),
    this function handles full stylesheets with selectors like:
        body { margin: 0; }
        .foo { color: red; }
        @media screen { .foo { color: blue; } }
    """
    rules = tinycss2.parse_stylesheet(css_str, skip_comments=True, skip_whitespace=True)
    return _normalize_rule_list(rules)


def _normalize_rule_list(rules):
    """Normalize a list of CSS rules (qualified rules, at-rules, etc.)."""
    normalized_rules = []

    for rule in rules:
        if rule.type == 'qualified-rule':
            normalized_rule = _normalize_qualified_rule(rule)
            normalized_rules.append(normalized_rule)
        elif rule.type == 'at-rule':
            normalized_rule = _normalize_at_rule(rule)
            normalized_rules.append(normalized_rule)
        elif rule.type == 'error':
            # keep errors for debugging
            normalized_rules.append(rule)

    return tuple(normalized_rules)


def _normalize_qualified_rule(rule):
    """Normalize a qualified rule (selector { declarations })."""
    prelude = _strip_whitespace(rule.prelude)

    # parse and normalize the content (declarations)
    content_decls = tinycss2.parse_declaration_list(
        rule.content, skip_comments=True, skip_whitespace=True
    )
    normalized_decls = []
    for decl in content_decls:
        if decl.type == 'declaration':
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
            normalized_decls.append(_decl)

    # sort declarations by name for order-independent comparison
    sorted_decls = sorted(normalized_decls, key=attrgetter('name'))

    return QualifiedRule(
        rule.source_line,
        rule.source_column,
        prelude,
        sorted_decls,
    )


def _normalize_at_rule(rule):
    """Normalize an at-rule (@media, @keyframes, etc.)."""
    prelude = _strip_whitespace(rule.prelude)

    # normalize the content if it contains nested rules (like @media)
    if rule.content is not None:
        content_rules = tinycss2.parse_rule_list(
            rule.content,
            skip_comments=True,
            skip_whitespace=True,
        )
        normalized_content = list(_normalize_rule_list(content_rules))
    else:
        normalized_content = None

    return AtRule(
        rule.source_line,
        rule.source_column,
        rule.at_keyword,
        rule.lower_at_keyword,
        prelude,
        normalized_content,
    )
