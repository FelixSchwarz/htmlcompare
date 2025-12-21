# SPDX-License-Identifier: MIT

from operator import attrgetter

import tinycss2
from tinycss2.ast import Declaration, NumberToken, QualifiedRule


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
    """
    rules = tinycss2.parse_stylesheet(css_str, skip_comments=True, skip_whitespace=True)
    normalized_rules = []

    for rule in rules:
        if rule.type == 'qualified-rule':
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

            normalized_rule = QualifiedRule(
                rule.source_line,
                rule.source_column,
                prelude,
                sorted_decls,
            )
            normalized_rules.append(normalized_rule)
        elif rule.type == 'at-rule':
            # keep at-rules as-is for now (could be extended later)
            normalized_rules.append(rule)
        elif rule.type == 'error':
            # keep errors for debugging
            normalized_rules.append(rule)

    return tuple(normalized_rules)
