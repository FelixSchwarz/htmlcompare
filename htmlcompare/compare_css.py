# SPDX-License-Identifier: MIT

import re
from collections.abc import Callable, Container, Iterable, Sequence
from decimal import Decimal
from typing import Optional

import tinycss2
from tinycss2.ast import (
    AtRule,
    CurlyBracketsBlock,
    Declaration,
    DimensionToken,
    FunctionBlock,
    LiteralToken,
    Node,
    NumberToken,
    ParenthesesBlock,
    ParseError,
    PercentageToken,
    QualifiedRule,
    SquareBracketsBlock,
    StringToken,
    URLToken,
    WhitespaceToken,
)
from tinycss2.serializer import serialize_string_value


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

# a "ParseError" of one of these two kinds serializes to a fixed placeholder
# ('"[bad string]' resp. "url([bad url])"), so the offending source text is lost.
# Every other kind tinycss2 emits inside a token list survives serialization:
# ")", "]" and "}" write themselves and "eof-in-string"/"eof-in-url" write
# nothing because the text was already captured by the token before them.
_LOSSY_ERROR_KINDS = frozenset({'bad-string', 'bad-url'})

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
    if _must_compare_literally(_e_rules) or _must_compare_literally(_a_rules):
        return _compare_literally(expected_css, actual_css)
    _e_css_str = tinycss2.serialize(_e_rules)
    _a_css_str = tinycss2.serialize(_a_rules)
    return _e_css_str == _a_css_str


def _must_compare_literally(rules: Sequence[Node]) -> bool:
    """Return True if the normalized rules can not be compared as tokens."""
    return _contains_parse_error(rules) or _contains_lossy_token(rules)


def _contains_parse_error(rules: Iterable[Node]) -> bool:
    """Return True if any (possibly nested) rule is a tinycss2 parse error."""
    for rule in rules:
        if isinstance(rule, ParseError):
            return True
        is_nesting_at_rule = isinstance(rule, AtRule) and (rule.content is not None)
        if is_nesting_at_rule and _contains_parse_error(rule.content):
            return True
    return False


def _contains_lossy_token(nodes: Iterable[Node]) -> bool:
    """
    Return True if any (possibly nested) token loses its source text.

    tinycss2 reports a string containing a raw newline and an unquoted "url()"
    containing a quote as a ``ParseError`` *token* - one which serializes to a
    fixed placeholder rather than to the text it stands for. Different CSS
    therefore serializes identically:

        'a:"x<newline>y' and 'a:"z<newline>y' -> 'a:"[bad string]'

    Such a token is not a formatting difference the comparison may ignore, it is
    input which can not be compared as tokens at all. The enclosing block has to
    be compared literally, exactly like CSS which does not parse.
    """
    for node in nodes:
        if isinstance(node, ParseError) and (node.kind in _LOSSY_ERROR_KINDS):
            return True
        if _contains_lossy_token(_nested_nodes(node)):
            return True
    return False


def _nested_nodes(node: Node) -> Sequence[Node]:
    """Return the nodes inside "node": its tokens, declarations or nested rules."""
    if isinstance(node, FunctionBlock):
        return node.arguments
    elif isinstance(node, (ParenthesesBlock, SquareBracketsBlock, CurlyBracketsBlock)):
        return node.content
    elif isinstance(node, Declaration):
        return node.value
    elif isinstance(node, QualifiedRule):
        return [*node.prelude, *node.content]
    elif isinstance(node, AtRule):
        return [*node.prelude, *(node.content or ())]
    return ()


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


# a normalization pass over a token list, as passed to "_replace_nested_tokens()"
_Normalize = Callable[[Sequence[Node]], list[Node]]


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

    Whitespace inside a function or a bracket block is just as insignificant -
    "rgb(1, 2, 3)" and "rgb(1,2,3)" are the same color - so the same separators
    apply there. Passing them down unchanged is what keeps the recursion safe in
    the two places where whitespace carries meaning: "+" and "-" are not
    separators, so "calc(1px + 2px)" keeps the whitespace CSS requires there,
    and neither is the descendant combinator, so ":not(.a .b)" still differs
    from ":not(.a.b)".
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
        nested = _replace_nested_tokens(
            token, lambda tokens: _normalize_whitespace(tokens, separators)
        )
        tokens.append(nested)
    return tokens


