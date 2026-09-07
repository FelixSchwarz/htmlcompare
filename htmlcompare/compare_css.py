# SPDX-License-Identifier: MIT

import re
from collections.abc import Container, Iterable, Sequence
from operator import attrgetter

import tinycss2
from tinycss2.ast import (
    AtRule,
    Declaration,
    Node,
    NumberToken,
    QualifiedRule,
    WhitespaceToken,
)


__all__ = ['compare_css', 'compare_stylesheet']

# at-rules whose body is a list of declarations instead of a list of rules.
# Parsing these as a rule list yields nothing but tinycss2 parse errors.
_DECLARATION_BODIED_AT_RULES = frozenset({
    'counter-style',
    'font-face',
    'font-palette-values',
    'page',
    'property',
    'viewport',
})

_VENDOR_PREFIX_RE = re.compile(r'^-[a-z]+-')

# separators in a selector (or at-rule prelude) which do not need surrounding
# whitespace: "a > b" and "a>b" select the same elements.
_PRELUDE_SEPARATORS = frozenset({'>', '+', '~', ','})

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

def is_separator(token: Node, separators: Container[str]) -> bool:
    return (token.type == 'literal') and (token.value in separators)

def _normalize_whitespace(all_tokens: Iterable[Node], separators: Container[str]) -> list[Node]:
    """
    Return the tokens with all insignificant whitespace removed.

    Whitespace must not be stripped completely: in a selector it is the
    descendant combinator, so ".a .b" (a ".b" inside a ".a") and ".a.b" (one
    element with both classes) are entirely different rules.

    Insignificant is: a run of whitespace (equivalent to a single space),
    whitespace at the start or the end, and whitespace next to one of
    "separators" ("a > b" is the same as "a>b").
    """
    collapsed = []
    for token in all_tokens:
        if is_whitespace(token):
            if collapsed and is_whitespace(collapsed[-1]):
                continue
            token = WhitespaceToken(token.source_line, token.source_column, ' ')
        collapsed.append(token)

    tokens = []
    for i, token in enumerate(collapsed):
        if is_whitespace(token):
            previous_token = collapsed[i - 1] if (i > 0) else None
            next_token = collapsed[i + 1] if ((i + 1) < len(collapsed)) else None
            is_insignificant = (
                (previous_token is None)
                or (next_token is None)
                or is_separator(previous_token, separators)
                or is_separator(next_token, separators)
            )
            if is_insignificant:
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

def _normalize_declaration(decl):
    """Return a normalized copy of a tinycss2 ``Declaration``."""
    tokens = _strip_whitespace(decl.value)
    tokens = _strip_zero_units(tokens)
    return Declaration(
        line       = decl.source_line,
        column     = decl.source_column,
        name       = decl.name,
        lower_name = decl.lower_name,
        value      = tokens,
        important  = decl.important
    )


def _sort_declarations(decls):
    """Sort declarations by name so the comparison is order-independent."""
    return sorted(decls, key=attrgetter('name'))


def normalize_css(css_declaration_str):
    _decls = []
    _css_decls = tinycss2.parse_declaration_list(
        css_declaration_str, skip_comments=True, skip_whitespace=True
    )
    for decl in _css_decls:
        assert (decl.type == 'declaration'), decl
        _decls.append(_normalize_declaration(decl))

    return tuple(_sort_declarations(_decls))


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
    prelude = _normalize_whitespace(rule.prelude, _PRELUDE_SEPARATORS)

    return QualifiedRule(
        rule.source_line,
        rule.source_column,
        prelude,
        _normalize_declaration_body(rule.content),
    )


def _normalize_declaration_body(content: Sequence[Node]) -> list[Declaration]:
    """Normalize the body of a rule which contains declarations."""
    decls = tinycss2.parse_declaration_list(
        content, skip_comments=True, skip_whitespace=True
    )
    normalized_decls = [
        _normalize_declaration(decl) for decl in decls if decl.type == 'declaration'
    ]
    return _sort_declarations(normalized_decls)


def _has_declaration_body(rule: AtRule) -> bool:
    """Return True if the at-rule contains declarations instead of nested rules."""
    at_keyword = _VENDOR_PREFIX_RE.sub('', rule.lower_at_keyword)
    return (at_keyword in _DECLARATION_BODIED_AT_RULES)


def _normalize_at_rule(rule: AtRule) -> AtRule:
    """Normalize an at-rule (@media, @keyframes, etc.)."""
    prelude = _normalize_whitespace(rule.prelude, _PRELUDE_SEPARATORS)

    if rule.content is None:
        # at-rules without a body (e.g. "@import url(x.css);")
        normalized_content = None
    elif _has_declaration_body(rule):
        # e.g. "@font-face" or "@page": the body holds declarations, not rules
        normalized_content = _normalize_declaration_body(rule.content)
    else:
        # the content contains nested rules (like @media)
        content_rules = tinycss2.parse_rule_list(
            rule.content,
            skip_comments=True,
            skip_whitespace=True,
        )
        normalized_content = list(_normalize_rule_list(content_rules))

    return AtRule(
        rule.source_line,
        rule.source_column,
        rule.at_keyword,
        rule.lower_at_keyword,
        prelude,
        normalized_content,
    )
