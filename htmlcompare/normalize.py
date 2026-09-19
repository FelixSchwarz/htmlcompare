# SPDX-License-Identifier: MIT

import re
from collections.abc import Sequence
from typing import Optional

from htmlcompare.elements import (
    is_atomic_inline_element,
    is_block_element,
    is_forced_line_break,
)
from htmlcompare.nodes import (
    Comment,
    ConditionalComment,
    ConditionalCommentMarker,
    Document,
    Element,
    Node,
    TextNode,
)
from htmlcompare.options import CompareOptions


__all__ = ['normalize_tree']

_WHITESPACE_RE = re.compile(r'\s+')
_DEFAULT_OPTIONS = CompareOptions()


def normalize_tree(doc: Document, options: Optional[CompareOptions] = None) -> Document:
    """
    Normalize a document tree for comparison.

    This removes insignificant whitespace between block elements while
    preserving significant whitespace in inline contexts.
    """
    if options is None:
        options = _DEFAULT_OPTIONS
    normalized_children = _normalize_children(doc.children, options)
    normalized_children = _trim_line_boundary_whitespace(normalized_children)
    return Document(
        children=normalized_children,
        doctype=doc.doctype,
        # the point of the prefix is exact preservation, so only the whitespace
        # separating it from the DOCTYPE is insignificant
        prefix=doc.prefix.strip(),
    )


def _normalize_children(
    children: Sequence[Node],
    options: CompareOptions,
) -> list[Node]:
    result: list[Node] = []
    for child in _filter_ignored_nodes(children, options):
        normalized = _normalize_node(child, options)
        if normalized is not None:
            _append_normalized_node(result, normalized)
    return result


def _append_normalized_node(result: list[Node], node: Node) -> None:
    """Append a node, joining text which only an ignored comment separated."""
    if result and isinstance(result[-1], TextNode) and isinstance(node, TextNode):
        result[-1].content = _WHITESPACE_RE.sub(' ', result[-1].content + node.content)
    else:
        result.append(node)


def _filter_ignored_nodes(
    children: Sequence[Node],
    options: CompareOptions,
) -> list[Node]:
    """Return the children which participate in normalization and comparison."""
    return [child for child in children if not _should_ignore_node(child, options)]


def _should_ignore_node(node: Node, options: CompareOptions) -> bool:
    if isinstance(node, Comment):
        return options.ignore_comments
    if isinstance(node, (ConditionalComment, ConditionalCommentMarker)):
        return options.ignore_conditional_comments
    return False


def _normalize_node(node: Node, options: CompareOptions) -> Optional[Node]:
    """
    Normalize a single node.

    Returns None for comments which are ignored by the comparison options.
    """
    if isinstance(node, TextNode):
        return _normalize_text_node(node)
    elif isinstance(node, Element):
        return _normalize_element(node, options)
    elif isinstance(node, Comment):
        return None if options.ignore_comments else node
    elif isinstance(node, ConditionalComment):
        return _normalize_conditional_comment(node, options)
    elif isinstance(node, ConditionalCommentMarker):
        # a marker is conditional-comment syntax, not a comment: "ignore_comments"
        # must not drop it, only "ignore_conditional_comments" may
        return None if options.ignore_conditional_comments else node
    return node


def _normalize_text_node(node: TextNode) -> Optional[TextNode]:
    """Collapse a whitespace run without deciding yet whether it renders."""
    normalized = _WHITESPACE_RE.sub(' ', node.content)
    if normalized == '':
        return None
    return TextNode(content=normalized)


def _normalize_element(element: Element, options: CompareOptions) -> Element:
    """Normalize an element and its children."""
    normalized_children = _normalize_children(element.children, options)
    if is_block_element(element.tag):
        normalized_children = _trim_line_boundary_whitespace(normalized_children)

    return Element(
        tag=element.tag,
        attributes=element.attributes,
        children=normalized_children,
        is_self_closing=element.is_self_closing,
    )


def _trim_line_boundary_whitespace(children: list[Node]) -> list[Node]:
    """Remove collapsed spaces which occur at the start or end of a line."""
    _trim_leading_whitespace(children, has_content=False)
    _trim_trailing_whitespace(children, has_content=False)
    return _remove_empty_text_nodes(children)


def _trim_leading_whitespace(children: Sequence[Node], has_content: bool) -> bool:
    """Trim line-start spaces in document order and return the final line state."""
    for child in children:
        if isinstance(child, TextNode):
            if not has_content:
                child.content = child.content.lstrip(' ')
            if child.content:
                has_content = True
        elif isinstance(child, Element):
            if _is_line_boundary(child):
                has_content = False
            else:
                has_content = _trim_leading_whitespace(child.children, has_content)
                if is_atomic_inline_element(child.tag):
                    has_content = True
    return has_content


def _trim_trailing_whitespace(children: Sequence[Node], has_content: bool) -> bool:
    """Trim line-end spaces in reverse document order and return the line state."""
    for child in reversed(children):
        if isinstance(child, TextNode):
            if not has_content:
                child.content = child.content.rstrip(' ')
            if child.content:
                has_content = True
        elif isinstance(child, Element):
            if _is_line_boundary(child):
                has_content = False
            else:
                has_content = _trim_trailing_whitespace(child.children, has_content)
                if is_atomic_inline_element(child.tag):
                    has_content = True
    return has_content


def _is_line_boundary(element: Element) -> bool:
    return is_block_element(element.tag) or is_forced_line_break(element.tag)


def _remove_empty_text_nodes(children: Sequence[Node]) -> list[Node]:
    result = []
    for child in children:
        if isinstance(child, TextNode) and not child.content:
            continue
        if isinstance(child, Element):
            child.children = _remove_empty_text_nodes(child.children)
        result.append(child)
    return result


def _normalize_conditional_comment(
    node: ConditionalComment,
    options: CompareOptions,
) -> Optional[ConditionalComment]:
    """
    Normalize a conditional comment.

    Conditional comments are compared by default, unlike regular comments.
    They are only removed when ignore_conditional_comments is True.
    """
    if options.ignore_conditional_comments:
        return None
    normalized_children = _normalize_children(node.children, options)
    normalized_children = _trim_line_boundary_whitespace(normalized_children)
    return ConditionalComment(
        condition=node.condition,
        children=normalized_children,
    )
