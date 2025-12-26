# SPDX-License-Identifier: MIT

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Union


__all__ = ['Node', 'Element', 'TextNode', 'Comment', 'ConditionalComment', 'Document']


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

    def __eq__(self, other):
        if not isinstance(other, Document):
            return NotImplemented
        return self.children == other.children


# Type alias for any node type
Node = Union[Element, TextNode, Comment, ConditionalComment]
