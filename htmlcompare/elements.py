# SPDX-License-Identifier: MIT


__all__ = [
    'is_block_element',
    'is_inline_element',
    'is_preformatted_element',
    'is_self_closing_significant',
]

# Block-level elements where whitespace between them is typically insignificant.
# Based on HTML5 spec and browser rendering behavior.
BLOCK_ELEMENTS = frozenset({
    # Document sections
    'html', 'head', 'body',
    # Content sectioning
    'address', 'article', 'aside', 'footer', 'header', 'hgroup',
    'main', 'nav', 'section',
    # Text content (block)
    'blockquote', 'dd', 'div', 'dl', 'dt', 'figcaption', 'figure',
    'hr', 'li', 'menu', 'ol', 'p', 'pre', 'ul',
    # Table content
    'caption', 'col', 'colgroup', 'table', 'tbody', 'td', 'tfoot',
    'th', 'thead', 'tr',
    # Form elements (block-like)
    'fieldset', 'form', 'legend', 'optgroup', 'option',
    # Other block elements
    'details', 'dialog', 'summary',
    # Headings
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    # Metadata (typically not rendered)
    'base', 'link', 'meta', 'noscript', 'script', 'style', 'template', 'title',
    # VML elements (used in Outlook conditional comments)
    'v:image', 'v:rect', 'v:fill', 'v:stroke', 'v:textbox', 'v:shape',
    'v:shapetype', 'v:roundrect', 'v:oval', 'v:line', 'v:polyline',
    'v:group', 'v:background',
    # Microsoft Office elements
    'o:p', 'o:wrapblock',
})

# Inline elements where whitespace is significant for rendering.
INLINE_ELEMENTS = frozenset({
    # Text semantics
    'a', 'abbr', 'b', 'bdi', 'bdo', 'br', 'cite', 'code', 'data',
    'dfn', 'em', 'i', 'kbd', 'mark', 'q', 'rp', 'rt', 'ruby',
    's', 'samp', 'small', 'span', 'strong', 'sub', 'sup', 'time',
    'u', 'var', 'wbr',
    # Edits
    'del', 'ins',
    # Embedded content (inline by default)
    'audio', 'canvas', 'embed', 'iframe', 'img', 'math', 'object',
    'picture', 'svg', 'video',
    # Form elements (inline by default)
    'button', 'datalist', 'input', 'label', 'meter', 'output',
    'progress', 'select', 'textarea',
})

# Elements that preserve whitespace (like <pre>).
PREFORMATTED_ELEMENTS = frozenset({
    'pre', 'code', 'textarea', 'script', 'style',
})


def is_block_element(tag: str) -> bool:
    return tag.lower() in BLOCK_ELEMENTS


def is_inline_element(tag: str) -> bool:
    return tag.lower() in INLINE_ELEMENTS


def is_preformatted_element(tag: str) -> bool:
    """Return True if the element preserves whitespace."""
    return tag.lower() in PREFORMATTED_ELEMENTS


# HTML5 void elements - these are always self-closing by definition.
# For these elements, <br>, <br/>, and <br /> are semantically identical.
# https://html.spec.whatwg.org/multipage/syntax.html#void-elements
HTML5_VOID_ELEMENTS = frozenset({
    'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
    'link', 'meta', 'source', 'track', 'wbr',
})

# VML (Vector Markup Language) elements used in Microsoft Office/Outlook.
# These are XML-based and self-closing syntax matters for correct rendering.
VML_ELEMENTS = frozenset({
    'v:background', 'v:fill', 'v:formulas', 'v:group', 'v:image',
    'v:imagedata', 'v:line', 'v:oval', 'v:path', 'v:polyline',
    'v:rect', 'v:roundrect', 'v:shadow', 'v:shape', 'v:shapetype',
    'v:stroke', 'v:textbox', 'v:textpath',
    # Office namespace elements
    'o:lock', 'o:wrapblock',
})

# HTML elements where self-closing syntax can cause issues or has different meaning.
# - script: <script /> may not work correctly in all browsers
# - style: similar to script
# - textarea: <textarea /> is invalid and may cause rendering issues
# - title: empty title vs self-closing can behave differently
# - iframe: self-closing iframe may not work in some browsers
SELF_CLOSING_SIGNIFICANT_HTML = frozenset({
    'script', 'style', 'textarea', 'title', 'iframe',
})


def is_self_closing_significant(tag: str) -> bool:
    """
    Return True if self-closing syntax is significant for this tag.

    For these elements, <tag /> vs <tag></tag> or <tag> matters and
    should be flagged as a difference.

    Returns False for:
    - HTML5 void elements (br, img, etc.) where self-closing is always implied
    - Regular HTML elements where it doesn't matter

    Returns True for:
    - VML elements (v:rect, v:fill, etc.)
    - Certain HTML elements (script, style, textarea, title, iframe)
    """
    tag_lower = tag.lower()

    # Void elements are always self-closing - syntax doesn't matter
    if tag_lower in HTML5_VOID_ELEMENTS:
        return False

    if tag_lower in VML_ELEMENTS:
        return True

    # Check for VML/Office namespace pattern (v:* or o:*)
    if ':' in tag_lower:
        prefix = tag_lower.split(':')[0]
        if prefix in ('v', 'o'):
            return True

    if tag_lower in SELF_CLOSING_SIGNIFICANT_HTML:
        return True
    return False
