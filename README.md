htmlcompare
=============

A Python library to ensure two HTML documents are "equal". Currently the functionality is very limited but the idea is that the library should ignore differences automatically when these are not relevant for HTML semantics (e.g. `<img style="">` should be the same as `<img>`.

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

Limitations / Plans
----------------------
**CSS is currently not validated**. Later I hope to add CSS parsing using a real CSS parser like [tinycss2](https://github.com/Kozea/tinycss2) but right now the only support for CSS is that contents of `<style>` tags is completely ignored and that trailing `;`s in `style` attributes are stripped.

**No validation of conditional comments**. Not sure which library I can use here but at some point I'll likely need this as well.

**JavaScript** - for obvious reasons it will be impossible to implement perfect JS comparison but it might be possible to run some kind of "beautifier" to take care of insignificant stylistic changes. However I don't need this feature so this is unlikely to get implemented (unless contributed by someone else).

**Custom hooks** could help adapting the comparison to your specific needs. However I don't know which API would be best so this will wait until there are real-world use cases.

**Better API**: The current API is very minimal and implements just what I needed right now. I hope to improve the API once I use this project in more complex scenarios.


Other projects
--------------
[xmldiff](https://github.com/Shoobx/xmldiff) is a well established project to compare two XML documents. However it seems as if the code does not contain knowledge about specific HTML semantics (e.g. CSS, empty attributes, insignificant attribute order).


Misc
--------------
The code is licensed under the MIT license. It supports Python 2.7 and Python 3.4+.


