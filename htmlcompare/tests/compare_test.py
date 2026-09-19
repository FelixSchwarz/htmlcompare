# SPDX-License-Identifier: MIT


import html

import pytest

from htmlcompare.compare import compare_html
from htmlcompare.compare_css import compare_css, compare_stylesheet
from htmlcompare.options import CompareOptions
from htmlcompare.result import DifferenceType


def _style_attribute(css: str) -> str:
    """Return an element whose "style" attribute holds "css", quotes and all."""
    return f"<p style='{html.escape(css, quote=True)}'>x</p>"


def test_identical_documents_are_equal():
    result = compare_html('<div></div>', '<div></div>')
    assert result.is_equal
    assert result.differences == []


def test_identical_nested_documents_are_equal():
    result = compare_html(
        '<div><p>hello</p></div>',
        '<div><p>hello</p></div>',
    )
    assert result.is_equal


def test_identical_with_attributes_are_equal():
    result = compare_html(
        '<div class="foo" id="bar"></div>',
        '<div class="foo" id="bar"></div>',
    )
    assert result.is_equal


def test_detects_different_tags():
    result = compare_html('<div></div>', '<span></span>')
    assert not result.is_equal
    assert len(result.differences) == 1
    tag_diff, = [d for d in result.differences if d.type == DifferenceType.TAG_MISMATCH]
    assert tag_diff.expected == 'div'
    assert tag_diff.actual == 'span'


def test_detects_different_self_closing_tags():
    result = compare_html('<foo />', '<bar/>')
    assert not result.is_equal
    assert len(result.differences) == 1
    tag_diff, = [d for d in result.differences if d.type == DifferenceType.TAG_MISMATCH]
    assert tag_diff.expected == 'foo'
    assert tag_diff.actual == 'bar'


def test_nested_tag_mismatch():
    result = compare_html(
        '<div><p>text</p></div>',
        '<div><span>text</span></div>',
    )
    assert not result.is_equal
    tag_diff, = [d for d in result.differences if d.type == DifferenceType.TAG_MISMATCH]
    assert tag_diff.expected == 'p'
    assert tag_diff.actual == 'span'



def test_different_text_detected():
    result = compare_html('<p>foo</p>', '<p>bar</p>')
    assert not result.is_equal
    text_diff, = [d for d in result.differences if d.type == DifferenceType.TEXT_MISMATCH]
    assert text_diff.expected == 'foo'
    assert text_diff.actual == 'bar'



def test_text_vs_empty_detected():
    result = compare_html('<p>hello</p>', '<p></p>')
    assert not result.is_equal


def test_different_attribute_values_detected():
    result = compare_html(
        '<div class="foo"></div>',
        '<div class="bar"></div>',
    )
    assert not result.is_equal
    # class attributes produce CLASS_MISSING/CLASS_EXTRA, not ATTRIBUTE_MISMATCH
    missing_diff, = [d for d in result.differences if d.type == DifferenceType.CLASS_MISSING]
    extra_diff, = [d for d in result.differences if d.type == DifferenceType.CLASS_EXTRA]
    assert 'foo' in missing_diff.expected
    assert 'bar' in extra_diff.actual


def test_missing_attribute_detected():
    result = compare_html(
        '<div class="foo"></div>',
        '<div></div>',
    )
    assert not result.is_equal
    # entire class attribute is missing -> ATTRIBUTE_MISSING
    attr_diffs = [d for d in result.differences if d.type == DifferenceType.ATTRIBUTE_MISSING]
    assert len(attr_diffs) >= 1


def test_extra_attribute_detected():
    result = compare_html(
        '<div></div>',
        '<div class="foo"></div>',
    )
    assert not result.is_equal
    attr_diffs = [d for d in result.differences if d.type == DifferenceType.ATTRIBUTE_EXTRA]
    assert len(attr_diffs) >= 1


def test_ignores_attribute_ordering():
    result = compare_html(
        '<div data-hidden="true" class="hidden"></div>',
        '<div class="hidden" data-hidden="true"></div>',
    )
    assert result.is_equal


def test_ignores_attribute_ordering_multiple_attributes():
    result = compare_html(
        '<div id="x" class="foo" data-value="1"></div>',
        '<div data-value="1" id="x" class="foo"></div>',
    )
    assert result.is_equal


def test_can_detect_different_attribute_value():
    result = compare_html(
        '<div style="color: green"></div>',
        '<div style="color: red"></div>',
    )
    assert not result.is_equal


def test_can_detect_missing_attribute_img_alt():
    """<img alt=""> has different semantic meaning than <img>."""
    # MDN: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/img#attr-alt
    result = compare_html(
        '<img alt="">',
        '<img>',
    )
    assert not result.is_equal
    attr_diffs = [d for d in result.differences if d.type == DifferenceType.ATTRIBUTE_MISSING]
    assert len(attr_diffs) >= 1


def test_ignores_ordering_of_css_classes():
    result = compare_html(
        '<div class="foo bar"></div>',
        '<div class="bar foo"></div>',
    )
    assert result.is_equal


def test_can_detect_different_css_classes():
    result = compare_html(
        '<div class="foo bar"></div>',
        '<div class="foobar"></div>',
    )
    assert not result.is_equal


def test_ignores_whitespace_inside_class_attribute():
    result = compare_html(
        '<div class="foo   bar"></div>',
        '<div class=" foo bar  "></div>',
    )
    assert result.is_equal


def test_ignores_tab_in_class_attribute():
    result = compare_html(
        '<div class="foo\tbar"></div>',
        '<div class="foo bar"></div>',
    )
    assert result.is_equal


def test_treats_absent_class_same_as_empty_class():
    result = compare_html(
        '<div class=""></div>',
        '<div></div>',
    )
    assert result.is_equal


def test_treats_whitespace_only_class_same_as_absent():
    result = compare_html(
        '<div class="  \t  "></div>',
        '<div></div>',
    )
    assert result.is_equal


def test_extra_child_detected():
    result = compare_html(
        '<div></div>',
        '<div><p>extra</p></div>',
    )
    assert not result.is_equal
    child_diffs = [d for d in result.differences if d.type == DifferenceType.CHILD_EXTRA]
    assert len(child_diffs) >= 1


def test_missing_child_detected():
    result = compare_html(
        '<div><p>expected</p></div>',
        '<div></div>',
    )
    assert not result.is_equal
    child_diffs = [d for d in result.differences if d.type == DifferenceType.CHILD_MISSING]
    assert len(child_diffs) >= 1


def test_multiple_children_comparison():
    result = compare_html(
        '<div><p>a</p><p>b</p></div>',
        '<div><p>a</p><p>b</p></div>',
    )
    assert result.is_equal


def test_child_order_matters():
    result = compare_html(
        '<div><p>a</p><span>b</span></div>',
        '<div><span>b</span><p>a</p></div>',
    )
    assert not result.is_equal


def test_identical_comments_are_equal():
    result = compare_html(
        '<div><!-- comment --></div>',
        '<div><!-- comment --></div>',
    )
    assert result.is_equal


def test_different_comments_detected():
    opts = CompareOptions(ignore_comments=False)
    result = compare_html(
        '<div><!-- comment a --></div>',
        '<div><!-- comment b --></div>',
        options=opts,
    )
    assert not result.is_equal
    comment_diffs = [d for d in result.differences if d.type == DifferenceType.COMMENT_MISMATCH]
    assert len(comment_diffs) >= 1


def test_result_str_for_equal():
    result = compare_html('<div></div>', '<div></div>')
    assert 'equal' in str(result).lower()


def test_result_str_for_different():
    result = compare_html('<div></div>', '<span></span>')
    result_str = str(result)
    assert 'differ' in result_str.lower()
    assert 'TAG_MISMATCH' in result_str


def test_result_bool_true_when_equal():
    result = compare_html('<div></div>', '<div></div>')
    assert bool(result) is True


def test_result_bool_false_when_different():
    result = compare_html('<div></div>', '<span></span>')
    assert bool(result) is False


def test_difference_path_includes_element():
    result = compare_html(
        '<div><p>expected</p></div>',
        '<div><p>actual</p></div>',
    )
    assert not result.is_equal
    # path should include the element hierarchy
    text_diffs = [d for d in result.differences if d.type == DifferenceType.TEXT_MISMATCH]
    assert len(text_diffs) >= 1
    assert 'p' in text_diffs[0].path


def test_difference_str_includes_values():
    result = compare_html('<p>expected</p>', '<p>actual</p>')
    text_diffs = [d for d in result.differences if d.type == DifferenceType.TEXT_MISMATCH]
    diff_str = str(text_diffs[0])
    assert 'expected' in diff_str
    assert 'actual' in diff_str


