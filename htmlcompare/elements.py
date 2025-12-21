# SPDX-License-Identifier: MIT


__all__ = ['is_block_element', 'is_inline_element', 'is_preformatted_element']

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
