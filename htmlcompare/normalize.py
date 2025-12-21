# SPDX-License-Identifier: MIT

import re

from htmlcompare.elements import is_block_element
from htmlcompare.nodes import Comment, Document, Element, Node, TextNode
from htmlcompare.options import CompareOptions


__all__ = ['normalize_tree']

_WHITESPACE_RE = re.compile(r'\s+')
_DEFAULT_OPTIONS = CompareOptions()


def normalize_tree(doc: Document, options: CompareOptions | None = None) -> Document:
    """
    Normalize a document tree for comparison.

    This removes insignificant whitespace between block elements while
    preserving significant whitespace in inline contexts.
    """
    if options is None:
        options = _DEFAULT_OPTIONS
    normalized_children = _normalize_children(doc.children, in_block_context=True, options=options)
    return Document(children=normalized_children)


def _has_inline_elements(children: list[Node]) -> bool:
    """
    Check if children list contains inline elements.

    This determines whether whitespace between text nodes and inline elements
    is significant. If there are inline elements, spaces around them matter.
    """
    for child in children:
        if isinstance(child, Element):
            if not is_block_element(child.tag):
                return True
    return False


def _normalize_children(
    children: list[Node],
    in_block_context: bool,
    options: CompareOptions,
) -> list[Node]:
    result: list[Node] = []
    for child in children:
        normalized = _normalize_node(child, in_block_context, options)
        if normalized is not None:
            result.append(normalized)
    return result


def _normalize_node(node: Node, in_block_context: bool, options: CompareOptions) -> Node | None:
    """
    Normalize a single node.

    Returns None if the node should be removed (whitespace-only text in block context,
    or comments when ignore_comments is True).
    """
    if isinstance(node, TextNode):
        return _normalize_text_node(node, in_block_context)
    elif isinstance(node, Element):
        return _normalize_element(node, options)
    elif isinstance(node, Comment):
        return None if options.ignore_comments else node
    return node


def _normalize_text_node(node: TextNode, in_block_context: bool) -> TextNode | None:
    """
    Normalize a text node.

    In block context (only block elements as siblings), whitespace-only text
    nodes are removed, and leading/trailing whitespace is stripped.

    In inline context (mixed with inline elements or text), consecutive
    whitespace is collapsed to a single space, preserving significant
    whitespace for rendering.
    """
    if in_block_context:
        # remove whitespace-only text nodes between block elements
        if node.content.strip() == '':
            return None
        # normalize leading/trailing whitespace in block context
        # also collapse internal whitespace
        normalized = _WHITESPACE_RE.sub(' ', node.content).strip()
        return TextNode(content=normalized)
    else:
        # In inline context: collapse consecutive whitespace to single space
        # but preserve leading/trailing spaces (they're significant)
        normalized = _WHITESPACE_RE.sub(' ', node.content)
        if normalized == '':
            return None
        return TextNode(content=normalized)


def _normalize_element(element: Element, options: CompareOptions) -> Element:
    """Normalize an element and its children."""
    # Determine if children are in block context or inline context.
    # Whitespace is significant (inline context) if:
    # 1. The element is inline (not a block element)
    # 2. OR the element contains inline elements as children
    #
    # If a block element contains only text (no inline elements),
    # we can strip leading/trailing whitespace.
    has_inline_children = _has_inline_elements(element.children)
    children_in_block_context = is_block_element(element.tag) and not has_inline_children

    normalized_children = _normalize_children(
        element.children,
        in_block_context=children_in_block_context,
        options=options,
    )

    return Element(
        tag=element.tag,
        attributes=element.attributes,
        children=normalized_children,
    )
