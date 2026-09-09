htmlcompare
=============

A Python library to ensure two HTML documents are "equal". Currently the functionality is very limited but the idea is that the library should ignore differences automatically when these are not relevant for HTML semantics (e.g. `<img style="">` is the same as `<img>`, `style="color: black; font-weight: bold"` is equal to `style="font-weight:bold;color:black;"`).

Usage
--------------

```python
import htmlcompare

diff = htmlcompare.compare_html('<div>', '<p>')
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
- inline style declarations and `<style>` tags are parsed with an actual CSS parser: trailing semicolons do not matter
- the order of CSS declarations does not matter - except between declarations whose property names begin with the same segment (`background` and `background-color`, but also `font-size` and `font-weight`). CSS makes the order significant as soon as one declaration can override another, so those keep the order they were written in.
- at-rules inside `<style>` tags are compared semantically as well - both those containing nested rules (`@media`, `@supports`, `@keyframes`) and those containing declarations (`@font-face`, `@page`, `@counter-style`, …).
- whitespace inside a CSS selector is significant because it is the descendant combinator: `.a .b` is *not* the same as `.a.b`. Whitespace around a combinator (`a > b`) or a comma (`a, b`) does not matter, nor does the length of a whitespace run.
- whitespace inside a CSS declaration is significant as well because it separates the component values: `font-family: Arial Black` is *not* the same as `font-family: ArialBlack`. Whitespace around a comma or a slash (`font: 12px / 1.5 serif`) does not matter, nor does the length of a whitespace run. The same applies inside a function, so `rgb(1, 2, 3)` is the same as `rgb(1,2,3)` and `linear-gradient(to right, red, blue)` the same as `linear-gradient(to right,red,blue)`. `calc()` still keeps the whitespace CSS requires around `+` and `-`, and a zero length inside a function keeps its unit because `calc(0 + 1px)` is invalid where `calc(0px + 1px)` is not.
- CSS property names are compared case-insensitively: `COLOR: red` is the same as `color: red`. Custom properties are the exception because CSS defines them as case-sensitive: `--Foo` is *not* the same as `--foo`.
- the *value* of a custom property is not normalized at all: CSS keeps it as written and `var()` substitutes it literally, so `--x: 0px` is *not* the same as `--x: 0` (only the former makes `calc(var(--x) + 1px)` valid) and `--x: a  b` is not the same as `--x: a b`. Only the whitespace around the value is insignificant, because CSS defines the value as the token sequence with leading and trailing whitespace removed: `--x: red` and `--x:red` are the same declaration.
- a zero length is considered equal to a bare `0`, no matter how it is written: `margin: 0px`, `margin: 0.0px` and `margin: 0` are all the same. Only lengths may drop their unit though, so `0%`, `0s` and `0deg` are *not* the same as `0`.
- malformed CSS in a `<style>` tag never raises: a declaration block which does not parse is compared literally (its formatting still does not matter) while the rest of the stylesheet is compared as usual. A `<style>` tag whose block structure is broken (e.g. a stray `}`) is compared literally as a whole, because the CSS parser does not preserve the source text of a structural error.
- a malformed `style` attribute never raises either: `style="color red"`, `style="padding"`, `style="*zoom:1"` and `style="@media screen{color:red}"` used to raise an `AssertionError` (and, because that was an `assert`, compared *equal* under `python -O`). Such an attribute is compared literally as a whole, so only the length of whitespace runs is ignored there.
- CSS which *looks* valid but contains a token the CSS parser can not represent is compared literally as well. A string which is not closed before the line ends (`content: "a`) and an unquoted `url()` containing a quote (`background: url(a'b)`) are both replaced by a fixed placeholder (`"[bad string]` resp. `url([bad url])`), so comparing the parse result would let any two of them pass as equal. A `style` attribute containing such a token is compared literally as a whole, and so is a `<style>` tag — the placeholder is all that is left of the source text, no matter which rule the token appeared in.
- text before the `<!DOCTYPE>` (e.g. `{# … #}` metadata emitted by a template engine) no longer corrupts the parse. It used to push the whole document into `<body>` and drop the DOCTYPE, which produced differences that pointed at the wrong nodes. Such a prefix is kept separately and compared only with `CompareOptions(compare_document_prefix=True)` — opt-in so an ordinary comment before the DOCTYPE does not suddenly become a significant difference. When enabled it is compared literally (only the whitespace separating it from the DOCTYPE is ignored), because the point of the feature is exact preservation. Note that the prefix is split off at the first `<!doctype`, so a leading comment mentioning one wins over the real declaration.
- conditional comments are considered when checking for equality, in both of their syntactic forms: the downlevel-*hidden* one (`<!--[if IE]>…<![endif]-->`), whose HTML is part of the comment, and the downlevel-*revealed* one (`<!--[if !mso]><!-->…<!--<![endif]-->` as well as `<![if !IE]>…<![endif]>`), whose HTML is visible to every browser. In the revealed form only the two markers are comments, so they are compared as markers while the HTML between them is compared like any other content — dropping a marker changes which clients display it and is therefore reported as a difference. Regular comments are ignored by default; `ignore_conditional_comments=True` drops the conditional ones as well.


Limitations / Plans
----------------------
**No validation of conditional comments**. Not sure which library I can use here but at some point I'll likely need this as well.

**JavaScript** - for obvious reasons it will be impossible to implement perfect JS comparison but it might be possible to run some kind of "beautifier" to take care of insignificant stylistic changes. However I don't need this feature so this is unlikely to get implemented (unless contributed by someone else).

**Custom hooks** could help adapting the comparison to your specific needs. However I don't know which API would be best so this will wait until there are real-world use cases.

**Better API**: The current API is very minimal and implements just what I needed right now. I hope to improve the API once I use this project in more complex scenarios.


Other projects
--------------
[xmldiff](https://github.com/Shoobx/xmldiff) is a well established project to compare two XML documents. However it seems as if the code does not contain knowledge about specific HTML semantics (e.g. CSS, empty attributes, insignificant attribute order).


Misc
--------------
The code is licensed under the MIT license. It requires Python 3.9+.
