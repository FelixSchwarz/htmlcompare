# SPDX-License-Identifier: MIT

from typing import Optional

from htmlcompare.nodes import Comment, ConditionalComment, Document, Element, TextNode
from htmlcompare.parser import parse_html as parse_html2


def test_parse_empty_document():
    doc = parse_html2('')
    assert isinstance(doc, Document)
    # html5lib always creates html/head/body structure
    assert len(doc.children) == 1
    assert doc.children[0].tag == 'html'


def test_parse_single_element():
    doc = parse_html2('<div></div>')
    html, = doc.children
    body = _find_first_child_with_tag(html, 'body')
    div = _find_first_child_with_tag(body, 'div')
    assert div is not None
    assert div.tag == 'div'
    assert div.attributes == {}
    assert div.children == []


def test_parse_element_with_text():
    doc = parse_html2('<p>Hello</p>')
    html, = doc.children
    body = _find_first_child_with_tag(html, 'body')
    p = _find_first_child_with_tag(body, 'p')
    assert p is not None
    assert p.tag == 'p'
    assert len(p.children) == 1
    assert p.children[0] == TextNode('Hello')


def test_parse_nested_elements():
    doc = parse_html2('<div><span>x</span></div>')
    html, = doc.children
    body = _find_first_child_with_tag(html, 'body')
    div = _find_first_child_with_tag(body, 'div')
    assert div is not None
    assert len(div.children) == 1
    span = div.children[0]
    assert isinstance(span, Element)
    assert span.tag == 'span'
    assert span.children == [TextNode('x')]


def test_parse_element_with_attributes():
    doc = parse_html2('<div class="foo" id="bar"></div>')
    html, = doc.children
    body = _find_first_child_with_tag(html, 'body')
    div = _find_first_child_with_tag(body, 'div')
    assert div.attributes == {'class': 'foo', 'id': 'bar'}


def test_parse_self_closing_element():
    doc = parse_html2('<br>')
    html, = doc.children
    body = _find_first_child_with_tag(html, 'body')
    br = _find_first_child_with_tag(body, 'br')
    assert br is not None
    assert br.tag == 'br'


def test_parse_multiple_children():
    doc = parse_html2('<div><p>a</p><p>b</p></div>')
    html, = doc.children
    body = _find_first_child_with_tag(html, 'body')
    div = _find_first_child_with_tag(body, 'div')
    assert len(div.children) == 2
    assert div.children[0].tag == 'p'
    assert div.children[1].tag == 'p'
    assert div.children[0].children == [TextNode('a')]
    assert div.children[1].children == [TextNode('b')]


def test_parse_mixed_content():
    doc = parse_html2('<p>Hello <b>world</b>!</p>')
    html, = doc.children
    body = _find_first_child_with_tag(html, 'body')
    p = _find_first_child_with_tag(body, 'p')
    assert len(p.children) == 3
    assert p.children[0] == TextNode('Hello ')
    assert isinstance(p.children[1], Element)
    assert p.children[1].tag == 'b'
    assert p.children[1].children == [TextNode('world')]
    assert p.children[2] == TextNode('!')


def test_parse_comment():
    doc = parse_html2('<div><!-- comment --></div>')
    html, = doc.children
    body = _find_first_child_with_tag(html, 'body')
    div = _find_first_child_with_tag(body, 'div')
    assert len(div.children) == 1
    assert isinstance(div.children[0], Comment)
    assert div.children[0].content == ' comment '


def test_parse_comment_with_text():
    doc = parse_html2('<div>before<!-- comment -->after</div>')
    html, = doc.children
    body = _find_first_child_with_tag(html, 'body')
    div = _find_first_child_with_tag(body, 'div')
    assert len(div.children) == 3
    assert div.children[0] == TextNode('before')
    assert isinstance(div.children[1], Comment)
    assert div.children[2] == TextNode('after')


def test_parse_whitespace_preserved():
    doc = parse_html2('<p>  spaces  </p>')
    html, = doc.children
    body = _find_first_child_with_tag(html, 'body')
    p = _find_first_child_with_tag(body, 'p')
    assert p.children == [TextNode('  spaces  ')]


def test_parse_attribute_with_empty_value():
    doc = parse_html2('<div class=""></div>')
    html, = doc.children
    body = _find_first_child_with_tag(html, 'body')
    div = _find_first_child_with_tag(body, 'div')
    assert div.attributes == {'class': ''}