def _replace_nested_tokens(token: Node, normalize: _Normalize) -> Node:
    """
    Return the token with "normalize" applied to the tokens *inside* it.

    A function and a bracket block carry their tokens in a nested node, which no
    loop over a token list ever looks into. Only those have nested tokens, every
    other token is returned unchanged.

    The nodes are rebuilt rather than mutated: tinycss2 nodes use "__slots__",
    and the parsed input is not ours to change.
    """
    if isinstance(token, FunctionBlock):
        arguments = normalize(token.arguments)
        return FunctionBlock(token.source_line, token.source_column, token.name, arguments)
    elif isinstance(token, ParenthesesBlock):
        content = normalize(token.content)
        return ParenthesesBlock(token.source_line, token.source_column, content)
    elif isinstance(token, SquareBracketsBlock):
        content = normalize(token.content)
        return SquareBracketsBlock(token.source_line, token.source_column, content)
    elif isinstance(token, CurlyBracketsBlock):
        content = normalize(token.content)
        return CurlyBracketsBlock(token.source_line, token.source_column, content)
    return token


def _canonical_number_representation(representation: str, int_value: Optional[int]) -> str:
    """Return one spelling of a parsed CSS number without changing its category."""
    if int_value is not None:
        return str(int_value)

    value = Decimal(representation).normalize()
    if value == 0:
        return '0.0'
    canonical = str(value).lower()
    if ('.' not in canonical) and ('e' not in canonical):
        canonical += '.0'
    return canonical


def _normalize_numbers(all_tokens: Sequence[Node]) -> list[Node]:
    """Return tokens with equivalent numeric representations written alike."""
    tokens = []
    for token in all_tokens:
        representation = None
        if isinstance(token, (NumberToken, PercentageToken, DimensionToken)):
            representation = _canonical_number_representation(
                token.representation, token.int_value
            )

        if isinstance(token, NumberToken):
            token = NumberToken(
                token.source_line,
                token.source_column,
                token.value,
                token.int_value,
                representation,
            )
        elif isinstance(token, PercentageToken):
            token = PercentageToken(
                token.source_line,
                token.source_column,
                token.value,
                token.int_value,
                representation,
            )
        elif isinstance(token, DimensionToken):
            token = DimensionToken(
                token.source_line,
                token.source_column,
                token.value,
                token.int_value,
                representation,
                token.lower_unit,
            )
        else:
            token = _replace_nested_tokens(token, _normalize_numbers)
        tokens.append(token)
    return tokens


def _normalize_function_names(all_tokens: Sequence[Node]) -> list[Node]:
    """Return tokens with ordinary CSS function names in lower case."""
    tokens = []
    for token in all_tokens:
        if isinstance(token, FunctionBlock):
            name = token.name if token.name.startswith('--') else token.lower_name
            arguments = _normalize_function_names(token.arguments)
            token = FunctionBlock(token.source_line, token.source_column, name, arguments)
        else:
            token = _replace_nested_tokens(token, _normalize_function_names)
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

def _url_value(token: Node) -> Optional[str]:
    """
    Return the URL of a "url()" token, no matter which spelling was used.

    CSS writes the same URL in two ways and tinycss2 represents them by two
    different nodes: "url(a.png)" is a single ``URLToken`` while "url('a.png')"
    is a ``FunctionBlock`` containing a ``StringToken``. Anything else is not a
    URL which can be compared as one - "url(var(--x))" for instance is not even
    a valid url token - so it returns None.
    """
    if isinstance(token, URLToken):
        return token.value
    is_url_function = isinstance(token, FunctionBlock) and (token.lower_name == 'url')
    if not is_url_function:
        return None
    arguments = [argument for argument in token.arguments if not is_whitespace(argument)]
    if (len(arguments) == 1) and isinstance(arguments[0], StringToken):
        return arguments[0].value
    return None


def _normalize_urls(all_tokens: Sequence[Node]) -> list[Node]:
    """
    Return the tokens with every "url()" written the same way.

    "background:url(a.png)" and "background:url('a.png')" declare the same
    background, and so does the upper case "URL(a.png)" - CSS function names are
    case-insensitive. Every spelling is rewritten into the quoted form, which is
    the one that can hold any URL: the unquoted form has to escape a quote, a
    space or a parenthesis.
    """
    tokens = []
    for token in all_tokens:
        url = _url_value(token)
        if url is not None:
            token = _quoted_url(token, url)
        else:
            token = _replace_nested_tokens(token, _normalize_urls)
        tokens.append(token)
    return tokens


def _quoted_url(token: Node, url: str) -> FunctionBlock:
    """Return a "url()" holding "url" as a double-quoted string."""
    representation = f'"{serialize_string_value(url)}"'
    string = StringToken(token.source_line, token.source_column, url, representation)
    return FunctionBlock(token.source_line, token.source_column, 'url', [string])