def test_identical_style_attributes():
    css = '<div style="color: red;"></div>'
    assert compare_html(css, css).is_equal


def test_style_declarations_order_independent():
    result = compare_html(
        '<div style="color: red; font-weight: bold;"></div>',
        '<div style="font-weight: bold; color: red;"></div>',
    )
    assert result.is_equal


def test_style_whitespace_irrelevant():
    result = compare_html(
        '<div style="color:red;font-weight:bold"></div>',
        '<div style="color: red; font-weight: bold;"></div>',
    )
    assert result.is_equal


def test_treats_absent_style_same_as_empty_style():
    result = compare_html(
        '<div style=""></div>',
        '<div></div>',
    )
    assert result.is_equal


def test_treats_whitespace_only_style_same_as_absent():
    result = compare_html(
        '<div style="  "></div>',
        '<div></div>',
    )
    assert result.is_equal


def test_style_zero_with_and_without_unit():
    result = compare_html(
        '<div style="width: 0px;"></div>',
        '<div style="width: 0;"></div>',
    )
    assert result.is_equal


@pytest.mark.xfail(reason="hex color expansion requires property-aware CSS comparison")
def test_can_handle_shorthand_hex_colors():
    result = compare_html(
        '<div style="color: #f60;"></div>',
        '<div style="color: #ff6600;"></div>',
    )
    assert result.is_equal


def test_style_mismatch_detected():
    result = compare_html(
        '<div style="color: red;"></div>',
        '<div style="color: blue;"></div>',
    )
    assert not result.is_equal
    style_diffs = [d for d in result.differences if d.type == DifferenceType.STYLE_MISMATCH]
    assert len(style_diffs) == 1


def test_style_missing_declaration_detected():
    result = compare_html(
        '<div style="color: red; font-size: 12px;"></div>',
        '<div style="color: red;"></div>',
    )
    assert not result.is_equal


def test_style_extra_declaration_detected():
    result = compare_html(
        '<div style="color: red;"></div>',
        '<div style="color: red; font-size: 12px;"></div>',
    )
    assert not result.is_equal


def test_ignores_whitespace_between_block_elements():
    expected = '''<html>
        <body>
            Foo bar
        </body>
    </html>'''
    actual = '<html><body>Foo bar</body></html>'
    assert compare_html(expected, actual).is_equal


def test_ignores_whitespace_around_nested_block_elements():
    expected = '''<div>
        <p>hello</p>
        <p>world</p>
    </div>'''
    actual = '<div><p>hello</p><p>world</p></div>'
    assert compare_html(expected, actual).is_equal


def test_ignores_leading_trailing_whitespace_in_block_text():
    result = compare_html(
        '<div>  hello world  </div>',
        '<div>hello world</div>',
    )
    assert result.is_equal


def test_preserves_text_content_in_block():
    result = compare_html(
        '<div>hello</div>',
        '<div>world</div>',
    )
    assert not result.is_equal


def test_detects_missing_space_between_inline_elements():
    result = compare_html(
        'foo <b>bar</b>',
        'foo<b>bar</b>',
    )
    assert not result.is_equal


def test_detects_missing_space_in_text():
    result = compare_html(
        '<p>hello world</p>',
        '<p>helloworld</p>',
    )
    assert not result.is_equal


def test_collapses_multiple_spaces():
    # Multiple spaces collapse to one in HTML rendering
    result = compare_html(
        '<p>hello   world</p>',
        '<p>hello world</p>',
    )
    assert result.is_equal


def test_preserves_space_around_inline_elements():
    # assert_same_html('<p>a <b>b</b> c</p>', '<p>a <b>b</b> c</p>')
    css = '<p>a <b>b</b> c</p>'
    assert compare_html(css, css).is_equal
    assert not compare_html(css, css.replace(' ', '')).is_equal


def test_can_detect_significant_whitespace():
    """Test that whitespace between text and inline elements is significant."""
    expected_html = 'foo <b>bar</b>'
    actual_html = 'foo<b>bar</b>'
    result = compare_html(expected_html, actual_html)
    assert not result.is_equal


@pytest.mark.parametrize(('expected_html', 'actual_html'), [
    # a collapsible space does not render at the start/end of a block's content
    ('<div>foo <b>bar</b> </div>', '<div>foo <b>bar</b></div>'),
    ('<div> <b>foo</b> bar</div>', '<div><b>foo</b> bar</div>'),
    # ... nor next to a <br>, which ends the line box
    ('<div>foo <br>bar</div>', '<div>foo<br>bar</div>'),
    ('<div>foo<br> bar</div>', '<div>foo<br>bar</div>'),
    # inline element boundaries do not start a separate whitespace context
    ('<div><span> foo</span></div>', '<div><span>foo</span></div>'),
    ('<div><span>foo </span></div>', '<div><span>foo</span></div>'),
])
def test_ignores_whitespace_which_does_not_render(expected_html, actual_html):
    assert compare_html(expected_html, actual_html).is_equal


def test_detects_whitespace_between_inline_elements():
    result = compare_html(
        '<div><b>foo</b> <b>bar</b></div>',
        '<div><b>foo</b><b>bar</b></div>',
    )
    assert not result.is_equal


@pytest.mark.parametrize(('expected_html', 'actual_html'), [
    ('<div>foo <p>bar</p></div>', '<div>foo<p>bar</p></div>'),
    ('<div><p>foo</p> bar</div>', '<div><p>foo</p>bar</div>'),
    ('<div>foo <br> <br> bar</div>', '<div>foo<br><br>bar</div>'),
    ('<div><span></span> <span></span></div>', '<div><span></span><span></span></div>'),
])
def test_ignores_whitespace_at_inline_flow_boundaries(expected_html, actual_html):
    assert compare_html(expected_html, actual_html).is_equal


@pytest.mark.parametrize(('expected_html', 'actual_html'), [
    ('<div><span><b>foo</b></span> <em>bar</em></div>',
     '<div><span><b>foo</b></span><em>bar</em></div>'),
    ('<div>foo<span> </span>bar</div>', '<div>foo<span></span>bar</div>'),
    ('<div><img src="a"> <img src="b"></div>',
     '<div><img src="a"><img src="b"></div>'),
])
def test_detects_whitespace_inside_an_inline_flow(expected_html, actual_html):
    assert not compare_html(expected_html, actual_html).is_equal


# --- Comment Handling ---

def test_ignores_leading_comments_by_default():
    result = compare_html(
        '<div><!-- comment -->foo</div>',
        '<div>foo</div>',
    )
    assert result.is_equal

def test_ignores_trailing_comments_by_default():
    result = compare_html(
        '<div>foo<!-- comment --></div>',
        '<div>foo</div>',
    )
    assert result.is_equal


def test_can_ignore_whitespace_after_comment():
    actual_html = '''<div>
        <!-- comment with extra whitespace before next tag -->

        <b>foo</b>
    </div>'''
    expected_html = '<div><b>foo</b></div>'
    assert compare_html(actual_html, expected_html).is_equal


@pytest.mark.parametrize(('commented_html', 'plain_html'), [
    ('<div>foo<!-- comment --> bar</div>', '<div>foo bar</div>'),
    ('<div>foo <!-- comment --> bar</div>', '<div>foo bar</div>'),
    ('<div>foo<!-- comment -->bar</div>', '<div>foobar</div>'),
])
def test_ignored_comment_is_transparent_to_text_normalization(commented_html, plain_html):
    assert compare_html(commented_html, plain_html).is_equal


def test_ignores_comments_with_different_content_by_default():
    result = compare_html(
        '<div><!-- comment A -->foo</div>',
        '<div><!-- comment B -->foo</div>',
    )
    assert result.is_equal


def test_compares_comments_when_ignore_comments_is_false():
    result = compare_html(
        '<div><!-- same -->foo</div>',
        '<div><!-- same -->foo</div>',
        options=CompareOptions(ignore_comments=False),
    )
    assert result.is_equal


def test_detects_different_comments_when_enabled():
    result = compare_html(
        '<div><!-- a -->foo</div>',
        '<div><!-- b -->foo</div>',
        options=CompareOptions(ignore_comments=False),
    )
    assert not result.is_equal


def test_detects_missing_comment_when_enabled():
    result = compare_html(
        '<div><!-- comment -->foo</div>',
        '<div>foo</div>',
        options=CompareOptions(ignore_comments=False),
    )
    assert not result.is_equal


def test_detects_extra_comment_when_enabled():
    result = compare_html(
        '<div>foo</div>',
        '<div><!-- comment -->foo</div>',
        options=CompareOptions(ignore_comments=False),
    )
    assert not result.is_equal


