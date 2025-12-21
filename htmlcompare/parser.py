# SPDX-License-Identifier: MIT

import re
import xml.etree.ElementTree as ET
from collections.abc import Sequence

import html5lib

from htmlcompare.nodes import Comment, ConditionalComment, Document, Element, TextNode


__all__ = ['parse_html']


_CONDITIONAL_START_RE = re.compile(r'^\[if\s+([^\]]+)\]>')
_CONDITIONAL_END_RE = re.compile(r'<!\[endif\]$')


def parse_html(html_string: str) -> Document:
    """
    Parse an HTML string into a Document tree of Node objects.

    Uses html5lib for HTML5-compliant parsing, then converts the
    resulting tree into our internal node representation.
    """
    html_element = html5lib.parse(html_string, namespaceHTMLElements=False)
    html_node = _element_to_node(html_element)

    return Document(children=[html_node])


def _element_to_node(element) -> Element:
    # Extract tag name (removes any namespace prefix)
    tag = element.tag
    if '}' in tag:
        tag = tag.split('}', 1)[1]

    attributes = {}
    for key, value in element.attrib.items():
        if isinstance(key, tuple):
            _namespace, attr_name = key
        else:
            attr_name = key
        attributes[attr_name] = value

    children = _convert_children(element)
    return Element(tag=tag, attributes=attributes, children=children)


def _convert_children(element) -> Sequence[Element | TextNode | Comment | ConditionalComment]:
    children: list[Element | TextNode | Comment | ConditionalComment] = []
    if element.text:
        # leading text before any child elements
        children.append(TextNode(content=element.text))
    for child in element:
        if _is_comment(child):
            comment_content = child.text or ''
            conditional = _parse_conditional_comment(comment_content)
            if conditional is not None:
                children.append(conditional)
            else:
                children.append(Comment(content=comment_content))
        else:
            # regular element
            node = _element_to_node(child)
            children.append(node)
        # tail text after this child element
        if child.tail:
            children.append(TextNode(content=child.tail))
    return children


def _is_comment(element) -> bool:
    # html5lib represents comments with a special function tag
    return callable(element.tag) or element.tag == ET.Comment


def _parse_conditional_comment(content: str) -> ConditionalComment | None:
    """
    Parse an IE conditional comment if the content matches the pattern.

    Returns a ConditionalComment node if the content is a conditional comment,
    otherwise returns None.
    """
    start_match = _CONDITIONAL_START_RE.match(content)
    end_match = _CONDITIONAL_END_RE.search(content)
    if not (start_match and end_match):
        return None

    condition = start_match.group(1).strip()
    # extract the HTML content between the condition and the endif
    inner_html = content[start_match.end():end_match.start()]
    inner_doc = parse_html(inner_html)
    # The inner HTML gets wrapped in html/head/body, extract the body children
    inner_children = _extract_body_children(inner_doc)
    return ConditionalComment(condition=condition, children=inner_children)


def _extract_body_children(doc: Document) -> list:
    if not doc.children:
        return []
    html_elem = doc.children[0]
    if not isinstance(html_elem, Element) or html_elem.tag != 'html':
        return []
    for child in html_elem.children:
        if isinstance(child, Element) and child.tag == 'body':
            return list(child.children)
    return []
