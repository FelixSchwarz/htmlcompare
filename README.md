htmlcompare
=============

A Python library to check whether two HTML documents are "the same". It ignores
differences which do not change what the document means, so a test does not fail
just because a template engine emitted the attributes in a different order or
wrote `margin: 0px` instead of `margin: 0`.


Usage
--------------

```python
import htmlcompare

result = htmlcompare.compare_html(expected_html, actual_html)
if not result:
    print(result)
```

`compare_html()` returns a `ComparisonResult` which is true when both documents
are the same. `result.differences` contains one `Difference` per mismatch,
including the path to the node which caused it.

For tests the library provides two assertions:

```python
from htmlcompare import assert_different_html, assert_same_html

assert_same_html('<div />', '<div></div>')
assert_different_html('<br>', '<p>')
```

Two files can also be compared on the command line:

```
htmlcompare expected.html actual.html
```


What is ignored
----------------------

- whitespace between tags, and `<div />` written as `<div></div>`
- the order of HTML attributes, and the order of the CSS classes inside a
  `class` attribute
- an empty `style` or `class` attribute, which is treated like an absent one
- HTML comments
- the formatting of CSS. `style` attributes and `<style>` tags are parsed with a
  real CSS parser, so trailing semicolons, the order of declarations, the case of
  property and function names, the spelling of a URL (`url(a.png)`,
  `url("a.png")`), a unit on a zero length and any whitespace CSS has no use for
  do not matter. At-rules (`@media`, `@font-face`, …) are compared the same way.


What is a difference
----------------------

Something is only ignored when HTML and CSS guarantee that both spellings mean
the same thing. Where the meaning can change, the documents differ:

- whitespace which CSS gives a meaning to: `.a .b` is the descendant combinator
  and not `.a.b`, `font-family: Arial Black` is not `font-family: ArialBlack`
- the order of declarations which can override each other, such as `background`
  and `background-color`
- custom properties, whose names are case-sensitive and whose values `var()`
  substitutes literally: `--x: 0px` is not the same as `--x: 0`
- [conditional comments](https://en.wikipedia.org/wiki/Conditional_comment) in
  both their forms, because dropping one changes which clients display the
  content

Malformed CSS never raises an exception. Whatever the CSS parser can not
represent is compared as source text instead, which may report a difference
which is not one but never hides one.


Options
----------------------

`compare_html()` and both assertions take a `CompareOptions` instance:

| option                        | default | effect                                                                                                                                                              |
| ----------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ignore_comments`             | `True`  | ignore HTML comments                                                                                                                                                |
| `ignore_conditional_comments` | `False` | ignore conditional comments as well                                                                                                                                 |
| `compare_document_prefix`     | `False` | compare text before the `<!DOCTYPE>` (e.g. `{# … #}` metadata emitted by a template engine). Such a prefix is always preserved, it is just not compared by default. |


Limitations / Plans
----------------------
**No validation of conditional comments**. Their condition is compared but not checked for validity. Not sure which library I can use here but at some point I'll likely need this as well.

**JavaScript** - for obvious reasons it will be impossible to implement perfect JS comparison but it might be possible to run some kind of "beautifier" to take care of insignificant stylistic changes. However I don't need this feature so this is unlikely to get implemented (unless contributed by someone else).

**Custom hooks** could help adapting the comparison to your specific needs. However I don't know which API would be best so this will wait until there are real-world use cases.

**Better API**: The current API is very minimal and implements just what I needed right now. I hope to improve the API once I use this project in more complex scenarios.


Other projects
--------------
[xmldiff](https://github.com/Shoobx/xmldiff) is a well established project to compare two XML documents. However it seems as if the code does not contain knowledge about specific HTML semantics (e.g. CSS, empty attributes, insignificant attribute order).


Misc
--------------
The code is licensed under the MIT license. It requires Python 3.9+.