# --- Conditional Comment Comparison ---

def test_compares_conditional_comments_by_default():
    # Conditional comments should be compared by default (unlike regular comments)
    result = compare_html(
        '<div><!--[if IE]><p>old</p><![endif]--></div>',
        '<div><!--[if IE]><p>new</p><![endif]--></div>',
    )
    assert not result.is_equal


def test_same_conditional_comments_are_equal():
    comment = '<div><!--[if IE]><p>same</p><![endif]--></div>'
    assert compare_html(comment, comment).is_equal


def test_different_conditional_comment_conditions_detected():
    result = compare_html(
        '<div><!--[if IE]><p>x</p><![endif]--></div>',
        '<div><!--[if lt IE 9]><p>x</p><![endif]--></div>',
    )
    assert not result.is_equal


def test_can_ignore_conditional_comments_when_option_set():
    opts = CompareOptions(ignore_conditional_comments=True)

    result = compare_html(
        '<div><!--[if IE]><p>old</p><![endif]--></div>',
        '<div><!--[if IE]><p>new</p><![endif]--></div>',
        options=opts,
    )
    assert result.is_equal


def test_ignores_regular_comments_but_compares_conditional_by_default():
    # Default: ignore_comments=True, ignore_conditional_comments=False
    # Regular comment difference should be ignored
    result = compare_html(
        '<div><!-- regular A --><!--[if IE]><p>same</p><![endif]--></div>',
        '<div><!-- regular B --><!--[if IE]><p>same</p><![endif]--></div>',
    )
    assert result.is_equal

    # Conditional comment difference should be detected
    result = compare_html(
        '<div><!-- regular A --><!--[if IE]><p>old</p><![endif]--></div>',
        '<div><!-- regular B --><!--[if IE]><p>new</p><![endif]--></div>',
    )
    assert not result.is_equal


# --- Document Prefix ---
#
# Comparing the prefix is opt-in: an ordinary comment before the DOCTYPE must not
# suddenly become a significant difference for existing users.

_PREFIX_DOC = '<!doctype html>\n<html><head><title>t</title></head><body>Hello</body></html>'


def test_text_before_the_doctype_no_longer_produces_bogus_differences():
    # this used to report a missing DOCTYPE plus text mismatches inside "<body>",
    # because the raw text pushed the whole document out of "<head>"
    result = compare_html('{# subject: x #}\n' + _PREFIX_DOC, _PREFIX_DOC)
    assert result.is_equal, result.differences


def test_does_not_compare_document_prefix():
    result = compare_html('{# subject: a #}\n' + _PREFIX_DOC, '{# subject: b #}\n' + _PREFIX_DOC)
    assert result.is_equal


def test_compares_document_prefix_when_option_is_set():
    opts = CompareOptions(compare_document_prefix=True)
    result = compare_html(
        '{# subject: a #}\n' + _PREFIX_DOC,
        '{# subject: b #}\n' + _PREFIX_DOC,
        options=opts,
    )
    assert not result.is_equal
    difference, = result.differences
    assert difference.type == DifferenceType.DOCUMENT_PREFIX_MISMATCH
    assert difference.expected == '{# subject: a #}'
    assert difference.actual == '{# subject: b #}'


def test_same_document_prefix_is_equal_when_option_set():
    opts = CompareOptions(compare_document_prefix=True)
    prefixed = '{# subject: x #}\n' + _PREFIX_DOC
    assert compare_html(prefixed, prefixed, options=opts).is_equal


def test_detects_missing_document_prefix_when_option_set():
    opts = CompareOptions(compare_document_prefix=True)
    result = compare_html('{# subject: x #}\n' + _PREFIX_DOC, _PREFIX_DOC, options=opts)
    assert not result.is_equal
    difference, = result.differences
    assert difference.type == DifferenceType.DOCUMENT_PREFIX_MISMATCH
    assert difference.actual == ''


def test_ignores_whitespace_around_the_document_prefix_when_option_set():
    # only the whitespace separating the prefix from the DOCTYPE is insignificant
    opts = CompareOptions(compare_document_prefix=True)
    result = compare_html(
        '{# subject: x #}\n\n  ' + _PREFIX_DOC,
        '  {# subject: x #}\n' + _PREFIX_DOC,
        options=opts,
    )
    assert result.is_equal


def test_compares_document_prefix_literally_when_option_set():
    # the point of the feature is exact preservation, so nothing inside is normalized
    opts = CompareOptions(compare_document_prefix=True)
    result = compare_html(
        '{# subject:  x #}\n' + _PREFIX_DOC,
        '{# subject: x #}\n' + _PREFIX_DOC,
        options=opts,
    )
    assert not result.is_equal


def test_compares_a_comment_before_the_doctype_when_option_set():
    # a comment in the prefix is prefix content, not a comment "ignore_comments" sees
    opts = CompareOptions(compare_document_prefix=True)
    result = compare_html(
        '<!-- generated by our template system -->\n' + _PREFIX_DOC,
        _PREFIX_DOC,
        options=opts,
    )
    assert not result.is_equal


def test_documents_without_a_doctype_are_equal_when_option_set():
    # both prefixes are empty, the option must not make the documents differ
    opts = CompareOptions(compare_document_prefix=True)
    result = compare_html(
        '<html><body>Hello</body></html>',
        '<html><body>Hello</body></html>',
        options=opts,
    )
    assert result.is_equal


def test_compares_mj_raw_file_start_metadata():
    opts = CompareOptions(compare_document_prefix=True)
    metadata = '{# subject: Welcome #}\n{# preheader: Hi there #}\n'
    assert compare_html(metadata + _PREFIX_DOC, metadata + _PREFIX_DOC, options=opts).is_equal
    result = compare_html(
        metadata + _PREFIX_DOC,
        '{# subject: Welcome #}\n' + _PREFIX_DOC,
        options=opts,
    )
    assert not result.is_equal
    difference, = result.differences
    assert difference.type == DifferenceType.DOCUMENT_PREFIX_MISMATCH


def test_does_not_compare_comment_before_the_doctype():
    result = compare_html(
        '<!-- generated by our template system -->\n' + _PREFIX_DOC,
        _PREFIX_DOC,
        options=CompareOptions(ignore_comments=False),
    )
    assert result.is_equal


# --- Downlevel-Revealed Conditional Comments ---
#
# The revealed form does not enclose its HTML in the comment, so html5lib
# reports two ordinary comments with the HTML as their sibling. Both markers
# must stay significant: losing one changes which clients display the content.

_REVEALED = '<div><!--[if !mso]><!--><span>x</span><!--<![endif]--></div>'


def test_same_downlevel_revealed_conditional_comment_is_equal():
    assert compare_html(_REVEALED, _REVEALED).is_equal


def test_detects_missing_downlevel_revealed_markers():
    # both markers used to be dropped as ordinary comments, so this compared equal
    result = compare_html(_REVEALED, '<div><span>x</span></div>')
    assert not result.is_equal


def test_detects_missing_closing_downlevel_revealed_marker():
    result = compare_html(_REVEALED, '<div><!--[if !mso]><!--><span>x</span></div>')
    assert not result.is_equal


def test_detects_changed_condition_in_downlevel_revealed_marker():
    result = compare_html(_REVEALED, '<div><!--[if mso]><!--><span>x</span><!--<![endif]--></div>')
    assert not result.is_equal
    difference, = [
        d for d in result.differences
        if d.type == DifferenceType.CONDITIONAL_COMMENT_MARKER_MISMATCH
    ]
    assert difference.expected == '<!--[if !mso]><!-->'
    assert difference.actual == '<!--[if mso]><!-->'


def test_ignores_spelling_of_the_opening_downlevel_revealed_marker():
    # "<!-->" and "<!---->" render identically in every browser
    result = compare_html(
        _REVEALED,
        '<div><!--[if !mso]><!----><span>x</span><!--<![endif]--></div>',
    )
    assert result.is_equal


def test_compares_downlevel_revealed_markers_without_a_comment_wrapper():
    # "<![if !IE]>...<![endif]>" is the form without the outer comment
    revealed = '<div><![if !IE]><span>x</span><![endif]></div>'
    assert compare_html(revealed, revealed).is_equal
    result = compare_html(revealed, '<div><![if !IE]><span>x</span></div>')
    assert not result.is_equal


def test_can_ignore_downlevel_revealed_conditional_comments_when_option_set():
    opts = CompareOptions(ignore_conditional_comments=True)
    result = compare_html(_REVEALED, '<div><span>x</span></div>', options=opts)
    assert result.is_equal


