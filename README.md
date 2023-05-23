htmlcompare
=============

A Python library to ensure two HTML documents are "equal". Currently the functionality is very limited but the idea is that the library should ignore differences automatically when these are not relevant for HTML semantics (e.g. `<img style="">` is the same as `<img>`, `style="color: black; font-weight: bold"` is equal to `style="font-weight:bold;color:black;"`).

Usage
--------------

```python
import htmlcompare

diff = htmlcompare.compare('<div>', '<p>')
is_same = bool(diff)
```

To ease testing the library provides some helpers

```python
from htmlcompare import assert_different_html, assert_same_html

assert_different_html('<br>', '<p>')
assert_same_html('<div />', '<div></div>')
```

Implemented Features
----------------------

- ignores whitespace between HTML tags
- `<div />` is treated like `<div></div>`
- ordering of HTML attributes does not matter: `<div class="…" style="…" />` is treated equal to `<div style="…" class="…" />`
- HTML comments are ignored (yes, also [conditional comments](https://en.wikipedia.org/wiki/Conditional_comment) unfortunately)
- ordering of CSS classes inside `class` attribute does not matter: `<div class="foo bar" />` is the same as `<div class="bar foo" />`.
- a `style` or `class` attribute with empty content (e.g. `style=""`) is considered the same as an absent `style`/`class` attribute.
- inline style declarations are parsed with an actual CSS parser: ordering, whitespace and trailing semicolons do not matter (Python 3.5+ only)
- `0px` is considered equal to `0` in inline CSS.


Limitations / Plans
----------------------
**Only basic CSS support**. Declarations in `style` attributes are parsed with [tinycss2](https://github.com/Kozea/tinycss2) (Python 3.5+) so ordering of declarations and extra whitespace should not matter. `tinycss2` does not support Python 2 and 3.4 so the only help here is to strip trailing `;`s in `style` attributes. Contents of `<style>` tags are completely ignored for now (even with `tinycss2`).

**No validation of conditional comments**. Not sure which library I can use here but at some point I'll likely need this as well.

**JavaScript** - for obvious reasons it will be impossible to implement perfect JS comparison but it might be possible to run some kind of "beautifier" to take care of insignificant stylistic changes. However I don't need this feature so this is unlikely to get implemented (unless contributed by someone else).

**Custom hooks** could help adapting the comparison to your specific needs. However I don't know which API would be best so this will wait until there are real-world use cases.

**Better API**: The current API is very minimal and implements just what I needed right now. I hope to improve the API once I use this project in more complex scenarios.


Other projects
--------------
[xmldiff](https://github.com/Shoobx/xmldiff) is a well established project to compare two XML documents. However it seems as if the code does not contain knowledge about specific HTML semantics (e.g. CSS, empty attributes, insignificant attribute order).


Misc
--------------
The code is licensed under the MIT license. It supports Python 2.7 and Python 3.4+ though some features are only available for Python 3.5+.