def _is_custom_property(decl: Declaration) -> bool:
    return decl.name.startswith('--')


def _property_name(decl: Declaration) -> str:
    """
    Return the property name of a declaration as it should be compared.

    CSS property names are case-insensitive, so "COLOR" and "color" are the same
    property. Custom properties are not: "--Foo" and "--foo" are two distinct
    properties. tinycss2 lowercases those as well (its "_parse_declaration()"
    carries a "# TODO: Handle custom property names"), so "lower_name" must not
    be used for them.
    """
    if _is_custom_property(decl):
        return decl.name
    return decl.lower_name


def _normalize_custom_property_value(all_tokens: Sequence[Node]) -> list[Node]:
    """
    Return the value of a custom property with only its outer whitespace removed.

    A custom property does not have a value in the sense the other properties
    have one: it carries an arbitrary token sequence which CSS preserves as
    written and "var()" substitutes literally. None of the usual normalization
    may run on it, because none of it is safe there: "calc(var(--x) + 1px)" is
    valid for "--x:0px" and invalid for "--x:0", and the substituted text is
    observable as-is (JavaScript reads it back through
    "getComputedStyle().getPropertyValue()").

    The one thing CSS does normalize is the whitespace *around* the value: the
    custom property is defined as the token sequence "with leading and trailing
    whitespace removed", so "--x: red" and "--x:red" are the same declaration.
    tinycss2 keeps that whitespace in "Declaration.value".
    """
    tokens = list(all_tokens)
    while tokens and is_whitespace(tokens[0]):
        tokens.pop(0)
    while tokens and is_whitespace(tokens[-1]):
        tokens.pop()
    return tokens


def _normalize_declaration(decl):
    """Return a normalized copy of a tinycss2 ``Declaration``."""
    if _is_custom_property(decl):
        tokens = _normalize_custom_property_value(decl.value)
    else:
        tokens = _normalize_whitespace(decl.value, _VALUE_SEPARATORS)
        tokens = _normalize_numbers(tokens)
        tokens = _normalize_function_names(tokens)
        tokens = _strip_zero_units(tokens)
        tokens = _normalize_urls(tokens)
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
    if _is_custom_property(decl):
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
    _css_decls = tinycss2.parse_blocks_contents(
        css_declaration, skip_comments=True, skip_whitespace=True
    )
    for decl in _css_decls:
        # tinycss2 also returns `ParseError` ("color red", "*zoom:1") and
        # `AtRule` ("@media screen{color:red}") objects.
        if not isinstance(decl, Declaration):
            return None
        if _contains_lossy_token(decl.value):
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
        elif rule.type == 'declaration':
            # a declaration directly inside "@media" - invalid at the top level
            # of a stylesheet, valid in a nested rule, and a parse error to the
            # rule list parser this used to use. It keeps its position: mixing
            # declarations and rules makes the order significant.
            normalized_rules.append(_normalize_declaration(rule))
        elif rule.type == 'error':
            # keep errors: they can not be serialized but compare_stylesheet()
            # needs them to notice that it must fall back to a literal comparison
            normalized_rules.append(rule)

    return tuple(normalized_rules)


def _normalize_qualified_rule(rule):
    """Normalize a qualified rule (selector { declarations })."""
    prelude = _normalize_whitespace(rule.prelude, _PRELUDE_SEPARATORS)
    prelude = _normalize_numbers(prelude)
    prelude = _normalize_function_names(prelude)

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
    items = tinycss2.parse_blocks_contents(
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
    at_keyword = (
        rule.at_keyword if rule.at_keyword.startswith('--') else rule.lower_at_keyword
    )

    # "@import url(a.css)" is the one prelude which can contain a URL
    prelude = _normalize_whitespace(rule.prelude, _PRELUDE_SEPARATORS)
    prelude = _normalize_numbers(prelude)
    prelude = _normalize_function_names(prelude)
    prelude = _normalize_urls(prelude)

    if rule.content is None:
        # at-rules without a body (e.g. "@import url(x.css);")
        normalized_content = None
    elif _has_declaration_body(rule):
        # e.g. "@font-face" or "@page": the body holds declarations, not rules
        normalized_content = _normalize_declaration_body(rule.content)
    else:
        # the content contains nested rules (like @media)
        content_rules = tinycss2.parse_blocks_contents(
            rule.content,
            skip_comments=True,
            skip_whitespace=True,
        )
        normalized_content = list(_normalize_rule_list(content_rules))

    return AtRule(
        rule.source_line,
        rule.source_column,
        at_keyword,
        rule.lower_at_keyword,
        prelude,
        normalized_content,
    )
