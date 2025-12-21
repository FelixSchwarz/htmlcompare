# SPDX-License-Identifier: MIT

import re

from htmlcompare.elements import is_block_element
from htmlcompare.nodes import Comment, ConditionalComment, Document, Element, Node, TextNode
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


def _has_inline_elements(children: list[Node], options: CompareOptions) -> bool:
    """
    Check if children list contains inline elements.

    This determines whether whitespace between text nodes and inline elements
    is significant. If there are inline elements, spaces around them matter.

    Note: This checks what will remain AFTER normalization (comments removed).
    """
    for child in children:
        # skip comments that will be removed
        if isinstance(child, Comment) and options.ignore_comments:
            continue
        if isinstance(child, ConditionalComment) and options.ignore_conditional_comments:
            continue
        if isinstance(child, Element):
            if not is_block_element(child.tag):
                return True
    return False


def _has_significant_text(children: list[Node], options: CompareOptions) -> bool:
    """
    Check if children list contains non-whitespace text content.

    This helps determine if whitespace is significant: if there's text
    mixed with inline elements, whitespace between them matters.
    """
    for child in children:
        if isinstance(child, TextNode):
            if child.content.strip():
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
    elif isinstance(node, ConditionalComment):
        return _normalize_conditional_comment(node, options)
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
    # 2. OR the element contains inline elements AND significant text as children
    #
    # If a block element contains only inline elements (no text), or only text
    # (no inline elements), we can strip leading/trailing whitespace.
    # Whitespace only matters when text is ADJACENT to inline elements.
    has_inline_children = _has_inline_elements(element.children, options)
    has_text_content = _has_significant_text(element.children, options)
    # Whitespace is significant only when there's both inline elements AND text
    inline_context = has_inline_children and has_text_content
    children_in_block_context = is_block_element(element.tag) and not inline_context

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


def _normalize_conditional_comment(
    node: ConditionalComment,
    options: CompareOptions,
) -> ConditionalComment | None:
    """
    Normalize a conditional comment.

    Conditional comments are compared by default, unlike regular comments.
    They are only removed when ignore_conditional_comments is True.
    """
    if options.ignore_conditional_comments:
        return None
    normalized_children = _normalize_children(
        node.children,
        in_block_context=True,
        options=options,
    )
    return ConditionalComment(
        condition=node.condition,
        children=normalized_children,
    )
