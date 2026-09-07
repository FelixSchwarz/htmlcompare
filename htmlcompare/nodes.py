# SPDX-License-Identifier: MIT

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Optional, Union


__all__ = [
    'Node',
    'Element',
    'TextNode',
    'Comment',
    'ConditionalComment',
    'ConditionalCommentMarker',
    'Document',
    'Doctype',
]


@dataclass
class TextNode:
    """Represents text content in HTML."""
    content: str

    def __eq__(self, other):
        if not isinstance(other, TextNode):
            return NotImplemented
        return self.content == other.content


@dataclass
class Comment:
    """Represents an HTML comment."""
    content: str

    def __eq__(self, other):
        if not isinstance(other, Comment):
            return NotImplemented
        return self.content == other.content


@dataclass
class Doctype:
    """
    Represents a DOCTYPE declaration.

    For HTML5: name='html', public_id='', system_id=''
    For XHTML: name='html', public_id='-//W3C//DTD XHTML 1.0...', system_id='http://...'
    """
    name: str  # typically 'html'
    public_id: str = ''
    system_id: str = ''

    def __eq__(self, other):
        if not isinstance(other, Doctype):
            return NotImplemented
        return (
            self.name == other.name
            and self.public_id == other.public_id
            and self.system_id == other.system_id
        )


@dataclass(frozen=True)
class ConditionalComment:
    """
    Represents an IE conditional comment.

    Example: <!--[if IE]><p>IE only</p><![endif]-->
    """
    condition: str  # e.g., "IE", "lt IE 9", "gte IE 8"
    children: list['Node'] = field(default_factory=list)

    def __eq__(self, other):
        if not isinstance(other, ConditionalComment):
            return NotImplemented
        return self.condition == other.condition and self.children == other.children


@dataclass(frozen=True)
class ConditionalCommentMarker:
    """
    Represents one marker of a downlevel-revealed conditional comment.

    The downlevel-hidden form encloses its HTML in the comment itself, so it
    becomes a single `ConditionalComment` node. The revealed form does not -
    its HTML is visible to every browser and only the two markers are comments:

        <!--[if !mso]><!--><span>x</span><!--<![endif]-->

    html5lib therefore reports two ordinary comments with the enclosed HTML as
    their sibling. Keep them as siblings as well rather than re-nesting the HTML
    into a `ConditionalComment`: that matches the DOM and it survives an
    unbalanced marker, which a real-world document may well contain.

    Example: condition="!mso", is_start=True
    """
    condition: str  # always empty for a closing marker
    is_start: bool

    def __eq__(self, other):
        if not isinstance(other, ConditionalCommentMarker):
            return NotImplemented
        return (self.condition == other.condition) and (self.is_start == other.is_start)


@dataclass
class Element:
    """Represents an HTML element with tag, attributes, and children."""
    tag: str
    attributes: dict[str, str] = field(default_factory=dict)
    children: Sequence['Node'] = field(default_factory=list)
    is_self_closing: bool = False

    def __eq__(self, other):
        if not isinstance(other, Element):
            return NotImplemented
        return (
            self.tag == other.tag
            and self.attributes == other.attributes
            and self.children == other.children
            and self.is_self_closing == other.is_self_closing
        )


@dataclass
class Document:
    """Represents a parsed HTML document (list of root nodes)."""
    children: list['Node'] = field(default_factory=list)
    doctype: Optional['Doctype'] = None

    prefix: str = ''
    """
    Everything before the DOCTYPE, e.g. template metadata a generator emitted
    ahead of the document. Empty when the document has no DOCTYPE at all.
    """

    def __eq__(self, other):
        if not isinstance(other, Document):
            return NotImplemented
        return (
            self.children == other.children
            and self.doctype == other.doctype
            and self.prefix == other.prefix
        )


# Type alias for any node type
Node = Union[Element, TextNode, Comment, ConditionalComment, ConditionalCommentMarker]