def test_downlevel_revealed_markers_are_not_ignored_as_regular_comments():
    # default is ignore_comments=True, which must not reach a marker
    result = compare_html(
        '<div><!-- regular A --><!--[if !mso]><!--><span>x</span><!--<![endif]--></div>',
        '<div><!-- regular B --><span>x</span></div>',
    )
    assert not result.is_equal


def test_downlevel_hidden_conditional_comments_are_still_parsed_as_one_node():
    # the marker patterns must not steal the complete form from the parser
    result = compare_html(
        '<div><!--[if IE]><p>old</p><![endif]--></div>',
        '<div><!--[if IE]><p>new</p><![endif]--></div>',
    )
    assert not result.is_equal
    assert DifferenceType.CONDITIONAL_COMMENT_MARKER_MISMATCH not in {
        d.type for d in result.differences
    }


def test_downlevel_revealed_conditional_comment_around_a_table():
    # the mjml-python scenario: the markers decide whether Outlook sees the table
    expected = (
        '<!--[if mso | IE]><table><tr><td><![endif]-->'
        '<div>x</div>'
        '<!--[if mso | IE]></td></tr></table><![endif]-->'
    )
    assert compare_html(expected, expected).is_equal
    assert not compare_html(expected, '<div>x</div>').is_equal


# --- Style Tag CSS Normalization Tests ---

def test_style_tag_ignores_css_whitespace_differences():
    """CSS inside <style> tags should be compared semantically, not as strings."""
    result = compare_html(
        '<style>body { margin: 0; padding: 0; }</style>',
        '<style>body { margin:0;padding:0; }</style>',
    )
    assert result.is_equal


def test_style_tag_detects_actual_css_differences():
    result = compare_html(
        '<style>body { margin: 0; }</style>',
        '<style>body { margin: 10px; }</style>',
    )
    assert not result.is_equal


def test_style_tag_ignores_declaration_order():
    result = compare_html(
        '<style>.foo { color: red; font-size: 12px; }</style>',
        '<style>.foo { font-size: 12px; color: red; }</style>',
    )
    assert result.is_equal


def test_style_tag_ignores_unit_for_zero_values():
    result = compare_html(
        '<style>body { margin: 0px; }</style>',
        '<style>body { margin: 0; }</style>',
    )
    assert result.is_equal


def test_style_tag_with_multiple_selectors():
    result = compare_html(
        '<style>#outlook a { padding: 0; } body { margin: 0; }</style>',
        '<style>#outlook a { padding:0; } body { margin:0; }</style>',
    )
    assert result.is_equal


def test_style_tag_with_media_query():
    result = compare_html(
        '<style>@media only screen and (min-width:480px) { .foo { width: 100%; } }</style>',
        '<style>@media only screen and (min-width:480px) { .foo { width:100%; } }</style>',
    )
    assert result.is_equal


def test_style_tag_detects_different_media_query_content():
    result = compare_html(
        '<style>@media screen { .foo { width: 100%; } }</style>',
        '<style>@media screen { .foo { width: 50%; } }</style>',
    )
    assert not result.is_equal


# --- Whitespace In Selectors ---
#
# Whitespace inside a selector is the descendant combinator, so it must not be
# stripped: ".a .b" matches a ".b" inside a ".a" while ".a.b" matches a single
# element carrying both classes.

@pytest.mark.parametrize(('expected_selector', 'actual_selector'), [
    ('.a .b', '.a.b'),
    ('#a #b', '#a#b'),
    ('td .x', 'td.x'),
    ('a[href] p', 'a[href]p'),
    ('a b', 'ab'),
])
def test_style_tag_detects_missing_descendant_combinator(expected_selector, actual_selector):
    result = compare_html(
        f'<style>{expected_selector} {{ color: red; }}</style>',
        f'<style>{actual_selector} {{ color: red; }}</style>',
    )
    assert not result.is_equal


@pytest.mark.parametrize(('expected_selector', 'actual_selector'), [
    # whitespace around a combinator is insignificant
    ('a > b', 'a>b'),
    ('a  >  b', 'a>b'),
    ('a + b', 'a+b'),
    ('a ~ b', 'a~b'),
    ('a , b', 'a,b'),
    # ... and so is a longer run of whitespace or a line break
    ('.a   .b', '.a .b'),
    ('.a\n.b', '.a .b'),
    ('  .a .b  ', '.a .b'),
    ('a > b .c , d', 'a>b .c,d'),
])
def test_style_tag_ignores_insignificant_selector_whitespace(expected_selector, actual_selector):
    result = compare_html(
        f'<style>{expected_selector} {{ color: red; }}</style>',
        f'<style>{actual_selector} {{ color: red; }}</style>',
    )
    assert result.is_equal


def test_style_tag_ignores_insignificant_whitespace_in_at_rule_prelude():
    result = compare_html(
        '<style>@media  only   screen { .foo { width: 100%; } }</style>',
        '<style>@media only screen { .foo { width: 100%; } }</style>',
    )
    assert result.is_equal

    result = compare_html(
        '<style>@media screen , print { .foo { width: 100%; } }</style>',
        '<style>@media screen,print { .foo { width: 100%; } }</style>',
    )
    assert result.is_equal


def test_style_tag_detects_different_at_rule_prelude():
    result = compare_html(
        '<style>@media only screen { .foo { width: 100%; } }</style>',
        '<style>@media only print { .foo { width: 100%; } }</style>',
    )
    assert not result.is_equal


# --- Case Of At-Rule Names ---

@pytest.mark.parametrize(('expected_css', 'actual_css'), [
    ('@IMPORT url(a.css);', '@import url("a.css");'),
    ('@MEDIA screen { p { color: red } }', '@media screen { p { color:red } }'),
    ('@FONT-FACE { font-family: x; src: url(a.woff2) }',
     '@font-face { src:url(a.woff2);font-family:x }'),
    ('@-MS-VIEWPORT { width: device-width }',
     '@-ms-viewport { width:device-width }'),
    ('@MEDIA screen { @SUPPORTS (display: grid) { p { color: red } } }',
     '@media screen { @supports (display: grid) { p { color:red } } }'),
])
def test_compare_stylesheet_ignores_case_of_at_rule_names(expected_css, actual_css):
    assert compare_stylesheet(expected_css, actual_css)


def test_compare_html_ignores_case_of_at_rule_names():
    result = compare_html(
        '<style>@MEDIA screen { p { color: red } }</style>',
        '<style>@media screen { p { color:red } }</style>',
    )
    assert result.is_equal


def test_keeps_case_of_custom_at_rule_names():
    assert not compare_stylesheet('@--Foo {}', '@--foo {}')


# --- Whitespace In Declaration Values ---
#
# Whitespace between the component values of a declaration separates them, so it
# must not be stripped either: "font-family: Arial Black" names a different font
# than "font-family: ArialBlack". Whitespace around a "," or a "/" is
# insignificant, just like whitespace around a combinator in a selector.

@pytest.mark.parametrize(('expected_css', 'actual_css'), [
    # a longer run of whitespace (or a line break) is the same as a single space
    ('margin: 0 auto', 'margin: 0    auto'),
    ('border: 1px solid red', 'border: 1px  solid  red'),
    ('margin: 0 auto', 'margin:0 auto'),
    # ... and so is whitespace around a separator
    ('font: 12px / 1.5 serif', 'font: 12px/1.5 serif'),
    ('grid-area: a / b', 'grid-area: a/b'),
    ('font-family: Arial , sans-serif', 'font-family: Arial,sans-serif'),
    ('transition: color .3s ease , opacity .2s', 'transition: color .3s ease,opacity .2s'),
])
def test_ignores_insignificant_whitespace_in_declaration_value(expected_css, actual_css):
    result = compare_html(
        f'<div style="{expected_css}"></div>',
        f'<div style="{actual_css}"></div>',
    )
    assert result.is_equal


@pytest.mark.parametrize(('expected_css', 'actual_css'), [
    ('font-family: Arial Black', 'font-family: ArialBlack'),
    ('background: url(a.png) no-repeat', 'background: url(a.png)no-repeat'),
])
def test_detects_missing_whitespace_in_declaration_value(expected_css, actual_css):
    result = compare_html(
        f'<div style="{expected_css}"></div>',
        f'<div style="{actual_css}"></div>',
    )
    assert not result.is_equal


def test_style_tag_ignores_insignificant_whitespace_in_declaration_value():
    result = compare_html(
        '<style>.foo { font: 12px / 1.5  Arial Black , sans-serif; }</style>',
        '<style>.foo { font: 12px/1.5 Arial Black,sans-serif; }</style>',
    )
    assert result.is_equal


