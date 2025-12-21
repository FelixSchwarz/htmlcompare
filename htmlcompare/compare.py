# SPDX-License-Identifier: MIT

from collections.abc import Sequence

from htmlcompare.compare_css import compare_css
from htmlcompare.nodes import Comment, ConditionalComment, Document, Element, Node, TextNode
from htmlcompare.normalize import normalize_tree
from htmlcompare.options import CompareOptions
from htmlcompare.parser import parse_html
from htmlcompare.result import ComparisonResult, Difference, DifferenceType


__all__ = ['compare_html']


def compare_html(
    expected_html: str,
    actual_html: str,
    options: CompareOptions | None = None,
) -> ComparisonResult:
    """
    Compare two HTML strings for equality.

    This implementation uses a tree-based approach with normalization
    to handle insignificant whitespace between block elements.
    """
    expected_tree = parse_html(expected_html)
    actual_tree = parse_html(actual_html)

    # normalize trees to remove insignificant whitespace
    expected_normalized = normalize_tree(expected_tree, options)
    actual_normalized = normalize_tree(actual_tree, options)
    return _compare_trees(expected_normalized, actual_normalized)


def _compare_trees(expected: Document, actual: Document) -> ComparisonResult:
    differences: list[Difference] = []
    _compare_node_lists(expected.children, actual.children, "", differences)
    _documents_are_equal = (len(differences) == 0)
    return ComparisonResult(is_equal=_documents_are_equal, differences=differences)


def _compare_node_lists(
    expected: Sequence[Node],
    actual: Sequence[Node],
    path: str,
    differences: list[Difference],
) -> None:
    max_len = max(len(expected), len(actual))

    for i in range(max_len):
        child_path = f"{path}[{i}]" if path else f"[{i}]"

        if i >= len(expected):
            # Extra node in actual
            actual_node = actual[i]
            differences.append(Difference(
                type=DifferenceType.CHILD_EXTRA,
                path=child_path,
                expected=None,
                actual=_node_summary(actual_node),
                message=f"unexpected node: {_node_summary(actual_node)}",
            ))
            continue

        if i >= len(actual):
            # Missing node in actual
            expected_node = expected[i]
            differences.append(Difference(
                type=DifferenceType.CHILD_MISSING,
                path=child_path,
                expected=_node_summary(expected_node),
                actual=None,
                message=f"missing node: {_node_summary(expected_node)}",
            ))
            continue

        _compare_nodes(expected[i], actual[i], child_path, differences)


def _compare_nodes(
    expected: Node,
    actual: Node,
    path: str,
    differences: list[Difference],
) -> None:
    if type(expected) is not type(actual):
        differences.append(Difference(
            type=DifferenceType.NODE_TYPE_MISMATCH,
            path=path,
            expected=type(expected).__name__,
            actual=type(actual).__name__,
        ))
        return

    if isinstance(expected, Element):
        assert isinstance(actual, Element)
        _compare_elements(expected, actual, path, differences)
    elif isinstance(expected, TextNode):
        assert isinstance(actual, TextNode)
        _compare_text_nodes(expected, actual, path, differences)
    elif isinstance(expected, Comment):
        assert isinstance(actual, Comment)
        _compare_comments(expected, actual, path, differences)
    elif isinstance(expected, ConditionalComment):
        assert isinstance(actual, ConditionalComment)
        _compare_conditional_comments(expected, actual, path, differences)


def _compare_elements(
    expected: Element,
    actual: Element,
    path: str,
    differences: list[Difference],
) -> None:
    element_path = f"{path} > {expected.tag}" if path else expected.tag

    # check tag names
    if expected.tag != actual.tag:
        differences.append(Difference(
            type=DifferenceType.TAG_MISMATCH,
            path=element_path,
            expected=expected.tag,
            actual=actual.tag,
        ))
        return  # don't compare children if tags differ

    _compare_attributes(expected.attributes, actual.attributes, element_path, differences)
    # compare children
    _compare_node_lists(expected.children, actual.children, element_path, differences)


