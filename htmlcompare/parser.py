# SPDX-License-Identifier: MIT

import xml.etree.ElementTree as ET

import html5lib

from htmlcompare.nodes import Comment, Document, Element, TextNode


__all__ = ['parse_html']


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


def _convert_children(element) -> list:
    children = []
    if element.text:
        # leading text before any child elements
        children.append(TextNode(content=element.text))
    for child in element:
        if _is_comment(child):
            children.append(Comment(content=child.text or ''))
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
