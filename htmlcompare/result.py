# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


__all__ = ['ComparisonResult', 'Difference', 'DifferenceType']


class DifferenceType(Enum):
    """Types of differences that can be detected between HTML trees."""
    TAG_MISMATCH = auto()
    TEXT_MISMATCH = auto()
    ATTRIBUTE_MISMATCH = auto()
    ATTRIBUTE_MISSING = auto()
    ATTRIBUTE_EXTRA = auto()
    CLASS_MISSING = auto()
    CLASS_EXTRA = auto()
    CHILD_COUNT_MISMATCH = auto()
    CHILD_MISSING = auto()
    CHILD_EXTRA = auto()
    NODE_TYPE_MISMATCH = auto()
    COMMENT_MISMATCH = auto()


@dataclass
class Difference:
    """Represents a single difference between two HTML trees."""
    type: DifferenceType
    path: str  # e.g., "html > body > div[0] > p[1]"
    expected: Any
    actual: Any
    message: str = ""

    def __str__(self) -> str:
        if self.message:
            return f"{self.type.name} at {self.path}: {self.message}"
        return f"{self.type.name} at {self.path}: expected {self.expected!r}, got {self.actual!r}"


@dataclass(frozen=True)
class ComparisonResult:
    is_equal: bool
    differences: list[Difference]

    def __bool__(self) -> bool:
        return self.is_equal

    def __str__(self) -> str:
        if self.is_equal:
            return "HTML documents are equal"
        diff_strs = [str(d) for d in self.differences]
        return "HTML documents differ:\n" + "\n".join(f"  - {d}" for d in diff_strs)