def test_style_tag_detects_missing_whitespace_in_declaration_value():
    # two adjacent strings are serialized without a separator, so this used to
    # compare equal once the whitespace had been stripped
    result = compare_html(
        '<style>.foo { content: "a" "b"; }</style>',
        '<style>.foo { content: "a""b"; }</style>',
    )
    assert not result.is_equal


# --- Numeric Token Representations ---
#
# tinycss2 retains the source spelling of a number separately from its parsed
# value. CSS treats spellings with the same value and numeric category alike.

@pytest.mark.parametrize(('expected_css', 'actual_css'), [
    ('opacity: +.5', 'opacity: 0.5'),
    ('width: 05e-1%', 'width: .5%'),
    ('margin: +.5e0px', 'margin: 0.5px'),
    ('opacity: 0.50000000000000001', 'opacity: .500000000000000010'),
])
def test_compare_css_ignores_numeric_token_representation(expected_css, actual_css):
    assert compare_css(expected_css, actual_css)


@pytest.mark.parametrize(('expected_css', 'actual_css'), [
    ('<p style="opacity:+.5">x</p>', '<p style="opacity:0.5">x</p>'),
    ('<style>p{width:05e-1%}</style>', '<style>p{width:.5%}</style>'),
    ('<style>p:nth-child(+01){color:red}</style>',
     '<style>p:nth-child(1){color:red}</style>'),
    ('<style>p{width:calc(.5px + 1px)}</style>',
     '<style>p{width:calc(0.5px + 1px)}</style>'),
])
def test_compare_html_ignores_numeric_token_representation(expected_css, actual_css):
    assert compare_html(expected_css, actual_css).is_equal


def test_keeps_integer_and_non_integer_number_tokens_distinct():
    assert not compare_css('z-index: 1', 'z-index: 1.0')


def test_does_not_merge_distinct_numbers_beyond_float_precision():
    assert not compare_css(
        'opacity: 0.50000000000000001',
        'opacity: 0.50000000000000002',
    )


def test_does_not_merge_distinct_numbers_after_float_overflow():
    assert not compare_css('width: 1e999px', 'width: 2e999px')


def test_does_not_normalize_numbers_in_a_custom_property():
    assert not compare_css('--x: .5px', '--x: 0.5px')


def test_does_not_normalize_numbers_in_a_malformed_declaration_body():
    assert not compare_stylesheet('p{*zoom:.5}', 'p{*zoom:0.5}')


# --- Case Of Dimension Units ---

@pytest.mark.parametrize(('expected_css', 'actual_css'), [
    ('margin: 1PX', 'margin: 1px'),
    ('animation-delay: 2S', 'animation-delay: 2s'),
    ('width: calc(1REM + 2px)', 'width: calc(1rem + 2px)'),
])
def test_compare_css_ignores_case_of_dimension_units(expected_css, actual_css):
    assert compare_css(expected_css, actual_css)


def test_style_tag_ignores_case_of_dimension_units():
    result = compare_html(
        '<style>p { margin: 1PX; }</style>',
        '<style>p { margin: 1px; }</style>',
    )
    assert result.is_equal


def test_does_not_normalize_dimension_units_in_a_custom_property():
    assert not compare_css('--x: 1PX', '--x: 1px')


# --- Case Of Function Names ---

@pytest.mark.parametrize(('expected_css', 'actual_css'), [
    ('color: RGB(255, 0, 0)', 'color: rgb(255,0,0)'),
    ('filter: DROP-SHADOW(0 0 1px black)', 'filter: drop-shadow(0 0 1px black)'),
    ('color: COLOR-MIX(in srgb, RGB(255,0,0), blue)',
     'color: color-mix(in srgb, rgb(255,0,0), blue)'),
    ('background: URL(a.png)', 'background: url("a.png")'),
])
def test_compare_css_ignores_case_of_function_names(expected_css, actual_css):
    assert compare_css(expected_css, actual_css)


@pytest.mark.parametrize(('expected_html', 'actual_html'), [
    ('<p style="color:RGB(255,0,0)">x</p>',
     '<p style="color:rgb(255,0,0)">x</p>'),
    ('<style>p{color:RGB(255,0,0)}</style>',
     '<style>p{color:rgb(255,0,0)}</style>'),
    ('<style>p:NOT(.a,.b){color:red}</style>',
     '<style>p:not(.a,.b){color:red}</style>'),
])
def test_compare_html_ignores_case_of_function_names(expected_html, actual_html):
    assert compare_html(expected_html, actual_html).is_equal


def test_keeps_case_of_custom_function_names():
    assert not compare_css('width: --Foo(1px)', 'width: --foo(1px)')


def test_does_not_normalize_function_names_in_a_custom_property():
    assert not compare_css('--x: RGB(1,2,3)', '--x: rgb(1,2,3)')


def test_does_not_normalize_function_names_in_a_malformed_declaration_body():
    assert not compare_stylesheet('p{*zoom:RGB(1)}', 'p{*zoom:rgb(1)}')


# --- Whitespace Inside A Function ---
#
# The value normalization used to walk only the top-level tokens, so whitespace
# CSS ignores stayed significant inside every function.

@pytest.mark.parametrize(('expected_css', 'actual_css'), [
    ('color:rgb(1, 2, 3)', 'color:rgb(1,2,3)'),
    ('color:rgb(1, 2, 3)', 'color:rgb(1,  2, 3)'),
    ('color:var(--x, red)', 'color:var(--x,red)'),
    ('background:linear-gradient(to right, red, blue)',
     'background:linear-gradient(to right,red,blue)'),
    # leading and trailing whitespace inside the parentheses
    ('width:calc( 1px + 2px )', 'width:calc(1px + 2px)'),
    # a slash is a separator in a value, inside a function as well as outside
    ('width:calc(4px / 2)', 'width:calc(4px/2)'),
    # nested functions are normalized too
    ('width:calc(100% - var(--x, 1px))', 'width:calc(100% - var(--x,1px))'),
])
def test_ignores_whitespace_inside_a_function(expected_css, actual_css):
    result = compare_html(
        f'<p style="{expected_css}">x</p>',
        f'<p style="{actual_css}">x</p>',
    )
    assert result.is_equal


def test_keeps_whitespace_required_inside_calc():
    # CSS requires the whitespace around "+" and "-" in calc(), so removing it
    # does not produce the same declaration - it produces an invalid one
    result = compare_html(
        '<p style="width:calc(1px + 2px)">x</p>',
        '<p style="width:calc(1px+2px)">x</p>',
    )
    assert not result.is_equal


def test_does_not_drop_zero_units_inside_a_function():
    # "calc(0 + 1px)" is invalid where "calc(0px + 1px)" is fine, so the
    # zero-length normalization must not follow the whitespace one into a function
    result = compare_html(
        '<p style="width:calc(0px + 1px)">x</p>',
        '<p style="width:calc(0 + 1px)">x</p>',
    )
    assert not result.is_equal


def test_detects_different_values_inside_a_function():
    result = compare_html(
        '<p style="background:linear-gradient(to right, red, blue)">x</p>',
        '<p style="background:linear-gradient(to right, red, green)">x</p>',
    )
    assert not result.is_equal


def test_style_tag_ignores_whitespace_inside_a_function():
    result = compare_html(
        '<style>.foo{color:rgb(1, 2, 3)}</style>',
        '<style>.foo{color:rgb(1,2,3)}</style>',
    )
    assert result.is_equal


def test_style_tag_keeps_descendant_combinator_inside_a_selector_function():
    # the separators carry over into the nested block, and the descendant
    # combinator is not one of them
    result = compare_html(
        '<style>p:not(.a .b){color:red}</style>',
        '<style>p:not(.a.b){color:red}</style>',
    )
    assert not result.is_equal


def test_style_tag_ignores_whitespace_around_a_comma_inside_a_selector_function():
    result = compare_html(
        '<style>p:not(.a , .b){color:red}</style>',
        '<style>p:not(.a,.b){color:red}</style>',
    )
    assert result.is_equal


# --- Case Of CSS Property Names ---
#
# CSS property names are case-insensitive but custom properties ("--Foo") are
# not. tinycss2 lowercases custom property names as well, so its "lower_name"
# must not be used for those.

@pytest.mark.parametrize(('expected_css', 'actual_css'), [
    ('COLOR: red', 'color: red'),
    ('Background-COLOR: blue', 'background-color: blue'),
    ('-WEBKIT-Box-Shadow: none', '-webkit-box-shadow: none'),
    # ... even though the case decides where the declaration is sorted
    ('COLOR: red; FONT-SIZE: 12px', 'font-size: 12px; color: red'),
])
def test_ignores_case_of_property_names(expected_css, actual_css):
    result = compare_html(
        f'<div style="{expected_css}"></div>',
        f'<div style="{actual_css}"></div>',
    )
    assert result.is_equal


