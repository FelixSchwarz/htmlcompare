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
