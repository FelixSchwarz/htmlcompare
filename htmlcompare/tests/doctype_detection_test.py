from typing import Sequence

from htmlcompare.compare import compare_html
from htmlcompare.result import Difference, DifferenceType


def test_identical_html5_doctypes_are_equal():
    html = '<!DOCTYPE html><html><body></body></html>'
    assert compare_html(html, html).is_equal

def test_both_without_doctype_are_equal():
    html = '<html><body></body></html>'
    assert compare_html(html, html).is_equal

def test_detects_missing_doctype():
    html = '<html><body></body></html>'
    result = compare_html(f'<!DOCTYPE html>{html}', html)
    assert not result.is_equal
    doctype_diff = _ensure_single_difference(result.differences, DifferenceType.DOCTYPE_MISSING)
    assert doctype_diff.path == 'DOCTYPE'
    assert '<!DOCTYPE html>' in doctype_diff.expected

def test_detects_extra_doctype():
    html = '<html><body></body></html>'
    result = compare_html(html, f'<!DOCTYPE html>{html}')
    assert not result.is_equal
    assert not result.is_equal
    doctype_diff = _ensure_single_difference(result.differences, DifferenceType.DOCTYPE_EXTRA)
    assert doctype_diff.path == 'DOCTYPE'
    assert '<!DOCTYPE html>' in doctype_diff.actual

def test_detects_different_doctype_public_id():
    html = '<html><body></body></html>'
    html5_doctype = '<!DOCTYPE html>'
    xhtml_doctype = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'
    result = compare_html(html5_doctype + html, xhtml_doctype + html)
    assert not result.is_equal
    doctype_diff = _ensure_single_difference(result.differences, DifferenceType.DOCTYPE_MISMATCH)
    assert doctype_diff.path == 'DOCTYPE'
    assert '<!DOCTYPE html>' == doctype_diff.expected
    assert 'XHTML 1.0 Transitional' in doctype_diff.actual

def test_detects_different_doctype_system_id():
    transitional_doctype = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'
    strict_doctype = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'
    html = '<html><body></body></html>'
    result = compare_html(transitional_doctype + html, strict_doctype + html)
    assert not result.is_equal
    doctype_diff = _ensure_single_difference(result.differences, DifferenceType.DOCTYPE_MISMATCH)
    assert 'Transitional' in doctype_diff.expected
    assert 'Strict' in doctype_diff.actual

def test_identical_xhtml_doctypes_are_equal():
    html = '<html><body></body></html>'
    xhtml_doctype = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'
    xhtml = xhtml_doctype + html
    assert compare_html(xhtml, xhtml).is_equal

def test_html_strict_doctype():
    html = '<html><body></body></html>'
    html5_doctype = '<!DOCTYPE html>'
    strict_doctype = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">'
    result = compare_html(strict_doctype + html, html5_doctype + html)
    assert not result.is_equal
    doctype_diff = _ensure_single_difference(result.differences, DifferenceType.DOCTYPE_MISMATCH)
    assert 'HTML 4.01' in doctype_diff.expected

def _ensure_single_difference(
    differences: Sequence[Difference],
    expected_type: DifferenceType,
) -> Difference:
    _diffs = [d for d in differences if d.type == expected_type]
    assert len(_diffs) == 1
    return _diffs[0]
