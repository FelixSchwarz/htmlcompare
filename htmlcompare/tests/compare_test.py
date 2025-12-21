# SPDX-License-Identifier: MIT


import pytest

from htmlcompare.compare import compare_html
from htmlcompare.options import CompareOptions
from htmlcompare.result import DifferenceType


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


@pytest.mark.xfail(reason="shorthand hex color matching not yet implemented")
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