def test_parse_img_with_alt():
    doc = parse_html2('<img alt="">')
    html, = doc.children
    body = _find_first_child_with_tag(html, 'body')
    img = _find_first_child_with_tag(body, 'img')
    assert img.attributes == {'alt': ''}


def test_parse_deeply_nested():
    doc = parse_html2('<div><ul><li><a href="#">link</a></li></ul></div>')
    html, = doc.children
    body = _find_first_child_with_tag(html, 'body')
    div = _find_first_child_with_tag(body, 'div')
    ul = div.children[0]
    li = ul.children[0]
    a = li.children[0]
    assert a.tag == 'a'
    assert a.attributes == {'href': '#'}
    assert a.children == [TextNode('link')]


def test_parse_style_attribute():
    doc = parse_html2('<div style="color: red; font-weight: bold"></div>')
    html, = doc.children
    body = _find_first_child_with_tag(html, 'body')
    div = _find_first_child_with_tag(body, 'div')
    assert div.attributes == {'style': 'color: red; font-weight: bold'}


def test_parse_multiple_classes():
    doc = parse_html2('<div class="foo bar baz"></div>')
    html, = doc.children
    body = _find_first_child_with_tag(html, 'body')
    div = _find_first_child_with_tag(body, 'div')
    assert div.attributes == {'class': 'foo bar baz'}


def test_parse_head_and_body():
    doc = parse_html2('<html><head><title>Test</title></head><body><p>Hello</p></body></html>')
    html, = doc.children
    assert html.tag == 'html'
    head = _find_first_child_with_tag(html, 'head')
    body = _find_first_child_with_tag(html, 'body')
    assert head is not None
    assert body is not None
    title = _find_first_child_with_tag(head, 'title')
    assert title.children == [TextNode('Test')]


def test_parse_script_content():
    doc = parse_html2('<script>var x = 1;</script>')
    html, = doc.children
    head = _find_first_child_with_tag(html, 'head')
    script = _find_first_child_with_tag(head, 'script')
    assert script is not None
    assert script.children == [TextNode('var x = 1;')]


def test_parse_style_tag_content():
    doc = parse_html2('<style>.foo { color: red; }</style>')
    html, = doc.children
    head = _find_first_child_with_tag(html, 'head')
    style = _find_first_child_with_tag(head, 'style')
    assert style is not None
    assert style.children == [TextNode('.foo { color: red; }')]


def test_parses_conditional_comment():
    doc = parse_html2('<div><!--[if IE]><p>IE only</p><![endif]--></div>')
    html, = doc.children
    body = _find_first_child_with_tag(html, 'body')
    div = _find_first_child_with_tag(body, 'div')
    assert len(div.children) == 1
    cc, = div.children
    assert isinstance(cc, ConditionalComment)
    assert cc.condition == 'IE'
    # Children should contain the <p> element
    p, = cc.children
    assert isinstance(p, Element)
    assert p.tag == 'p'


def test_parses_conditional_comment_with_comparison():
    doc = parse_html2("<div><!--[if lt IE 9]><script src='ie8.js'></script><![endif]--></div>")
    html, = doc.children
    body = _find_first_child_with_tag(html, 'body')
    div = _find_first_child_with_tag(body, 'div')
    cc, = div.children
    assert isinstance(cc, ConditionalComment)
    assert cc.condition == 'lt IE 9'


def test_parses_conditional_comment_gte():
    doc = parse_html2('<head><!--[if gte IE 8]><link rel="stylesheet" href="ie8.css"><![endif]--></head>')  # noqa: E501
    html, = doc.children
    head = _find_first_child_with_tag(html, 'head')
    assert len(head.children) >= 1
    cc, = head.children
    assert isinstance(cc, ConditionalComment)
    assert cc.condition == 'gte IE 8'


def test_regular_comment_not_parsed_as_conditional():
    doc = parse_html2('<div><!-- just a regular comment --></div>')
    html = doc.children[0]
    body = _find_first_child_with_tag(html, 'body')
    div = _find_first_child_with_tag(body, 'div')
    comment, = div.children
    assert isinstance(comment, Comment)
    assert comment.content == ' just a regular comment '


def _find_first_child_with_tag(element: Element, tag: str) -> Optional[Element]:
    for child in element.children:
        if isinstance(child, Element) and child.tag == tag:
            return child
    return None
