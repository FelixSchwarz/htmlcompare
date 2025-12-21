# SPDX-License-Identifier: MIT

from dataclasses import dataclass


__all__ = ['CompareOptions']

@dataclass(frozen=True)
class CompareOptions:
    ignore_comments: bool = True
    """Whether HTML comments should be ignored when comparing for equality."""

    ignore_conditional_comments: bool = False
    """Whether IE conditional comments should be ignored when comparing for equality."""