def test_style_tag_ignores_case_of_property_names():
    result = compare_html(
        '<style>.foo { COLOR: red; }</style>',
        '<style>.foo { color: red; }</style>',
    )
    assert result.is_equal


def test_detects_case_difference_in_custom_property_name():
    result = compare_html(
        '<div style="--Foo: red"></div>',
        '<div style="--foo: red"></div>',
    )
    assert not result.is_equal


def test_style_tag_detects_case_difference_in_custom_property_name():
    result = compare_html(
        '<style>.foo { --Foo: red; }</style>',
        '<style>.foo { --foo: red; }</style>',
    )
    assert not result.is_equal


# --- Values Of Custom Properties ---
#
# A custom property carries an arbitrary token sequence which CSS preserves as
# written and "var()" substitutes literally, so none of the value normalization
# applies to it. Only the whitespace around the value is insignificant: CSS
# defines the value as the token sequence with leading and trailing whitespace
# removed.

@pytest.mark.parametrize(('expected_css', 'actual_css'), [
    # "calc(var(--x) + 1px)" is valid with "0px" and invalid with "0"
    ('--x: 0px', '--x: 0'),
    ('--x: 0.0px', '--x: 0'),
    ('--x: a  b', '--x: a b'),
    ('--x: a , b', '--x: a,b'),
    ('--x: 12px / 1.5', '--x: 12px/1.5'),
    ('--x: rgb(1, 2, 3)', '--x: rgb(1,2,3)'),
])
def test_does_not_normalize_custom_property_values(expected_css, actual_css):
    result = compare_html(
        f'<div style="{expected_css}"></div>',
        f'<div style="{actual_css}"></div>',
    )
    assert not result.is_equal


@pytest.mark.parametrize(('expected_css', 'actual_css'), [
    ('--x: red', '--x:red'),
    ('--x:red   ', '--x:red'),
    ('--x:  a b  ', '--x:a b'),
    # an empty value is valid CSS and stays empty
    ('--x: ', '--x:'),
])
def test_ignores_whitespace_around_custom_property_values(expected_css, actual_css):
    result = compare_html(
        f'<div style="{expected_css}"></div>',
        f'<div style="{actual_css}"></div>',
    )
    assert result.is_equal


def test_style_tag_does_not_normalize_custom_property_values():
    result = compare_html(
        '<style>.foo { --x: 0px; }</style>',
        '<style>.foo { --x: 0; }</style>',
    )
    assert not result.is_equal


def test_style_tag_ignores_whitespace_around_custom_property_values():
    result = compare_html(
        '<style>.foo { --x: red; }</style>',
        '<style>.foo { --x:red }</style>',
    )
    assert result.is_equal


# a custom property must not stop the regular declarations from being normalized
def test_normalizes_regular_declarations_next_to_a_custom_property():
    result = compare_html(
        '<div style="--x: 0px; margin: 0px"></div>',
        '<div style="--x: 0px; margin: 0"></div>',
    )
    assert result.is_equal


# --- Quoting Of url() ---
#
# The URL in a "url()" may be quoted or not, and the function name is
# case-insensitive like every other one. tinycss2 represents the unquoted
# spelling by a URLToken and the quoted one by a function containing a string,
# which never compare equal.

@pytest.mark.parametrize(('expected_css', 'actual_css'), [
    ('background: url("a.png")', 'background: url(a.png)'),
    ("background: url('a.png')", 'background: url(a.png)'),
    ('background: URL(a.png)', 'background: url("a.png")'),
    ('background: url( "a.png" )', 'background: url(a.png)'),
    ('background: url()', 'background: url("")'),
    # only the unquoted spelling has to escape a space
    (r'background: url(a\ b.png)', 'background: url("a b.png")'),
    # ... and the same inside another function
    ('background: image-set(url("a.png") 1x)', 'background: image-set(url(a.png) 1x)'),
])
def test_ignores_quoting_of_urls(expected_css, actual_css):
    result = compare_html(
        _style_attribute(expected_css),
        _style_attribute(actual_css),
    )
    assert result.is_equal


@pytest.mark.parametrize(('expected_css', 'actual_css'), [
    ('background: url("a.png")', 'background: url(b.png)'),
    # a URL is case-sensitive, the function name around it is not
    ('background: url("a.png")', 'background: URL(A.png)'),
    # a function which only looks like one
    ('background: src("a.png")', 'background: src(a.png)'),
])
def test_detects_different_urls(expected_css, actual_css):
    result = compare_html(
        _style_attribute(expected_css),
        _style_attribute(actual_css),
    )
    assert not result.is_equal


def test_keeps_url_quoting_in_a_custom_property_value():
    # a custom property is substituted literally, so its value stays verbatim
    result = compare_html(
        _style_attribute('--x: url(a.png)'),
        _style_attribute('--x: url("a.png")'),
    )
    assert not result.is_equal


@pytest.mark.parametrize(('expected_css', 'actual_css'), [
    ('p { background: url(a.png) }', 'p { background: url("a.png") }'),
    ('@font-face { src: url(a.woff2) }', '@font-face { src: url("a.woff2") }'),
    # the one prelude which can contain a URL
    ('@import url(a.css);', '@import url("a.css");'),
])
def test_style_tag_ignores_quoting_of_urls(expected_css, actual_css):
    result = compare_html(
        f'<style>{expected_css}</style>',
        f'<style>{actual_css}</style>',
    )
    assert result.is_equal


def test_style_tag_detects_different_urls():
    result = compare_html(
        '<style>p { background: url(a.png) }</style>',
        '<style>p { background: url("b.png") }</style>',
    )
    assert not result.is_equal


# --- Zero Lengths ---
#
# A zero *length* may omit its unit ("margin: 0" means "margin: 0px"). No other
# kind of dimension may: "0" is not a valid <time> and not a valid <angle>.

@pytest.mark.parametrize(('expected_css', 'actual_css'), [
    ('margin: 0px', 'margin: 0'),
    ('margin: 0.0px', 'margin: 0'),
    ('margin: 0.0px', 'margin: 0px'),
    ('margin: 0em', 'margin: 0'),
    ('margin: 0Q', 'margin: 0'),
    ('margin: 0vmin', 'margin: 0'),
    ('margin: 0 auto', 'margin: 0px auto'),
])
def test_ignores_unit_of_zero_lengths(expected_css, actual_css):
    result = compare_html(
        f'<div style="{expected_css}"></div>',
        f'<div style="{actual_css}"></div>',
    )
    assert result.is_equal


@pytest.mark.parametrize(('expected_css', 'actual_css'), [
    ('transition: all 0s', 'transition: all 0'),
    ('margin: 0%', 'margin: 0'),
    ('width: 0%', 'width: 0px'),
])
def test_keeps_unit_of_zero_values_which_are_not_lengths(expected_css, actual_css):
    result = compare_html(
        f'<div style="{expected_css}"></div>',
        f'<div style="{actual_css}"></div>',
    )
    assert not result.is_equal


def test_style_tag_detects_zero_time_without_unit():
    result = compare_html(
        '<style>.foo { transition: all 0s; }</style>',
        '<style>.foo { transition: all 0; }</style>',
    )
    assert not result.is_equal


# --- Order Of Related Declarations ---
#
# Declaration order is ignored so that reformatting a stylesheet does not show
# up as a difference. It cannot be ignored between related declarations though:
# "background:red;background-color:blue" renders blue and the reverse renders
# red.

@pytest.mark.parametrize(('expected_css', 'actual_css'), [
    ('background: red; background-color: blue', 'background-color: blue; background: red'),
    ('margin: 0; margin-top: 5px', 'margin-top: 5px; margin: 0'),
    # the same property twice: the last one wins, so the order decides
    ('color: red; color: blue', 'color: blue; color: red'),
    # a vendor-prefixed property belongs to the family of its plain spelling
    ('-webkit-transition: all; transition: none', 'transition: none; -webkit-transition: all'),
    ('--foo: red; --foo: blue', '--foo: blue; --foo: red'),
])
def test_detects_reordered_declarations_of_the_same_family(expected_css, actual_css):
    result = compare_html(
        f'<div style="{expected_css}"></div>',
        f'<div style="{actual_css}"></div>',
    )
    assert not result.is_equal


