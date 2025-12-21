# SPDX-License-Identifier: MIT


from htmlcompare.compare_v2 import compare_html2
from htmlcompare.result import DifferenceType


def test_identical_documents_are_equal():
    result = compare_html2('<div></div>', '<div></div>')
    assert result.is_equal
    assert result.differences == []


def test_identical_nested_documents_are_equal():
    result = compare_html2(
        '<div><p>hello</p></div>',
        '<div><p>hello</p></div>',
    )
    assert result.is_equal


def test_identical_with_attributes_are_equal():
    result = compare_html2(
        '<div class="foo" id="bar"></div>',
        '<div class="foo" id="bar"></div>',
    )
    assert result.is_equal


def test_different_tags_detected():
    result = compare_html2('<div></div>', '<span></span>')
    assert not result.is_equal
    assert len(result.differences) == 1
    tag_diff, = [d for d in result.differences if d.type == DifferenceType.TAG_MISMATCH]
    assert tag_diff.expected == 'div'
    assert tag_diff.actual == 'span'


def test_nested_tag_mismatch():
    result = compare_html2(
        '<div><p>text</p></div>',
        '<div><span>text</span></div>',
    )
    assert not result.is_equal
    tag_diff, = [d for d in result.differences if d.type == DifferenceType.TAG_MISMATCH]
    assert tag_diff.expected == 'p'
    assert tag_diff.actual == 'span'



def test_different_text_detected():
    result = compare_html2('<p>foo</p>', '<p>bar</p>')
    assert not result.is_equal
    text_diff, = [d for d in result.differences if d.type == DifferenceType.TEXT_MISMATCH]
    assert text_diff.expected == 'foo'
    assert text_diff.actual == 'bar'



def test_text_vs_empty_detected():
    result = compare_html2('<p>hello</p>', '<p></p>')
    assert not result.is_equal


def test_different_attribute_values_detected():
    result = compare_html2(
        '<div class="foo"></div>',
        '<div class="bar"></div>',
    )
    assert not result.is_equal
    attr_diff, = [d for d in result.differences if d.type == DifferenceType.ATTRIBUTE_MISMATCH]
    assert attr_diff.expected == 'foo'
    assert attr_diff.actual == 'bar'


def test_missing_attribute_detected():
    result = compare_html2(
        '<div class="foo"></div>',
        '<div></div>',
    )
    assert not result.is_equal
    attr_diffs = [d for d in result.differences if d.type == DifferenceType.ATTRIBUTE_MISSING]
    assert len(attr_diffs) >= 1


def test_extra_attribute_detected():
    result = compare_html2(
        '<div></div>',
        '<div class="foo"></div>',
    )
    assert not result.is_equal
    attr_diffs = [d for d in result.differences if d.type == DifferenceType.ATTRIBUTE_EXTRA]
    assert len(attr_diffs) >= 1


def test_ignores_attribute_ordering():
    result = compare_html2(
        '<div data-hidden="true" class="hidden"></div>',
        '<div class="hidden" data-hidden="true"></div>',
    )
    assert result.is_equal


def test_ignores_attribute_ordering_multiple_attributes():
    result = compare_html2(
        '<div id="x" class="foo" data-value="1"></div>',
        '<div data-value="1" id="x" class="foo"></div>',
    )
    assert result.is_equal


def test_can_detect_different_attribute_value():
    result = compare_html2(
        '<div style="color: green"></div>',
        '<div style="color: red"></div>',
    )
    assert not result.is_equal


def test_can_detect_missing_attribute_img_alt():
    """<img alt=""> has different semantic meaning than <img>."""
    result = compare_html2(
        '<img alt="">',
        '<img>',
    )
    assert not result.is_equal
    attr_diffs = [d for d in result.differences if d.type == DifferenceType.ATTRIBUTE_MISSING]
    assert len(attr_diffs) >= 1


def test_extra_child_detected():
    result = compare_html2(
        '<div></div>',
        '<div><p>extra</p></div>',
    )
    assert not result.is_equal
    child_diffs = [d for d in result.differences if d.type == DifferenceType.CHILD_EXTRA]
    assert len(child_diffs) >= 1


def test_missing_child_detected():
    result = compare_html2(
        '<div><p>expected</p></div>',
        '<div></div>',
    )
    assert not result.is_equal
    child_diffs = [d for d in result.differences if d.type == DifferenceType.CHILD_MISSING]
    assert len(child_diffs) >= 1


def test_multiple_children_comparison():
    result = compare_html2(
        '<div><p>a</p><p>b</p></div>',
        '<div><p>a</p><p>b</p></div>',
    )
    assert result.is_equal


def test_child_order_matters():
    result = compare_html2(
        '<div><p>a</p><span>b</span></div>',
        '<div><span>b</span><p>a</p></div>',
    )
    assert not result.is_equal


def test_identical_comments_are_equal():
    result = compare_html2(
        '<div><!-- comment --></div>',
        '<div><!-- comment --></div>',
    )
    assert result.is_equal


def test_different_comments_detected():
    result = compare_html2(
        '<div><!-- comment a --></div>',
        '<div><!-- comment b --></div>',
    )
    assert not result.is_equal
    comment_diffs = [d for d in result.differences if d.type == DifferenceType.COMMENT_MISMATCH]
    assert len(comment_diffs) >= 1


def test_result_str_for_equal():
    result = compare_html2('<div></div>', '<div></div>')
    assert 'equal' in str(result).lower()


def test_result_str_for_different():
    result = compare_html2('<div></div>', '<span></span>')
    result_str = str(result)
    assert 'differ' in result_str.lower()
    assert 'TAG_MISMATCH' in result_str


def test_result_bool_true_when_equal():
    result = compare_html2('<div></div>', '<div></div>')
    assert bool(result) is True


def test_result_bool_false_when_different():
    result = compare_html2('<div></div>', '<span></span>')
    assert bool(result) is False


def test_difference_path_includes_element():
    result = compare_html2(
        '<div><p>expected</p></div>',
        '<div><p>actual</p></div>',
    )
    assert not result.is_equal
    # path should include the element hierarchy
    text_diffs = [d for d in result.differences if d.type == DifferenceType.TEXT_MISMATCH]
    assert len(text_diffs) >= 1
    assert 'p' in text_diffs[0].path


def test_difference_str_includes_values():
    result = compare_html2('<p>expected</p>', '<p>actual</p>')
    text_diffs = [d for d in result.differences if d.type == DifferenceType.TEXT_MISMATCH]
    diff_str = str(text_diffs[0])
    assert 'expected' in diff_str
    assert 'actual' in diff_str
