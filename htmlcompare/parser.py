# SPDX-License-Identifier: MIT

import re
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from typing import Optional, Union

import html5lib

from htmlcompare.nodes import Comment, ConditionalComment, Doctype, Document, Element, TextNode


__all__ = ['parse_html']


_CONDITIONAL_START_RE = re.compile(r'^\[if\s+([^\]]+)\]>')
_CONDITIONAL_END_RE = re.compile(r'<!\[endif\]$')

# Marker attribute to track self-closing tags through html5lib parsing
_SELF_CLOSING_MARKER = 'data-htmlcompare-self-closing'

# pattern to detect self-closing tags: <tag ... /> (but not <!-- or <!)
# captures: (1) tag name, (2) attributes section
_SELF_CLOSING_TAG_PATTERN = rb'<([a-zA-Z][a-zA-Z0-9:_-]*)(\s[^>]*)?\s*/>'


def _mark_self_closing_tags(html_string: Union[str, bytes]) -> Union[str, bytes]:
    """
    Pre-process HTML to mark self-closing tags with a marker attribute.

    This is needed because html5lib normalizes self-closing syntax away.
    We inject a marker attribute that survives parsing.
    """
    if not isinstance(html_string, (str, bytes)):
        raise TypeError("html_string must be str or bytes")
    elif isinstance(html_string, bytes):
        def _inject_bytes_marker_attribute(match) -> bytes:
            tag = match.group(1)
            attrs = match.group(2) or b''
            _marker = f' {_SELF_CLOSING_MARKER}="true" '.encode('utf-8')
            return b'<' + tag + attrs + _marker + b'/>'
        _regex = re.compile(_SELF_CLOSING_TAG_PATTERN, re.DOTALL)
        return _regex.sub(_inject_bytes_marker_attribute, html_string)
    else:
        def _inject_str_marker_attribute(match) -> str:
            tag = match.group(1)
            attrs = match.group(2) or ''
            return f'<{tag}{attrs} {_SELF_CLOSING_MARKER}="true" />'
        pattern = _SELF_CLOSING_TAG_PATTERN.decode('utf-8')
        _SELF_CLOSING_TAG_RE = re.compile(pattern, re.DOTALL)
        return _SELF_CLOSING_TAG_RE.sub(_inject_str_marker_attribute, html_string)


def parse_html(html_string: Union[str, bytes]) -> Document:
    """
    Parse an HTML string into a Document tree of Node objects.

    Uses html5lib for HTML5-compliant parsing, then converts the
    resulting tree into our internal node representation.
    """
    TreeBuilder = html5lib.getTreeBuilder('etree')
    parser = html5lib.HTMLParser(tree=TreeBuilder, namespaceHTMLElements=False)
    marked_html = _mark_self_closing_tags(html_string)
    parser.parse(marked_html)

    doctype = _extract_doctype(parser.tree.document)
    html_element = parser.tree.getDocument()
    html_node = _element_to_node(html_element)
    return Document(children=[html_node], doctype=doctype)


def _extract_doctype(document) -> Optional[Doctype]:
    for child in document.childNodes:
        element = getattr(child, '_element', None)
        if element is None:
            continue
        is_document_type_node = (getattr(element, 'tag', None) == '<!DOCTYPE>')
        if is_document_type_node:
            name = element.text or ''
            public_id = element.attrib.get('publicId', '')
            system_id = element.attrib.get('systemId', '')
            return Doctype(name=name, public_id=public_id, system_id=system_id)
    return None


def _element_to_node(element) -> Element:
    # Extract tag name (removes any namespace prefix)
    tag = element.tag
    if '}' in tag:
        tag = tag.split('}', 1)[1]

    is_self_closing = False
    attributes = {}
    for key, value in element.attrib.items():
        if isinstance(key, tuple):
            _namespace, attr_name = key
        else:
            attr_name = key

        if attr_name == _SELF_CLOSING_MARKER:
            is_self_closing = True
            # don't include marker in final attributes
            continue

        attributes[attr_name] = value

    children = _convert_children(element)
    return Element(
        tag=tag,
        attributes=attributes,
        children=children,
        is_self_closing=is_self_closing,
    )


def _convert_children(element) -> Sequence[Union[Element, TextNode, Comment, ConditionalComment]]:
    children: list[Union[Element, TextNode, Comment, ConditionalComment]] = []
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



def _parse_conditional_comment(content: str) -> Optional[ConditionalComment]:
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