@pytest.mark.parametrize(('expected_css', 'actual_css'), [
    ('color: red; font-size: 12px', 'font-size: 12px; color: red'),
    ('margin: 0; padding: 0', 'padding: 0; margin: 0'),
    (
        'color: red; background: blue; font-size: 12px',
        'font-size: 12px; color: red; background: blue',
    ),
    # two vendor prefixes are unrelated to each other
    (
        '-webkit-transform: none; -moz-appearance: none',
        '-moz-appearance: none; -webkit-transform: none',
    ),
    ('--foo: red; --bar: blue', '--bar: blue; --foo: red'),
])
def test_ignores_order_of_unrelated_declarations(expected_css, actual_css):
    result = compare_html(
        f'<div style="{expected_css}"></div>',
        f'<div style="{actual_css}"></div>',
    )
    assert result.is_equal


def test_style_tag_detects_reordered_declarations_of_the_same_family():
    result = compare_html(
        '<style>.foo { background: red; background-color: blue; }</style>',
        '<style>.foo { background-color: blue; background: red; }</style>',
    )
    assert not result.is_equal


# --- Malformed CSS ---
#
# Broken CSS must never raise and must never be dropped: both are worse than
# reporting a difference. What tinycss2 can not parse is compared literally,
# scoped as narrowly as the parse result allows.

@pytest.mark.parametrize('css', [
    'p{color:red}}',
    'color:red;',
    '}',
    '.foo{*zoom:1}',
    '@media screen{p{color:red}}}',
])
def test_style_tag_with_malformed_css_is_equal_to_itself(css):
    # these used to raise "TypeError: Can not serialize <ParseError invalid>"
    result = compare_html(f'<style>{css}</style>', f'<style>{css}</style>')
    assert result.is_equal


@pytest.mark.parametrize(('expected_css', 'actual_css'), [
    # the ParseError is identical for both, only the source text differs
    ('p{color:red}}', 'p{color:red}]'),
    ('p{color:red}}', 'p{color:blue}}'),
    # the IE star hack: invalid CSS which used to be dropped silently
    ('.foo{*zoom:1}', '.foo{}'),
    ('.foo{*zoom:1}', '.foo{*zoom:2}'),
    ('@font-face{*zoom:1}', '@font-face{}'),
])
def test_style_tag_detects_differences_in_malformed_css(expected_css, actual_css):
    result = compare_html(
        f'<style>{expected_css}</style>',
        f'<style>{actual_css}</style>',
    )
    assert not result.is_equal


def test_style_tag_ignores_formatting_of_a_malformed_declaration_block():
    result = compare_html(
        '<style>.foo{*zoom:1}</style>',
        '<style>.foo { *zoom: 1 }</style>',
    )
    assert result.is_equal


def test_style_tag_compares_valid_rules_next_to_a_broken_one_semantically():
    # only the broken block falls back to a literal comparison, so ".a" is still
    # compared without regard to declaration order, whitespace or the zero unit
    result = compare_html(
        '<style>.a{color:red;margin:0px}.b{*zoom:1}</style>',
        '<style>.a{margin:0;color: red}.b{*zoom:1}</style>',
    )
    assert result.is_equal


# --- Malformed Inline Styles ---
#
# Same rule as for a "<style>" tag: a "style" attribute which does not parse
# must never raise and must never be dropped.

@pytest.mark.parametrize('style', [
    'color red',
    'padding',
    'width:100%; !important',
    '@media screen{color:red}',
    # the IE star hack, still in use in HTML email
    '*zoom:1',
])
def test_malformed_style_attribute_is_equal_to_itself(style):
    # these used to raise "AssertionError: <ParseError invalid>"
    result = compare_html(f'<p style="{style}">x</p>', f'<p style="{style}">x</p>')
    assert result.is_equal


@pytest.mark.parametrize(('expected_style', 'actual_style'), [
    ('color red', 'background blue'),
    ('padding', 'margin'),
    ('*zoom:1', '*zoom:2'),
    # a malformed declaration must not be dropped, not even next to a valid one
    ('width:100%; !important', 'width:100%'),
    ('@media screen{color:red}', '@media print{color:red}'),
])
def test_detects_differences_in_malformed_style_attributes(expected_style, actual_style):
    result = compare_html(
        f'<p style="{expected_style}">x</p>',
        f'<p style="{actual_style}">x</p>',
    )
    assert not result.is_equal


def test_malformed_style_attribute_is_reported_as_a_style_mismatch():
    # a raised exception is not attributable to an element, a difference is
    result = compare_html('<p style="color red">x</p>', '<p style="padding">x</p>')
    assert not result.is_equal
    (difference,) = result.differences
    assert difference.type == DifferenceType.STYLE_MISMATCH
    assert difference.path.endswith('p@style')
    assert difference.expected == 'color red'
    assert difference.actual == 'padding'


def test_compares_other_attributes_next_to_a_malformed_style_attribute():
    result = compare_html(
        '<p class="a" style="color red">x</p>',
        '<p class="b" style="color red">x</p>',
    )
    assert not result.is_equal
    difference_types = {difference.type for difference in result.differences}
    assert DifferenceType.STYLE_MISMATCH not in difference_types


# --- Tokens Which Lose Their Source Text ---
#
# tinycss2 reports a string containing a raw newline and an unquoted "url()"
# containing a quote as a ParseError *token*, and only those two kinds serialize
# to a fixed placeholder ('"[bad string]' resp. "url([bad url])") instead of to
# the text they stand for. The enclosing declaration looks perfectly valid, so
# it never reached the fallback for unparseable CSS: the placeholders compared
# equal no matter what the source said.

# a string with a raw newline and an unquoted "url()" containing a quote
_BAD_STRING = 'a:"x\ny'
_BAD_URL = "a:url(p'q)r"


@pytest.mark.parametrize(('expected_css', 'actual_css'), [
    (_BAD_STRING, 'a:"z\ny'),
    (_BAD_URL, "a:url(s't)r"),
    # ... also when the token sits inside a function
    ('a:f("x\ny)', 'a:f("z\ny)'),
    # ... and next to a declaration which parses just fine
    (f'color:red;{_BAD_STRING}', 'color:red;a:"z\ny'),
])
def test_detects_differences_hidden_by_an_unserializable_token(expected_css, actual_css):
    result = compare_html(
        _style_attribute(expected_css),
        _style_attribute(actual_css),
    )
    assert not result.is_equal


@pytest.mark.parametrize('css', [_BAD_STRING, _BAD_URL])
def test_style_attribute_with_an_unserializable_token_is_equal_to_itself(css):
    html_str = _style_attribute(css)
    assert compare_html(html_str, html_str).is_equal


@pytest.mark.parametrize(('expected_css', 'actual_css'), [
    # in a declaration value
    ('p{content:"a\nb"}', 'p{content:"z\nb"}'),
    ("p{a:url(x'y)z}", "p{a:url(q'r)z}"),
    # in a selector
    ('p[title="a\n]{color:red}', 'p[title="z\n]{color:red}'),
    # in an at-rule prelude and in the body of a declaration-bodied at-rule
    ('@media (x:"a\n){p{color:red}}', '@media (x:"z\n){p{color:red}}'),
    ("@font-face{src:url(a'b)}", "@font-face{src:url(c'd)}"),
])
def test_style_tag_detects_differences_hidden_by_an_unserializable_token(
        expected_css, actual_css):
    result = compare_html(
        f'<style>{expected_css}</style>',
        f'<style>{actual_css}</style>',
    )
    assert not result.is_equal


@pytest.mark.parametrize('css', [
    'p{content:"a\nb"}',
    "p{a:url(x'y)z}",
    "@font-face{src:url(a'b)}",
])
def test_style_tag_with_an_unserializable_token_is_equal_to_itself(css):
    result = compare_html(f'<style>{css}</style>', f'<style>{css}</style>')
    assert result.is_equal


def test_compares_valid_declarations_next_to_an_unserializable_token_literally():
    # the fallback is the whole attribute, so the formatting of the valid
    # declaration next to the broken one becomes significant as well
    result = compare_html(
        _style_attribute(f'color:red;{_BAD_STRING}'),
        _style_attribute(f'color: red;{_BAD_STRING}'),
    )
    assert not result.is_equal


# --- At-Rules With A Declaration Body ---
#
# The body of "@font-face" (and "@page", "@property", ...) contains declarations
# while the body of "@media" (and "@supports", "@keyframes", ...) contains nested
# rules. Parsing the former as a rule list yields only tinycss2 parse errors,
# which used to raise a TypeError when serializing the normalized stylesheet.