def _compare_attributes(
    expected: dict[str, str],
    actual: dict[str, str],
    path: str,
    differences: list[Difference],
) -> None:
    expected_normalized = _normalize_attributes(expected)
    actual_normalized = _normalize_attributes(actual)
    all_keys = set(expected_normalized) | set(actual_normalized)
    for key in sorted(all_keys):
        if key not in expected_normalized:
            differences.append(Difference(
                type=DifferenceType.ATTRIBUTE_EXTRA,
                path=f"{path}@{key}",
                expected=None,
                actual=actual_normalized[key],
                message=f"unexpected attribute '{key}'",
            ))
        elif key not in actual_normalized:
            differences.append(Difference(
                type=DifferenceType.ATTRIBUTE_MISSING,
                path=f"{path}@{key}",
                expected=expected_normalized[key],
                actual=None,
                message=f"missing attribute '{key}'",
            ))
        elif key == 'class':
            _compare_class_attribute(
                expected_normalized[key], actual_normalized[key], path, differences
            )
        elif key == 'style':
            _compare_style_attribute(
                expected_normalized[key], actual_normalized[key], path, differences
            )
        elif expected_normalized[key] != actual_normalized[key]:
            differences.append(Difference(
                type=DifferenceType.ATTRIBUTE_MISMATCH,
                path=f"{path}@{key}",
                expected=expected_normalized[key],
                actual=actual_normalized[key],
            ))


def _normalize_attributes(attrs: dict[str, str]) -> dict[str, str]:
    """Normalize attributes, removing empty class/style attributes."""
    result = {}
    for key, value in attrs.items():
        # an empty class attribute is same as absent
        if key == 'class' and not value.strip():
            continue
        # an empty style attribute is same as absent
        if key == 'style' and not value.strip():
            continue
        result[key] = value
    return result


def _compare_class_attribute(
    expected: str,
    actual: str,
    path: str,
    differences: list[Difference],
) -> None:
    expected_classes = set(expected.split())
    actual_classes = set(actual.split())

    missing = expected_classes - actual_classes
    extra = actual_classes - expected_classes

    if missing:
        differences.append(Difference(
            type=DifferenceType.CLASS_MISSING,
            path=f"{path}@class",
            expected=sorted(missing),
            actual=None,
            message=f"missing classes: {sorted(missing)}",
        ))
    if extra:
        differences.append(Difference(
            type=DifferenceType.CLASS_EXTRA,
            path=f"{path}@class",
            expected=None,
            actual=sorted(extra),
            message=f"unexpected classes: {sorted(extra)}",
        ))


def _compare_style_attribute(
    expected: str,
    actual: str,
    path: str,
    differences: list[Difference],
) -> None:
    """Compare style attributes using CSS-aware comparison."""
    if compare_css(expected, actual):
        return  # styles are equivalent

    differences.append(Difference(
        type=DifferenceType.STYLE_MISMATCH,
        path=f"{path}@style",
        expected=expected,
        actual=actual,
    ))


def _compare_text_nodes(
    expected: TextNode,
    actual: TextNode,
    path: str,
    differences: list[Difference],
) -> None:
    if expected.content != actual.content:
        differences.append(Difference(
            type=DifferenceType.TEXT_MISMATCH,
            path=path,
            expected=expected.content,
            actual=actual.content,
        ))


def _compare_comments(
    expected: Comment,
    actual: Comment,
    path: str,
    differences: list[Difference],
) -> None:
    if expected.content != actual.content:
        differences.append(Difference(
            type=DifferenceType.COMMENT_MISMATCH,
            path=path,
            expected=expected.content,
            actual=actual.content,
        ))


def _compare_conditional_comments(
    expected: ConditionalComment,
    actual: ConditionalComment,
    path: str,
    differences: list[Difference],
) -> None:
    cc_path = f"{path} > <!--[if {expected.condition}]>" if path else f"<!--[if {expected.condition}]>"  # noqa: E501

    # Compare conditions
    if expected.condition != actual.condition:
        differences.append(Difference(
            type=DifferenceType.CONDITIONAL_COMMENT_CONDITION_MISMATCH,
            path=cc_path,
            expected=expected.condition,
            actual=actual.condition,
        ))
        return  # don't compare children if conditions differ

    # Compare children
    _compare_node_lists(expected.children, actual.children, cc_path, differences)


def _node_summary(node: Node) -> str:
    if isinstance(node, Element):
        return f"<{node.tag}>"
    elif isinstance(node, TextNode):
        content = node.content[:20] + "..." if len(node.content) > 20 else node.content
        return f"text({content!r})"
    elif isinstance(node, Comment):
        content = node.content[:20] + "..." if len(node.content) > 20 else node.content
        return f"comment({content!r})"
    elif isinstance(node, ConditionalComment):
        return f"<!--[if {node.condition}]>..."
    return str(type(node).__name__)
