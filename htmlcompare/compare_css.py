# SPDX-License-Identifier: MIT

import re
from collections.abc import Container, Iterable, Sequence
from typing import Optional

import tinycss2
from tinycss2.ast import (
    AtRule,
    Declaration,
    DimensionToken,
    LiteralToken,
    Node,
    NumberToken,
    ParseError,
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

# separators in a declaration value which do not need surrounding whitespace:
# "font:12px / 1.5 serif" and "font:12px/1.5 serif" declare the same font.
# "+" and "-" are not in this set: they are arithmetic operators inside a value
# and CSS requires the whitespace around them (in "calc()" it is mandatory).
_VALUE_SEPARATORS = frozenset({',', '/'})

# separators in a declaration block which does not parse and is therefore
# compared literally: ";" ends a declaration and ":" separates name and value,
# so "color:red;*zoom:1" and "color: red; *zoom: 1" are the same block.
_BLOCK_SEPARATORS = _VALUE_SEPARATORS | frozenset({':', ';'})

_WHITESPACE_RE = re.compile(r'\s+')

# CSS length units. A zero length may omit its unit ("margin:0" means
# "margin:0px"), which is not true for any other kind of dimension: "0s" is not
# a valid <time> and "0deg" is not a valid <angle>.
_LENGTH_UNITS = frozenset({
    # absolute
    'cm', 'in', 'mm', 'pc', 'pt', 'px', 'q',
    # font-relative
    'cap', 'ch', 'em', 'ex', 'ic', 'lh', 'rcap', 'rch', 'rem', 'rex', 'ric', 'rlh',
    # viewport-relative
    'vb', 'vh', 'vi', 'vmax', 'vmin', 'vw',
    'dvb', 'dvh', 'dvi', 'dvmax', 'dvmin', 'dvw',
    'lvb', 'lvh', 'lvi', 'lvmax', 'lvmin', 'lvw',
    'svb', 'svh', 'svi', 'svmax', 'svmin', 'svw',
})

def compare_css(expected_css: str, actual_css: str) -> bool:
    _e_css = normalize_css(expected_css)
    _a_css = normalize_css(actual_css)
    if (_e_css is None) or (_a_css is None):
        return _compare_literally(expected_css, actual_css)
    _e_css_str = tinycss2.serialize(_e_css)
    _a_css_str = tinycss2.serialize(_a_css)
    return _e_css_str == _a_css_str


def compare_stylesheet(expected_css, actual_css):
    _e_rules = normalize_stylesheet(expected_css)
    _a_rules = normalize_stylesheet(actual_css)
    if _contains_parse_error(_e_rules) or _contains_parse_error(_a_rules):
        return _compare_literally(expected_css, actual_css)
    _e_css_str = tinycss2.serialize(_e_rules)
    _a_css_str = tinycss2.serialize(_a_rules)
    return _e_css_str == _a_css_str


def _contains_parse_error(rules: Iterable[Node]) -> bool:
    """Return True if any (possibly nested) rule is a tinycss2 parse error."""
    for rule in rules:
        if isinstance(rule, ParseError):
            return True
        is_nesting_at_rule = isinstance(rule, AtRule) and (rule.content is not None)
        if is_nesting_at_rule and _contains_parse_error(rule.content):
            return True
    return False


def _compare_literally(expected_css: str, actual_css: str) -> bool:
    """
    Compare CSS which tinycss2 could not parse into rules or declarations.

    A ``ParseError`` carries only "kind" and "message", never the offending
    source text, so it can not be serialized. Comparing those attributes instead
    is not an option either: "p{color:red}}" and "p{color:red}]" produce the
    very same error at the very same position, so different CSS would silently
    compare equal.

    Compare the input itself instead, ignoring insignificant whitespace. That is
    stricter than the regular comparison, but it can only ever report a
    difference which is not one, never miss one.
    """
    return _collapse_whitespace(expected_css) == _collapse_whitespace(actual_css)


def _collapse_whitespace(css_str: str) -> str:
    return _WHITESPACE_RE.sub(' ', css_str).strip()


def is_whitespace(token):
    return (token.type == 'whitespace')

def is_separator(token: Node, separators: Container[str]) -> bool:
    return isinstance(token, LiteralToken) and (token.value in separators)

def _normalize_whitespace(all_tokens: Iterable[Node], separators: Container[str]) -> list[Node]:
    """
    Return the tokens with all insignificant whitespace removed.

    Whitespace must not be stripped completely: in a selector it is the
    descendant combinator, so ".a .b" (a ".b" inside a ".a") and ".a.b" (one
    element with both classes) are entirely different rules. In a declaration
    value it separates component values, so "margin:0 auto" must not collapse
    into a single "0auto" token.

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

def _is_zero_length(token: Node) -> bool:
    # "isinstance" instead of a check on "token.type": "type" is defined on the
    # tinycss2 subclasses, not on "Node" itself.
    if not isinstance(token, DimensionToken):
        return False
    # "value" instead of "int_value": the latter is None for "0.0px" (and for
    # "1e0px", which is not zero at all).
    return (token.value == 0) and (token.lower_unit in _LENGTH_UNITS)

def _strip_zero_units(all_tokens):
    tokens = []
    for token in all_tokens:
        if _is_zero_length(token):
            # a plain "0", no matter how the zero length was written: "0.0px"
            # and "0px" must end up with the same representation.
            token = NumberToken(token.source_line, token.source_column, 0, 0, '0')
        tokens.append(token)
    return tokens

def _property_name(decl: Declaration) -> str:
    """
    Return the property name of a declaration as it should be compared.

    CSS property names are case-insensitive, so "COLOR" and "color" are the same
    property. Custom properties are not: "--Foo" and "--foo" are two distinct
    properties. tinycss2 lowercases those as well (its "_parse_declaration()"
    carries a "# TODO: Handle custom property names"), so "lower_name" must not
    be used for them.
    """
    if decl.name.startswith('--'):
        return decl.name
    return decl.lower_name


def _normalize_declaration(decl):
    """Return a normalized copy of a tinycss2 ``Declaration``."""
    tokens = _normalize_whitespace(decl.value, _VALUE_SEPARATORS)
    tokens = _strip_zero_units(tokens)
    return Declaration(
        line       = decl.source_line,
        column     = decl.source_column,
        name       = _property_name(decl),
        lower_name = decl.lower_name,
        value      = tokens,
        important  = decl.important
    )


def _property_family(decl: Declaration) -> str:
    """
    Return the family of related properties a declaration belongs to.

    CSS makes the order of two declarations significant as soon as one of them
    can override the other: "background:red;background-color:blue" renders blue
    while the reverse renders red. Grouping by the first segment of the property
    name keeps a shorthand together with its longhands (and with its
    vendor-prefixed spellings), so their source order survives the sorting while
    unrelated properties stay order-independent.

    A custom property is a family of its own: "--" is not a shorthand prefix and
    the name is case-sensitive.
    """
    if decl.name.startswith('--'):
        return decl.name
    return _VENDOR_PREFIX_RE.sub('', decl.name).split('-')[0]


def _sort_declarations(decls):
    """
    Sort declarations by family so the comparison is order-independent.

    Only *across* families: the sort is stable, so declarations of the same
    family keep the order they were written in. See "_property_family()".
    """
    return sorted(decls, key=_property_family)


def normalize_css(css_declaration: str) -> Optional[tuple[Declaration, ...]]:
    """
    Normalize the declarations of a "style" attribute for comparison.

    Return `None` if the attribute does not parse as a declaration list, so the
    caller can fall back to a literal comparison.
    """
    _decls = []
    _css_decls = tinycss2.parse_declaration_list(
        css_declaration, skip_comments=True, skip_whitespace=True
    )
    for decl in _css_decls:
        # tinycss2 also returns `ParseError` ("color red", "*zoom:1") and
        # `AtRule` ("@media screen{color:red}") objects.
        if not isinstance(decl, Declaration):
            return None
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
            # keep errors: they can not be serialized but compare_stylesheet()
            # needs them to notice that it must fall back to a literal comparison
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


def _normalize_declaration_body(content: Sequence[Node]) -> list[Node]:
    """
    Normalize the body of a rule which contains declarations.

    Anything tinycss2 does not parse into a declaration used to be dropped here,
    which turned invalid CSS into a false negative: ".foo{*zoom:1}" (the IE star
    hack, still in use in HTML email) compared equal to ".foo{}" and even to
    ".foo{*zoom:2}".

    Such a body is compared literally instead - as its tokens, which unlike a
    ``ParseError`` do carry the source text. The fallback is scoped to the block
    which actually failed, so a broken rule does not stop the rest of the
    stylesheet from being compared semantically.
    """
    items = tinycss2.parse_declaration_list(
        content, skip_comments=True, skip_whitespace=True
    )
    if not all(isinstance(item, Declaration) for item in items):
        return _normalize_whitespace(content, _BLOCK_SEPARATORS)
    normalized_decls = [_normalize_declaration(decl) for decl in items]
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