@pytest.mark.parametrize('css', [
    '@font-face { font-family: x; src: url(a.woff2); }',
    '@page { margin: 1cm; }',
    '@page :first { margin: 1cm; }',
    '@viewport { width: device-width; }',
    '@-ms-viewport { width: device-width; }',
    '@counter-style x { system: cyclic; symbols: a; }',
    '@property --x { syntax: "<color>"; inherits: false; }',
])
def test_style_tag_with_declaration_body_at_rule_is_equal_to_itself(css):
    html = f'<style>{css}</style>'
    assert compare_html(html, html).is_equal


def test_style_tag_ignores_declaration_order_inside_font_face():
    result = compare_html(
        '<style>@font-face { font-family: x; src: url(a.woff2); }</style>',
        '<style>@font-face { src:url(a.woff2);font-family:x }</style>',
    )
    assert result.is_equal


def test_style_tag_detects_differences_inside_font_face():
    result = compare_html(
        '<style>@font-face { font-family: x; }</style>',
        '<style>@font-face { font-family: y; }</style>',
    )
    assert not result.is_equal


def test_style_tag_with_font_face_nested_in_media_query():
    result = compare_html(
        '<style>@media screen { @font-face { font-family: x; } }</style>',
        '<style>@media screen { @font-face { font-family: x; } }</style>',
    )
    assert result.is_equal

    result = compare_html(
        '<style>@media screen { @font-face { font-family: x; } }</style>',
        '<style>@media screen { @font-face { font-family: y; } }</style>',
    )
    assert not result.is_equal


@pytest.mark.parametrize('css', [
    '@media screen { .foo { width: 100%; } }',
    '@supports (display: grid) { .foo { display: grid; } }',
    '@keyframes spin { 0% { opacity: 0; } 100% { opacity: 1; } }',
    '@-webkit-keyframes spin { from { opacity: 0; } }',
])
def test_style_tag_still_treats_rule_body_at_rules_as_nested_rules(css):
    html = f'<style>{css}</style>'
    assert compare_html(html, html).is_equal


# --- Declarations Inside An At-Rule ---
#
# A declaration directly inside "@media" is invalid at the top level of a
# stylesheet and valid in a nested rule. Either way it must be compared, not
# dropped: the parser this used to use only knew rules and reported one as a
# parse error, which downgraded the whole stylesheet to a literal comparison.

@pytest.mark.parametrize(('expected_css', 'actual_css'), [
    ('@media screen{color:red}', '@media screen{color: red}'),
    ('@media screen{color:red}', '@media screen{color:red;}'),
    ('@media screen{margin:0px}', '@media screen{margin:0}'),
    ('@supports (a:b){color:red}', '@supports (a:b){color: red}'),
])
def test_style_tag_compares_a_declaration_inside_an_at_rule(expected_css, actual_css):
    result = compare_html(
        f'<style>{expected_css}</style>',
        f'<style>{actual_css}</style>',
    )
    assert result.is_equal


@pytest.mark.parametrize(('expected_css', 'actual_css'), [
    ('@media screen{color:red}', '@media screen{color:blue}'),
    ('@media screen{color:red}', '@media screen{}'),
    ('@media screen{color:red}', '@media screen{background:red}'),
    # a declaration next to a rule keeps its place: the order decides which wins
    ('@media screen{color:red;p{color:blue}}', '@media screen{p{color:blue};color:red}'),
])
def test_style_tag_detects_differences_in_a_declaration_inside_an_at_rule(
        expected_css, actual_css):
    result = compare_html(
        f'<style>{expected_css}</style>',
        f'<style>{actual_css}</style>',
    )
    assert not result.is_equal


# --- Conditional Comment Tests ---

def test_conditional_comment_ignores_whitespace_inside_nested_block_elements():
    """Whitespace inside nested block elements in conditional comments should be ignored.

    When content inside a conditional comment is formatted with indentation and newlines,
    html5lib parses these as TextNode children of the elements. For block-level elements
    like table/tr/td, this whitespace is semantically insignificant and should be ignored.
    """
    multi_line = '''<div><!--[if mso | IE]>
                <table>
                    <tr>
                        <td>
                            <v:image src="test.jpg" />
            <![endif]--></div>'''
    single_line = '<div><!--[if mso | IE]><table><tr><td><v:image src="test.jpg" /><![endif]--></div>'  # noqa: E501
    result = compare_html(multi_line, single_line)
    assert result.is_equal



class TestSelfClosingTagDetection:
    def test_detects_vml_rect_self_closing_vs_opening_tag(self):
        # v:rect is a VML element where self-closing syntax matters for Outlook.
        result = compare_html(
            '<div><v:rect style="width:100px" /></div>',
            '<div><v:rect style="width:100px" ></v:rect></div>',
        )
        assert not result.is_equal
        diff, = [d for d in result.differences if d.type == DifferenceType.SELF_CLOSING_MISMATCH]
        assert 'v:rect' in diff.path

    def test_detects_vml_fill_self_closing_difference(self):
        result = compare_html(
            '<v:fill color="red" />',
            '<v:fill color="red" ></v:fill>',
        )
        assert not result.is_equal

    def test_same_vml_self_closing_elements_are_equal(self):
        html = '<v:rect xmlns:v="urn:schemas-microsoft-com:vml" style="width:100px" />'
        assert compare_html(html, html).is_equal

    def test_same_vml_non_self_closing_elements_are_equal(self):
        html = '<v:rect style="width:100px"></v:rect>'
        assert compare_html(html, html).is_equal

    def test_detects_script_self_closing_difference(self):
        # <script /> behaves differently from <script></script> in browsers.
        result = compare_html(
            '<script src="app.js" />',
            '<script src="app.js"></script>',
        )
        assert not result.is_equal

    def test_detects_style_self_closing_difference(self):
        # <style /> behaves differently from <style></style> in browsers.
        result = compare_html(
            '<style type="text/css" />',
            '<style type="text/css"></style>',
        )
        assert not result.is_equal

    def test_ignores_html5_void_element_self_closing_br(self):
        assert compare_html('<br>', '<br/>').is_equal
        assert compare_html('<br>', '<br />').is_equal
        assert compare_html('<br/>', '<br />').is_equal

    def test_ignores_html5_void_element_self_closing_img(self):
        assert compare_html(
            '<img src="test.jpg" alt="">',
            '<img src="test.jpg" alt="" />',
        ).is_equal

    def test_ignores_html5_void_element_self_closing_input(self):
        assert compare_html(
            '<input type="text" name="foo">',
            '<input type="text" name="foo" />',
        ).is_equal

    def test_ignores_html5_void_element_self_closing_meta(self):
        assert compare_html(
            '<meta charset="utf-8">',
            '<meta charset="utf-8" />',
        ).is_equal

    def test_ignores_regular_div_self_closing(self):
        # Regular HTML elements like div - self-closing doesn't matter semantically.
        # Note: both become <div></div> after parsing, self-closing div is invalid HTML
        assert compare_html('<div />', '<div></div>').is_equal

    def test_vml_in_conditional_comment(self):
        # VML self-closing detection works also inside conditional comments.
        result = compare_html(
            '<div><!--[if mso]><v:rect style="width:100px" /><![endif]--></div>',
            '<div><!--[if mso]><v:rect style="width:100px" ></v:rect><![endif]--></div>',
        )
        assert not result.is_equal

    def test_multiple_vml_elements_with_mixed_self_closing(self):
        # Each VML element's self-closing status is checked independently.
        html = '<v:rect /><v:fill /><v:stroke />'
        assert compare_html(html, html).is_equal

        # different self-closing on v:fill
        result = compare_html(
            '<v:rect /><v:fill /><v:stroke />',
            '<v:rect /><v:fill ></v:fill><v:stroke />',
        )
        assert not result.is_equal

    def test_detects_textarea_self_closing_difference(self):
        # <textarea /> is invalid and may cause rendering issues.
        result = compare_html(
            '<textarea name="comment" />',
            '<textarea name="comment"></textarea>',
        )
        assert not result.is_equal

    def test_detects_iframe_self_closing_difference(self):
        result = compare_html(
            '<iframe src="page.html" />',
            '<iframe src="page.html"></iframe>',
        )
        assert not result.is_equal

    def test_unknown_vml_namespace_element(self):
        # Any v: prefixed element should have self-closing checked.
        result = compare_html(
            '<v:customshape fill="red" />',
            '<v:customshape fill="red"></v:customshape>',
        )
        assert not result.is_equal

    def test_office_namespace_element(self):
        # o: prefixed elements (Office namespace) should have self-closing checked.
        result = compare_html(
            '<o:lock aspectratio="t" />',
            '<o:lock aspectratio="t"></o:lock>',
        )
        assert not result.is_equal
