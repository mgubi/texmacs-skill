---
name: texmacs
description: Read, write, convert and typeset GNU TeXmacs documents (.tm). Use whenever a task involves a .tm file, the TeXmacs app, converting LaTeX/beamer to native TeXmacs, TeXmacs presentations (beamer style, screens), the TikZ plugin, or exporting TeXmacs to PDF headlessly.
---

# TeXmacs documents

A practical guide for agents working with GNU TeXmacs, collected while
converting lecture notes and talks, writing style packages and auditing long
mathematical manuscripts. Keep it alive: append what is newly learnt to
"Pitfalls" and keep the scripts in `scripts/` working. Project-specific
additions belong in a separate local skill that points here; the
"Conventions (mandatory)" section applies everywhere.
Source: <https://github.com/mgubi/texmacs-skill>. Last update: 2026-11-09.

## Keeping this skill up to date

This skill is meant to be installed as a git clone (usually
`~/.claude/skills/texmacs`). Before working on TeXmacs documents:

- **Update it:** run `git -C <skill dir> pull --ff-only` (if SSH to GitHub
  fails, pull from `https://github.com/mgubi/texmacs-skill.git main`). If the
  clone has local changes or commits that are not pushed, tell the user
  instead of pulling over them.
- **Contribute back:** when something new about TeXmacs is learnt, add it
  here (usually to "Pitfalls", or fix a script), commit it in the clone and
  push it to GitHub (or open a pull request if you cannot push), so every
  installation gets it. Project-specific material stays in the project.

## The file format

- A `.tm` file is a serialised tree: `<tag|arg1|arg2>` inline,
  `<\tag>…</tag>` (with `<|tag>` between arguments) for block arguments,
  paragraphs are separated by blank lines, indentation is layout only.
  Inside strings `\<alpha\>` is a symbol, `<less>`/`<gtr>` are `<`/`>`, `\|`
  is a literal bar, `<#89AB…>` is hexadecimal raw data (embedded images).
- **Encoding: strings are Cork (T1) encoded, not UTF‑8.** Accented Latin
  letters mostly coincide with Latin‑1 bytes (é = 0xE9, à = 0xE0, ö = 0xF6),
  but e.g. en dash = 0x15, em dash = 0x16, § = 0x9F; any other Unicode
  character is written `<#XXXX>` (hex code point). Do not write `<#XX>` yourself as a
  standalone token: it is read as raw data (see "Writing style packages").
  Consequences: never edit a .tm with UTF‑8 tools (the Edit/Write tools
  refuse or corrupt it). Read/write with Python `encoding='latin-1',
  newline=''`, or better go through the stree route below and let TeXmacs
  write the file.
- **Writing a `.tm` file by hand: copy this skeleton exactly.** The
  top-level items are separated by *blank lines*; without them TeXmacs keeps
  only the `<TeXmacs|…>` header and silently drops everything else (the
  stree dump is `(document (TeXmacs "2.1.5"))`, the PDF is empty, and there
  is no error):

  ```
  <TeXmacs|2.1.5>

  <style|<tuple|article|british>>

  <\body>
    First paragraph with <math|x<rsup|2>>.

    Second paragraph.
  </body>

  <\initial>
    <\collection>
      <associate|font|TeX Gyre Pagella>
    </collection>
  </initial>
  ```

  Inside `<\body>` paragraphs (and the blocks of any `<\tag>…</tag>`) are
  also separated by blank lines; a single newline continues the same
  paragraph. Close every block tag on its own line, escape symbols as
  `\<alpha\>` and literal `<`, `>`, `|` in text as `<less>`, `<gtr>`, `\|`,
  and keep the file Cork/Latin-1 (write it with Python, not `printf` or the
  Write tool, as soon as it holds a non-ASCII character).
- **Prefer generating over hand-writing.** For anything beyond a few lines,
  build the stree in Python (`scripts/latex2tm/stree.py`) and let TeXmacs
  serialise it (`tm-undump` in `dump.scm`); or write the fragment, `tm-dump`
  it and splice the tree. When writing by hand, **check the result before
  using it**: `tm-dump` it and confirm that the body has the expected number
  of paragraphs, or typeset it and confirm that the PDF text is non-empty
  and complete (`mutool draw -F txt`). An empty or short PDF, or a dump
  with one huge node, means a formatting error, not a TeXmacs bug.
- Big files: talks embed images as raw data (10+ MB). Strip `<#…>` runs
  before reading: `re.sub(r'<#[0-9A-F]{200,}>', '<#HEX>', s)`.

## Running TeXmacs headless

Binary (macOS): `/Applications/TeXmacs.app/Contents/MacOS/TeXmacs`; on Linux
`texmacs`. Tested with 2.1.4 and 2.1.5. `scripts/latex2tm/run.sh` holds the
path; adjust it there.

- Convert: `TeXmacs -headless -c in.tex out.tm -q` (LaTeX import),
  `-c in.tm out.pdf -q` (PDF of the current buffer).
- Scheme: `TeXmacs -headless -x "(begin (load \"/abs/dump.scm\") … (quit-TeXmacs))"`.
  **Always wrap the body in `(catch #t (lambda () …) (lambda args (display args)))`
  and end with `(quit-TeXmacs)`**: an error otherwise leaves the process
  hanging forever. Run it in the background and poll its PID (see
  `scripts/latex2tm/run.sh`); kill only that PID — never `pkill TeXmacs` (the user may
  have TeXmacs open).
- Headless runs write TeXmacs' own state under `~/.TeXmacs/system`; that is
  normal.

### Scheme API that works headless (`scripts/latex2tm/dump.scm`)

- `(tree-import (string->url f) "texmacs")` / `"latex"`, and
  `(tree-export t (string->url f) "texmacs")`: file ↔ tree without a buffer.
- `(tree->stree t)` / `(stree->tree s)`: s‑expressions. Write them with
  `(call-with-output-file f (lambda (p) (write s p)))` — `with-output-to-file`
  does not redirect in TeXmacs' Guile. Guile writes control characters as
  `\xHH` escapes (handled by `scripts/latex2tm/stree.py`).
- Typesetting: `(load-buffer u) (switch-to-buffer u)
  (export-buffer-main u (string->url pdf) "pdf" (list))` — the PDF export is
  what typesets. `(update-document "all")` does nothing headless (it is a
  *delayed* idle command); call `(generate-all-aux) (update-current-buffer)`
  directly to fill the table of contents / bibliography, export again, then
  `(buffer-pretend-modified u) (buffer-save u)` to store `<\references>`.
  A fresh file needs **two typesetting runs, in separate processes, each with
  a real PDF export** before all references resolve (`scripts/latex2tm/typeset.sh`).
  **Always export with `(list :overwrite)` as the options**: headless,
  `export-buffer-main` otherwise asks for confirmation to replace an existing
  file, nobody answers, and the export is silently skipped (mgubi/texmacs#807).
  `tm-typeset` and `tm-html` in `dump.scm` do this.
- Presentations (`screens`) export only the current screen. For a visual check
  build a preview copy with the screens flattened into pages separated by
  `new-page*` (`scripts/latex2tm/preview_slides.py`); deliver the screens version.
- Check output with `mutool draw -r 60 -o p%d.png file.pdf` and
  `magick montage … -tile 4x1 -geometry +4+4`; text with
  `mutool draw -F txt -o - file.pdf` (count `?` for unresolved references).

### HTML export

Do the HTML customisation **inside TeXmacs**: style packages (or a plugin)
set the exporter's variables and give `tmhtml-` renderings of macros; a
website is built by exporting a directory (`tmweb-convert-dir`) with
`TEXMACS_HOME_PATH` pointing at the site's plugin folder and
`(style-clear-cache)`. Do not post-process the generated HTML with scripts.

**Collect the generic fixes in one plugin** (below called `max-html`, linked
as `~/.TeXmacs/plugins/max-html`), and keep document-specific settings in the
document's package. Such a plugin holds:
- `progs/max-html/fixes.scm`, loaded at startup, fixes the MathJax export.
  Labels inside formulas get anchors (#617), `\ring` is written
  `\mathring` (#607) and `equations-base` is written `aligned` (#611). It
  replaces the binding of `tmhtml-mathjax-formula*` inside
  `(convert html tmhtml)` (`module-variable` + `variable-set!`; internal
  helpers like `cork->html` via `module-ref`) and extends `latex-mathjax`
  with `tm-define … (former x)`.
- The package `max-html` (articles) gives framed theorems, list labels and
  the contents side panel `div.max-toc`. The package `max-html-slides` gives
  the slide viewer and `tmhtml-mytitle`/`myframed`/`myframed-2`.
- `resources/` holds `max-html.css/js` and `max-html-slides.css/js`, to copy
  next to the pages. Document packages `<use-package|max-html>` and assign
  the whole `html-extra-css` tuple again (plugin file first): `merge` does
  not work, because the exporter reads the variable unevaluated. Fonts are
  CSS variables (`--max-text-font`, `--max-slide-font`).
- Generic fixes for HTML export go into the plugin. Document-specific
  things (fonts, favicon, talk macros) go into the document's package.

- Export: `(tm-html in out mathjax?)` in `scripts/latex2tm/dump.scm`
  (preferences `texmacs->html:mathjax|css|images`, then
  `(export-buffer-main u (string->url "x.html") "html" (list))`). Export the
  typeset .tm (stored `<\references>` give the numbers). `doc.tm#label`
  links become `doc.html#label`; images become `<base>-N.png` next to the
  page; MathJax 3 comes from jsdelivr.
- Style variables read by the exporter (set them in a style package):
  `html-css` (replaces the default inline css), `html-extra-css` (tuple of
  extra stylesheets, default css kept), `html-extra-javascript-src` (tuple,
  deferred), `html-extra-javascript`, `html-head-javascript(-src)`,
  `html-head-favicon`, `html-title`, `html-doc-title`, `html-site-version`.
- **HTML renderings of macros: define `tmhtml-NAME` next to `NAME`.** The
  exporter uses it instead of `NAME`. Markup helpers for it:
  `html-div-class|class|body` (block), `html-class|class|body` (inline span),
  `html-style`, `html-div-style`, `html-attr`, `html-tag`, `html-javascript`.
  This only works for macros defined in a **style package**: macros assigned
  in the document's `hide-preamble` are expanded before export and their
  `tmhtml-` variants are ignored. So put presentation macros in a package.
- A package `foo.ts` next to the document is found when the style tuple
  lists `foo`. After editing a package, call `(style-clear-cache)` (TeXmacs
  caches style environments in `~/.TeXmacs/system/cache`), otherwise old
  definitions are used.
- Table of contents (and other generated lists): the entries are written to
  the aux data *already expanded* (`write` evaluates its argument), so
  wrappers around `toc-main-*`/`toc-1…5` disappear and their `tmhtml-`
  variants are never seen. Only the outer `table-of-contents` macro can have
  a `tmhtml-` rendering. Markers that survive expansion and export: `<b>`
  (bold sections), `<with|font-size|…>` → `<font style=…>`, `font-shape` →
  `<i>`/small caps, `color` → `<font color>`; `par-left` indentation is
  lost. Each entry ends with `<a href="#auto-N">page</a>`. Side-panel recipe
  (plugin package `max-html`): `tmhtml-table-of-contents` →
  `div.max-toc` fixed on the left; hide and stretch the page link with
  `.max-toc p a[href^="#auto-"] {position:absolute; inset:0; font-size:0}`
  (select by href: an `eqref` in a title is also a link); mark
  paragraph-level entries by redefining `toc-3…5` with a nested
  `<with|font-size|0.92|…>` and select `p:has(> font)`. Regenerate the TOC
  (two typesetting runs) after changing `toc-*` macros.
- Highlighting the current section in the panel needs JavaScript:
  `max-html.js` (plugin), attached with `html-extra-javascript-src` in
  the package; it maps each entry's `#auto-N` link to the heading with that
  id, marks the last heading above 25% of the viewport (`p.toc-current`, and
  its bold parent `p.toc-current-section`) and scrolls the panel to keep it
  visible.
- Framed theorems (Joris van der Hoeven's web articles, e.g.
  texmacs.org/joris/fftcomp; the model is `styles/article/texmacs/tmarticle.ts`
  in TeXmacs): define `tmhtml-render-theorem` →
  `<html-div-class|theorem|<render-enunciation|…>>` and
  `tmhtml-render-enunciation` with `<html-class|enunciation-name|which>`;
  theorem, proposition, lemma, corollary *and definition* use
  `render-theorem`, while remarks and proofs use `render-remark`. Joris' css
  (texmacs.org/css/theme-dark-colored.css) is `.theorem {border: 1px solid;
  border-left: 1em solid; padding: 0 1em}`; a muted colour and a .5em bar
  also work well (`max-html.css`). This is HTML only;
  the PDF is unchanged.
  Colours (also as in Joris' theme): `h1…h6, strong, b, dt,
  .enunciation-name` in a muted dark red, MathJax output via
  `mjx-container {color: …}`; reset `b` inside the TOC panel.
- The HTML export turns every `enumerate-alpha|Alpha|roman` into a plain
  `<ol>` (decimal labels). Fix: `tmhtml-enumerate-alpha` →
  `<html-div-class|enum-alpha|<enumerate|…>>` plus
  `.enum-alpha > ol > li::marker {content: "(" counter(list-item, lower-alpha) ") "}`.
- MathJax: the converter writes the ring accent `<abovering>` as `\ring{…}`
  (LaTeX package accents), which MathJax lacks (mgubi/texmacs#607).
  Fixed by the plugin. A page-level alternative is an inline MathJax
  configuration in `html-extra-javascript` (it runs before the MathJax
  `<script>`): `window.MathJax = {tex: {macros: {ring: [String.fromCharCode(92)
  + 'mathring{#1}', 1]}}}`.
- MathJax: `aligned` inside an `equation` is pre-expanded by the HTML
  exporter to `equations-base` and reaches MathJax as
  `\begin{equationsbase}` (mgubi/texmacs#611). Fixed by the plugin; the page-level
  alternative is `environments: {equationsbase: […aligned…]}` in that configuration.
- **Check all formulas of an export** with `scripts/mathjax-check/`:
  `npm install mathjax-full@3.2.2` in a scratch `deps/` folder, then
  `python3 extract.py HTMLDIR formulas.json` (uses an HTML parser: raw `<` in
  `\(t < \infty\)` is text, as in browsers) and
  `node check.js deps/node_modules formulas.json`. It renders every formula
  without the `noundefined` package (which in the browser silently shows
  undefined macros in red) and groups the errors. It does not see empty
  formulas (count `\(\displaystyle \)` separately) or dead links: also check
  that every internal `href="…#x"` has a matching `id="x"`.
- Slides: an image with `width=100%` narrowed by a css `max-height` stays at
  the left of its paragraph; centre it with
  `div.toggle img.image {display: block; margin: 0 auto}`.
- Headless Firefox: the dark-mode `content-override` pref in `user.js` did
  not take effect; to check the light theme, screenshot a copy with
  `<html data-theme="light" …>`.
- Negative `vspace` from LaTeX layout hacks (e.g. `\vspace{-2.2em}` before
  a bibliography with an empty heading) exports as a negative margin and
  overlaps text in HTML: drop it (`post_notes.py`, `drop_negspace.py`).
- Headless Firefox `--screenshot` captures from the top of the document
  even when the page is scrolled (hash, `scrollIntoView`): `position:fixed`
  elements then disappear from the capture. Test scroll-dependent behaviour
  by recording state in `DOMContentLoaded` and scrolling back.
- **Exports do not overwrite an existing target file** (PDF and HTML) unless
  the options contain `:overwrite` (see above). Headless Firefox caches CSS in its profile: use a fresh profile
  directory for each visual check.
- `screens` export one `<div class="toggle">` per screen (primitive
  `hidden`/`shown`, no navigation; a hide-preamble yields an empty first
  toggle). A JS file via `html-extra-javascript-src` turns them into a deck.
- Document packages built this way: a notes package does
  `<use-package|max-html>` and sets fonts and its own css; a slides package
  does `<use-package|max-html-slides>` and defines the talk macros
  (`mytitle`, `myframed`…) with their `tmhtml-` renderings.
  `add_style.py` adds a package to a document's style tuple;
  `drop_preamble.py` removes the hide-preamble.
- Visual check: headless Firefox,
  `firefox --headless --profile DIR --window-size=1280,800 --screenshot out.png file:///…html#5`.

## Reading and patching .tm files (scripts/tmread, scripts/tmpatch)

- **Read a document as Markdown, not as PDF text.**
  `scripts/tmread/tm2md.sh doc.tm [out.md|out.tex]` converts a document
  headless, on a scratch copy with a private `TEXMACS_HOME_PATH`.
  - The Markdown keeps theorem and equation numbers and cross-references
    (resolved from the stored `<\references>`), writes every formula as
    LaTeX, and keeps labelled links. It is the best reading copy for an
    agent or a referee, and about 60% of the size of the source.
  - The LaTeX export (`out.tex`) keeps `\label`/`\ref` unresolved.
  - The text of the typeset PDF (`mutool draw -F txt`) mangles inline
    mathematics; use it only to check what was typeset.
  - The Markdown export needs TeXmacs Upsilon, and the script uses its Qt
    port (`TeXmacs Upsilon Qt.app`, searched in `/Applications`,
    `~/Applications` and `~/Downloads`; override with `TEXMACS_HEADLESS`).
    The Cocoa port of Upsilon is not meant to run headless; the Vue app is
    the web build. A few stray lines `bad assign` in the output are
    harmless.
- **Patch a document with `scripts/tmpatch/tmpatch.py`**, never with
  `sed` or a UTF-8 editor. Write the patch in readable UTF-8 with TeXmacs
  markup:

  ```
  @@ replace [count=N]
  <<<
  old text (é, –, ∞ allowed)
  ===
  new text (empty to delete)
  >>>
  ```

  `tmpatch.py doc.tm fix.patch [--dry-run] [--check] [--no-backup]`.
  - **Encoding.** It encodes the text to the file's serialization: Cork
    bytes (é stays 0xE9, but § is 0x9F and Œ 0xD7), a backslash and a letter
    for Cork bytes below 0x20 (en dash = `\U`, em dash = `\V`), and
    `<#XXXX>` for any other character.
  - **Matching.** It matches the old text whitespace-insensitively, since
    TeXmacs rewraps lines, and requires exactly `count` occurrences
    (default 1).
  - **Safety.** All blocks are applied atomically. Nothing is written if a
    body paragraph ends up with unbalanced `<`/`>`, or if block tags
    `<\tag>…</tag>` no longer nest. This is the failure mode in which
    TeXmacs silently drops the rest of the document.
  - **`--check`.** It also imports the patched file with a headless
    TeXmacs (`tm-dump`) and compares the number of top-level body
    paragraphs with the text.
  - **Backup.** It keeps `doc.tm.orig` unless `--no-backup`.
  - **`--show`.** `tmpatch.py --show doc.tm` prints the file decoded to
    UTF-8; `--encode TEXT` shows the serialization of a string.
- Guile's `write` in TeXmacs Upsilon abbreviates lists after 40 elements
  with `...` (mgubi/texmacs#840), so a `tm-dump` made with Upsilon looks like
  a truncated body. Use the standard
  TeXmacs for strees (`tmpatch.py --check` does; override with
  `TEXMACS_CHECK`).

## Restructuring a series of documents (scripts/restructure)

Example: a lecture series (notes and slide decks) was reorganised. Material
moved between documents, a lecture was added, and the later files were
renumbered. The one-off driver scripts stay with the project; the reusable
parts are here (`rwlib.py`, the outline and report scripts). Method:
- **Dump and outline:** dump every document to an stree.
  `outline.py`/`slides_outline.py` list the body paragraphs with their
  index, section and label, and the slides with their titles.
- **Cut and reassemble:** do it at paragraph level, in a driver script
  built on `rwlib.py` (`load`, `dump`, `visit`, `body`). Keep `section-nr`
  so that numbering continues across documents.
- **References:** afterwards, resolve every `reference`/`eqref` to a label
  that left the document, and every `hlink` to `file.tm#label`, by looking up
  which new document holds the label. Prefer the documents that received
  the rest of the material the label came from. Write them as
  `XREF@kind@doc@label` placeholders and fill them with `fill_xref.py` after
  one round of typesetting, then typeset again.
- **Bibliography:** copy the missing `bibitem*` entries from the other
  documents, and prune what no longer gets cited.
- **Prose:** `report.py`/`report_slides.py` list every "Lecture N" mention,
  including `Lecture<nbsp>N`. `relecture()` takes one explicit new number
  per mention and checks the count. Also grep for abbreviations such as
  "(L3)" and for hard-coded numbers on slides: exercise lists, "§9.2",
  "notes: §§…".
- **Checks:**
  - an undefined-tag check, then typeset twice;
  - count `??` and leftover `XREF` in the PDF text;
  - compare section and exercise numbers with what the slides quote;
  - for HTML, the link, anchor and MathJax checks.
- **Before installing:** check that the user hasn't edited the sources since
  they were copied, and save the old state in a dated folder in the Trash.
- **Slide fit:** beamer has no vertical alignment, so content sits at the
  top of the 8:5 page, and a small base font leaves an empty band below.
  - **Finding overflow:** to choose a larger `font-base-size`,
    `mark.py` puts an invisible `SLIDEMARK<n>` in each title. Then flatten
    the deck (`preview_slides.py`), typeset, and run `overflow3.py`: a page
    without a marker is an overflow, unless the next slide is a title or
    section slide.
  - **Choosing the size:** in one series of decks 10pt fitted all slides
    but ten. `bigger_font.py` sets the size and wraps the body of the listed
    slides in `<with|font-size|0.9|…>`.
  - **Checking the result:** recheck until pages equal slides. The
    detector can blame the slide after an overflow when that slide is a
    section slide, so look at the pages.
  - **Writing new slides:** write them natively, without fixed `vspace`
    or empty paragraphs, and with enough content; the talk's slides came
    with fixed gaps.
- **Pitfalls:**
  - `stree.walk` is functional: it rebuilds every node, so in-place edits
    made inside its callback are lost. Use `rwlib.visit` for in-place
    edits, and `walk` only when you keep its return value.
  - zsh does not split `$VAR` into words: list file names explicitly in
    commands.
  - A math formula inside a `paragraph` heading is dropped from the table
    of contents, so keep the heading plain text.
  - When writing new material as a `.tm` fragment (then `tm-dump` and
    splice in), write symbols as `\<mathd\>`,
    `\<mathe\>`, `\<alpha\>`. `<mathd>` without backslashes is an
    unknown macro and shows up in pink. Save the file as Latin-1/Cork,
    not UTF-8: the Write tool writes UTF-8, so `ô` came out as `Ã´`.
    Convert with `open(...,encoding='latin-1')`.
  - Lecture and section numbers inside TikZ pictures are compiled into the
    stored EPS. Edit the code of the `script-output` block and regenerate
    its image with `latex` and `dvips` (see the TikZ pitfall below).
  - Select a node by its label or content, never "the first `big-table`":
    a document can have several.
  - After a restructuring, have an independent reviewer read the PDFs. It
    found stale numbers in figures, prose left in the wrong lecture, and an
    item dropped by an off-by-one in a list edit.

## Native markup (what a hand-made TeXmacs document uses)

- Style: `<style|<tuple|article|number-long-article|british>>`
  (`number-long-article` = numbers prefixed by the section, reset per section,
  like LaTeX `\numberwithin`). Section offsets: `<assign|section-nr|10>`.
- Title: `<doc-data|<doc-title|…>|<doc-subtitle|…>|<doc-author|<author-data|<author-name|…>|<author-affiliation|…>>>|<doc-date|…>>`,
  `<abstract-data|<\abstract>…</abstract>>`, `<\table-of-contents|toc>…`.
- Theorems: `<\theorem>`, `proposition`, `lemma`, `corollary`, `definition`,
  `remark`, `exercise` (starred = unnumbered); an optional title is
  `<dueto|Title>` at the start of the body. Proof: `<\proof>`; a custom proof
  heading: `<\render-proof|Proof of Theorem 3>…`.
- Equations: `<\equation>…<label|eq:x>…`, `<\equation*>`, `<\align*>`;
  references `<reference|x>`, `<eqref|x>`; a link to a label in another
  document: `<hlink|11.2|other_doc.tm#prop:x>`.
- Lists: `itemize`, `enumerate`, `enumerate-alpha`, `enumerate-roman`,
  `enumerate-Alpha`, `description`, `description-long` (label on its own line).
- Bibliography without BibTeX: `<section*|References>` then
  `<\bib-list|LONGESTKEY>` with items `<bibitem*|KEY><label|bib-KEY>text`;
  `<cite|KEY>` then resolves.
- Figures: `<big-figure|<image|…>|caption>`; embed images as
  `<image|<tuple|<#hex>|name.png>|0.8par|||>` (stree:
  `(image (tuple (raw-data BYTES) "name.png") "0.8par" "" "" "")`). PNG, PDF
  and EPS all work.
- TikZ through the TikZ plugin (keeps the source editable and re-runnable):
  `<script-output|tikz|default|<document|\documentclass[tikz]{standalone}|…|\end{document}>|<image|<tuple|<#eps-hex>|ps>||||>>`.
  The plugin runs `latex` + `dvips` on the input (wrapping it in
  `\documentclass[tikz]{standalone}` unless it already starts with
  `\documentclass`), so generate the stored output the same way.
- Math symbols: `<leqslant>`, `<geqslant>` for inequalities (never `<leq>`, `<geq>`, `<le>`, `<ge>`); `<mathd>`, `<mathe>`, `<mathi>` for upright d, e, i, and `<mathD>` for an upright derivative operator D;
  `<math-up|Tr>` for operator names; `<big|int>`, `<big|iint>`, `<big|sum>`;
  `<around*|(|…|)>` for `\left(…\right)`; `<wide|x|^>` accents.

## A presentation setup that works

A hand-made beamer talk, used as the reference style for converted decks:
- `<style|<tuple|beamer|fira-font|british|triangle-list>>`.
- A `<\hide-preamble>` defining `mytitle` (dark-red bold title with a left
  rule), `myframed` (top/bottom rules), `myframed-2` (box), `mynote`,
  `hand`, `triang`, `mydot`, and the math font assignment (TeX Gyre Pagella).
- Body: `<screens|<\shown>…</shown>|<\hidden>…</hidden>|…>`; each slide starts
  `<mytitle|lower-case title>`, blank lines between blocks; notes in
  `<small|<with|color|dark grey|…>>`; emphasis `<strong|…>` (strong colour
  dark red).
- `<initial>`: bg-color #f2f2f2, color darker grey, font-base-size 9,
  math-color #620000, page-medium beamer, page-type 8:5, par-mode justify,
  strong-color dark red, item-1 ▸.
- Extract preamble/style/initial programmatically from the reference talk
  (`scripts/latex2tm/post_slides.py` reads them from its stree dump
  `talk_style.scm`). For a series of decks, move the preamble macros into a
  package (with their HTML renderings), drop the preamble from the documents
  and end the style tuple with that package (`TM_SLIDES_PACKAGE`).

## LaTeX → native TeXmacs (scripts/latex2tm)

The built-in LaTeX import is only a first pass for the math. The pipeline:
1. `prep.py` (LaTeX → LaTeX): expand the document's own macros (the importer keeps
   them as user macros and drops arguments of `\DeclarePairedDelimiter`
   ones), resolve `\cref` with the `.aux` cleveref data (`Lemma~\ref{x}`;
   external xr labels become placeholders `XREF@kind@doc@label`), turn
   tikzpictures into `\tmtikz{name}` + standalone sources, optional
   environment titles into `\tmdueto{…}`/`\tmproofof{…}`, list options into
   `\tmlist{alpha|roman|long}`, remove minipages, tabularx, `\fint`,
   `\eqqcolon`.
2. TeXmacs import → `.tm` → stree dump.
3. `post_notes.py`: native rewrite (style, doc-data/subtitle, dueto,
   render-proof, bib-list, embedded images, TikZ plugin blocks, list styles,
   dashes, `<mathd>`…). Optional environment: `TM_STYLE_PACKAGES` (packages
   appended to the style tuple) and `TM_DOC_TITLE` (a common title for a
   series; the imported one becomes the subtitle). It also sets a house page
   layout (Pagella, 11pt, A4): change `restyle` for another one.
4. `typeset.sh` (stree → .tm, two typesetting passes) and `fill_xref.py`
   (fill links to other documents from the targets' computed references),
   then typeset again.
For beamer: `prep_slides.py` turns frames/sections/blocks/columns/`\refs`
into marker paragraphs, then `prep.py`, import, `post_notes.py`, and
`post_slides.py` assembles the screens in the reference talk style (title
slide text from `TM_TALK_TITLE`, `TM_TALK_AUTHOR`, `TM_TALK_FOOTER`).
Copy `scripts/latex2tm/` to a scratch directory and run there (the scripts
use relative `src/ prep/ out/ sout/ slides/` folders; see the driver
scripts `build_note.sh BASE`, `build_all_notes.sh BASE…`,
`build_slides.sh BASE N`).

## Writing style packages and documents by hand

A pattern that worked for a house style (letters, invoices, slips,
envelopes, cards): generate the package from Python (small helpers for
tables, column widths, rows, coloured bars and letter tracking; logos
embedded as raw data), generate the documents the same way, and typeset them
with a script.

- Do not copy or link a package into `~/.TeXmacs/packages/`. Prefer a
  **plugin folder inside the project**, symlinked as
  `~/.TeXmacs/plugins/NAME`.
  Plugin layout (all found through `plugin_path`, `init_texmacs.cpp`):
  `packages/NAME.ts`, `misc/patterns/` (page backgrounds), `doc/NAME.en.tm`
  + `doc/NAME-abstract.en.tm` (both needed: then *Help > Plug-ins > NAME*;
  check headless with `(url-exists-in-help? "NAME.en.tm")`), `progs/init-NAME.scm`
  with `(plugin-configure NAME (:require #t))`, and `templates/` (linked
  from the help page with relative `hlink`s). Fonts cannot be loaded from a
  plugin: ship them with an install script that copies to
  `~/.TeXmacs/fonts/truetype` and runs `(font-database-build-local)`.
  Without a plugin, a package is
  also found next to the document or by a relative path in the style tuple
  (`<tuple|generic|Stationery/pkg>`). `(style-clear-cache)` before each test run.
- Help pages opened from the Help menu are expanded into a
  `tmfs://help/article/…` buffer: **relative links in them do not resolve**.
  Link to plugin files with `<action|text|(cmd …)>` calling a `tm-define`
  with `(:secure #t)` (no confirmation) from `progs/init-NAME.scm`. To start
  an untitled copy of a template: `(new-document)` then
  `(buffer-set (current-buffer) (tree->stree (tree-import u "texmacs")))`
  (a `NAME-new` command in the plugin). `url-unix` takes two arguments.
- Help pages use `<style|tmdoc>`: `tmdoc-title`, `<\explain>`
  `<explain-macro|tag|arg…>` `<|explain>` text `</explain>`, `markup`,
  `src-var`, `src-arg`, `menu`, `tmdoc-copyright`; initial `preamble|false`.
- **tformat arguments are separate**: `<tformat|<twith|…>|<cwith|…>|…|<table|…>>`.
  Concatenating them (`<twith…><cwith…>`) makes one argument and every
  setting is silently ignored (tables collapse to text in one line).
- Fixed columns: `cell-width` + `cell-hmode|exact` per column,
  `table-width` + `table-hmode|exact`; multi-line cells need
  `cell-hyphen|t` (then `<new-line>` works inside the cell).
- **Table borders have no colour property** (`cell-border-color` does not
  exist): they take the text colour around the *outermost* table. Wrap the
  table in `<with|color|RULE|…>` and re-colour each cell's content; for a
  coloured rule inside a nested table, draw a bar instead: a 1×1 table with
  `cell-background`, `cell-width/height` + `cell-hmode/vmode|exact`.
- **Paragraph-level properties only act on whole paragraphs**: inline
  `<with|par-mode|center|x>` or `<with|par-left|…|x>` inside a line is
  ignored; use the block form `<\with|par-mode|center>…</with>`.
- **`<vspace*|…><arg|body>` makes the block body inline** (a concat): no
  line breaking, paragraphs run off the page. Use
  `<surround|<vspace*|…>||<arg|body>>`.
- `<\macro|a|body>` with several lines = block macro; an empty first line
  (e.g. one holding only `<assign|…>`s) costs a line of height (on small
  pages it pushes content onto a new page): put such assignments at the
  start of the first real line.
- Page layout from a package: `<assign|page-top|…>` etc. work. Headers and
  footers must be quoted so they are evaluated per page:
  `<assign|page-odd-header|<quote|<my-header>>>`; `<page-the-page>` inside.
  First page different: assign `page-this-header` / `page-this-footer`
  (unquoted empty, or `<quote|…>`) from a macro used on page 1.
  Negative `vspace*` at the top of a page is ignored: to have a high
  masthead, keep `page-top` small and `page-head-sep` small.
- Custom page sizes: `page-type|user`, `page-width`, `page-height` in the
  document's `<initial>`.
- Absolute decoration (watermark bleeding off the page): a zero-size moved
  box in the first-page footer, `<resize|<move|IMG|dx|dy>|0mm|0mm|0mm|0mm>`
  (resize outside move; the other order keeps the width and shifts the line).
  Opacity: pre-fade the SVG (`<g opacity="0.08">`) and convert with
  `rsvg-convert -f pdf`; PDF images keep their transparency.
  But headers/footers are drawn *above* the text (mgubi/texmacs#609), so
  this hides text (on screen even a transparent image looks opaque).
  **Use a page background instead**: `<assign|page-this-bg-color|<pattern|FILE|100%|100%>>`
  (or `bg-color` for all pages) with FILE a full-page image (same size as the
  page, transparent except the decoration, e.g. an SVG with a nested `<svg x y
  width height>`). Make it **opaque**: preferably a vector PDF with no transparency at all
  (white `<rect>` behind, colours/gradient stops mixed with white instead of
  `opacity`, generated by a script), or an opaque PNG
  (`rsvg-convert -f png -d 300 -p 300 -b white`): a transparent pattern
  shows a checkerboard over the whole page on screen and translucent parts
  too dark, for PDF and PNG alike (mgubi/texmacs#616: `clear_pattern` does not
  clear before drawing). It is drawn before the text. The
  pattern must be a file (no raw data). Lookup (`resolve_pattern`, brush.cpp;
  verified headless): first `$TEXMACS_PATTERN_PATH` and its subfolders =
  `~/.TeXmacs/misc/patterns`, `$TEXMACS_PATH/misc/patterns|pictures` and
  `misc/patterns` of every plugin (`~/.TeXmacs/plugins/*/misc/patterns`, …),
  then relative to the document. So a plugin folder (`packages/` +
  `misc/patterns/`) makes a style and its backgrounds global; if the user
  wants things local, keep the folder in a variable that documents elsewhere
  override in `<initial>`.
- No letter-spacing property: track capitals by inserting `<hspace|0.14fn>`
  between letters (generate it).
- `<#B7>` written as a separate token is **raw data**, not U+00B7 (it eats
  the following text). `·` serialises as `<centerdot>`, which text fonts do
  not render (red "(centerdot)"). Use a raised full stop
  `<move|.|0fn|0.32fn>`. £ is the Cork byte 0xBF; check any other
  character with `(utf8->cork "…")` headless.
  Another way: import a one-line LaTeX file with the accent macro
  (`tree-import` from "latex", then `tree-export` to "texmacs") and read the
  byte TeXmacs writes. For example `\H{o}` (ő) is the Cork byte 0xAE, so
  "Lőrinczi" is `L\xaerinczi` in a Latin-1 Python string.
- Placeholders for empty arguments: `<macro|x|default|<if|<hc-blank|<arg|x>>|<arg|x><with|color|grey|<arg|default>>|<arg|x>>>`
  with `hc-blank` = `<or|<equal|<arg|x>|>|<equal|<arg|x>|<document|>>>`.
  Keep `<arg|x>` rendered in the empty branch too (else the cursor cannot
  enter the argument), and never write `<arg|x><if|…>`. Even so, wrapping a
  **multi-paragraph** argument in such an inline macro loses its paragraph
  spacing and `vspace*`: use it only for in-paragraph arguments; put a
  placeholder paragraph in the template instead.
- Several TeXmacs processes sharing `~/.TeXmacs` (other sessions' test
  suites) delete each other's `system/tmp/<pid>`: PDF export then fails
  ("failed to include image file", truncated PDF). Run headless jobs with a
  private `TEXMACS_HOME_PATH` whose `fonts`, `plugins`, `packages`, `styles`
  are symlinks to the real home.
- In macros, test empty arguments/values with
  `<if|<unequal|<arg|x>|>|…>` (works for args and `<value|…>`).
- Edit .tm/.ts files with Python (`latin-1`, `newline=''`), not sed: BSD
  sed fails with "illegal byte sequence" on Cork bytes.
- The user may open and edit the test files in TeXmacs while you work
  (e.g. moving a note or reducing `page-top`): re-read a file before
  regenerating it, take their edits as design feedback, and do not
  overwrite their copy.

### Fonts

- TeXmacs uses fonts from `~/.TeXmacs/fonts/truetype/`; after copying,
  rebuild the database headless: `run.sh '(font-database-build-local)'`
  (≈1 min). Check `~/.TeXmacs/fonts/font-database.scm`. Deleting a font
  file leaves a stale entry there; remove it by hand.
- Variable fonts (Google Fonts `Family[wght].ttf`): make static cuts with
  `fontTools.varLib.instancer.instantiateVariableFont(f, {"wght": w})`,
  remove name IDs 16/17, set IDs 1/2/4/6, `usWeightClass`, `fsSelection`
  and `macStyle`. TeXmacs knows regular/bold/italic per family: map the
  semibold cut to "Bold" if that is the design weight.
- TeXmacs strips weight words ("Medium", "Light"…) from family names, so a
  "Jost Medium" family merges into "Jost": give an extra weight a neutral
  family name ("Jost Label") and select it with `<with|font|Jost Label|…>`.
- "missing 'X' master" in the log is harmless (substitution lookup);
  confirm the embedded fonts with `mutool info -F file.pdf`.

## Conventions (mandatory)

These rules are **mandatory for every TeXmacs document** written, converted or
edited with this skill. They are not defaults to be overridden: they keep the
markup semantic (TeXmacs knows the extent of every bracket and the role of
every symbol) and the typography consistent. Check them before delivering:
`scan.py`, `around_pairs.py` and `nbsp.py -n` on the stree dump, a grep for
`\<leq\>`/`\<geq\>` and for bare `d*`/`D*` in maths, and a look at the
rendered pages.

- **Inequalities: always `\<leqslant\>` and `\<geqslant\>`** (stree `<leqslant>`, `<geqslant>`), never `\<leq\>`, `\<geq\>`, `\<le\>` or `\<ge\>`. The LaTeX importer produces `<leq>`/`<geq>`; `post_notes.py` converts them, but hand-written markup and generators must emit the slanted forms directly. Check with a grep before delivering, skipping embedded image data.

- **Differentials and derivative operators are upright symbols, not
  letters.** The integration differential is `\<mathd\>x`
  (`<big|int>f<around|(|x|)>*\<mathd\>x`, `\<mathd\>t`, `\<mathd\>s`,
  `<frac|\<mathd\>|\<mathd\>t>`), never `d*x`: a plain `d` is an italic
  variable. Likewise a derivative operator written D (Fréchet or
  Malliavin derivative, `DF<around|(|\<varphi\>|)><around|[|h|]>`,
  `D<rsup|2>V`) is `\<mathD\>`, never the letter `D`. TeXmacs adds the
  thin space before `\<mathd\>` itself: do not insert `<space|…>`.
  Stochastic differentials follow the same rule (`\<mathd\>B<rsub|t>`,
  `\<mathd\>W`). Leave `d` and `D` alone where they are genuine
  variables, dimensions or names (`d` = space dimension, a matrix `D`).
  The LaTeX importer turns `\,\mathrm{d}x` into
  `<space|0.17em><math-up|d>x` and `\mathrm{D}` into `<math-up|D>`;
  `post_notes.py` rewrites these as `\<mathd\>`/`\<mathD\>` and drops
  the space. A bare `dx` or `DF` stays `d*x`, `D*F`: check integrals,
  derivatives and stochastic differentials by hand, and look at the
  rendered page.
- **Non-breaking spaces.** Put `<nbsp>` (never a plain space) between text and
  a citation or cross-reference, and in numbered names:
  `Bauerschmidt and Bodineau<nbsp><cite|BB19>`, `by<nbsp><eqref|eq:x>`,
  `Theorem<nbsp><reference|thm:x>`, `Lecture<nbsp>3`, `Section<nbsp>8`,
  `Lectures<nbsp>1\U3`, `Part<nbsp>I`, `Step<nbsp>2`. This covers `cite`,
  `reference`, `eqref`, `pageref` and numbered `hlink`s to other documents.
  Write new text this way. To retrofit a document, run
  `scripts/restructure/nbsp.py [-n] file.scm ...` on the stree dump
  (`-n` = dry run with counts). It never touches maths, labels or links.
- **Paragraph titles** have no final full stop (see the style rule below).
- **Every bracket pair in maths is an `around`**: parentheses, square
  brackets, braces, angle brackets, absolute values and norms. Write
  `<around|(|…|)>`, `<around|[|…|]>`, `<around|\<langle\>|a,b|\<rangle\>>`,
  `<around|\||x|\|>`, `<around|\<\|\|\>|u|\<\|\|\>><rsup|2>`, never bare
  `(`…`)` or `\<\|\|\>`…`\<\|\|\>` in a math string. TeXmacs uses the
  `around` to know the extent of the bracket (sizing, selection, editing,
  semantics), so **the body must be exactly what is between the two
  delimiters**: exponents and subscripts go after the `around`
  (`<around|(|…|)><rsup|-1>`), and two separate brackets are two separate
  `around`s. Wrong extents seen (left by the LaTeX importer or hand edits):
  `<around|\<\|\|\>|a+b*<around|\<\|\|\>|<rsup|2>-<tfrac|1|2>|\<\|\|\>>*u|\<\|\|\>>`
  for `‖a+b‖²−½‖u‖²`, and a set
  `{… : …}` split into `<around*|{|…|<nobracket>>` + `<around*|<nobracket>|…|}>`.
  `around` = normal size (what typing `(` gives); `around*` = stretching,
  like `\left…\right` (use it when the body holds `frac`, big operators…).
  Mixed pairs are fine (`<around|[|0,\<infty\>|)>`), as is
  `<around*|.|…|\|>` for an evaluation bar. A conditional bar inside a
  bracket (`\<bbb-E\>[X\|\<cal-F\>]`, `Ent(\<nu\>\|\<mu\>)`) stays a plain
  `\|` (or `<mid|\|>`) inside the `around` body.
  Check and fix on the stree dump: `scripts/restructure/scan.py doc.scm [x]`
  counts the arounds and lists the bare delimiters left in maths;
  `scripts/restructure/fixaround.py in.scm out.scm` wraps every pair that
  matches inside one concat into `around`/`around*`, and reports unmatched
  delimiters and `SUSPICIOUS` arounds (body starting with `rsup`/`rsub` or
  ending with an operator). Fix those by hand, then look at the arounds
  whose body has a top-level `=` or `\<leqslant\>`: they are often too wide.
  Full pipeline (used on a whole lecture series), on the stree dump:
  1. `fixaround.py a.scm b.scm`: wrap bare `(…)`, `[…]`, `⟨…⟩`, `‖…‖`.
  2. `around_pairs.py b.scm`: list arounds with impossible delimiter pairs
     (importer debris such as `<around|)||)>`, `<around|\||…|]>`,
     `<around*|[||(>`); bra/ket pairs `|Ω⟩`, `⟨Ω|` are legitimate.
  3. `rebracket.py b.scm c.scm`: in every concat containing such a pair or
     a SUSPICIOUS around, flatten all its arounds back to delimiter tokens
     and pair them again (keeps `around*` when either delimiter came from
     one; a lone `|` met before a closer becomes a middle bar). Check its
     log line by line, and fix the bar type by hand where the import lost
     it (e.g. an L² norm imported as `|…|`).
  4. `fixaround.py c.scm d.scm` again, then `bars.py d.scm e.scm`: pair bare
     `|` bars (absolute values, very common in imported notes). At each level an even number of bars is paired in order;
     one bar inside a bracket is a conditioning bar and is kept; one bar
     followed by a subscript is an evaluation/restriction bar and becomes
     `<around*|.|…|\|><rsub|…>` from the last `=` on; the rest is logged as
     ODD/REVIEW. Review the `PAIRED4+` lines (four or more bars at one level).
  5. Re-run `scan.py`: what is left should be conditioning bars only.

## Pitfalls seen so far

- **Table formats are separate `tformat` arguments.** Write
  `<tformat|<twith|…>|<cwith|…>|<table|…>>` with a `|` between every
  `twith`/`cwith`; written back to back (`<cwith|…><cwith|…>`) they form one
  concatenation argument and are silently ignored. For a table of page width
  whose last column wraps: `<twith|table-width|1par>|<twith|table-hmode|exact>|
  <cwith|1|-1|3|3|cell-hyphen|t>|<cwith|1|-1|3|3|cell-hpart|1>`, plus
  `cell-width`/`cell-hmode|exact` for another wrapping column.

- The 2.1.4 LaTeX importer numbered the `\notag`/`\nonumber` rows of
  `align` environments (82 extra numbers in 66 blocks of one imported
  manuscript), so equation numbers drift from the source and "the second
  equation in (x)" can point to the wrong row. After importing, compare the
  `<eq-number>` count of each `align` with the source's numbered rows and
  drop the numbers of `\notag` rows (check that every label sits on a row
  that keeps its number).
- Deleting a label does not remove its `<associate|…>` entry from the
  `<\references>` block on the next typeset; delete stale entries by hand.
- A bracket that spans two rows of an `align` cannot be one `around`: use
  `<around*|[|…|<nobracket>>` in one cell and `<around*|<nobracket>|…|]>`
  in the next (`around_pairs.py` accepts these half pairs).
- `post_notes.py` keeps the imported title and the plain article style
  unless `TM_DOC_TITLE` / `TM_STYLE_PACKAGES` are set. The LaTeX importer may also
  split a bibliography item into several document children; group each item
  into one paragraph with `bibitem*` and its `bib-KEY` label before typesetting.
  Check multi-key citations against the source: the 2.1.4 importer dropped
  the last key of `\\cite{K,C,L}` and of a six-key citation.
- In this layout, restructuring helpers import `stree.py` from
  the sibling `scripts/latex2tm/` directory. `rwlib.py` uses that relative
  location so the scripts work without a custom `PYTHONPATH`.

- Marker macro arguments containing `_` are imported as subscripts: keep
  marker arguments free of `_` (encode file names with `-`).
- `\left\lvert … \right\rvert`, `\lVert` → red `<left-lvert-0>`: replace by
  `|` and `\|` before importing.
- `\begin{description}[…]`, `\begin{enumerate}[label=…]`: the option makes
  the importer drop the environment; strip it.
- `\varepsilon*` (macro glued to `*`) becomes an unknown `<varepsilon*>`.
- An unscoped `\large` (e.g. after `\usebeamercolor`) swallows the rest of
  the document into one `with` block.
- `--` in titles, theorem names and abstracts is not converted to a dash.
- Python reading the stree must use `newline=''`, or `\r\n` inside embedded
  PNG data is silently changed and the image breaks.
- A load right after a save in the same process can return stale content;
  use one TeXmacs process per step.
- Beamer leftovers: `\setlength{…}{…}` leaves a stray `}`; `\textstyle`
  inside `aligned` scatters the rows; `&&\text{…}` comment columns overflow
  (use `\qquad`); removing `\small` etc. must leave `{}` or the next control
  word is glued (`\raggedrightTwo`).
- Images inside `wide-tabular` cells: `Xpar` is still the page paragraph
  width, so multiply by the column width (otherwise plots are clipped).
- TikZ output images have natural size; on slides scale them to the
  beamer text width (≈397pt for 16:9) via the EPS bounding box and centre.
- zsh: an unmatched glob (`rm -f shot*.png`) aborts the whole `&&` chain;
  removals with `$VAR` paths are blocked by the safety check — use literal
  absolute paths or `${VAR:?}`.
- `\begin{gathered}` inside `equation` is imported as an undefined
  `<gathered|…>` macro (shown as red text in the PDF, an empty
  `\(\displaystyle \)` in HTML). `eqarrays.py` (called from
  `post_notes.py`) rewrites it as a native `eqnarray*`: lines in the centred
  middle column, `<eq-number>` plus the labels in the last cell of the last
  row. Same equation numbers.
- `aligned` inside `equation` typesets with the number on a line of its own
  below the block; `eqarrays.py` rewrites it as a native `align`, with the
  rows unchanged and any trailing text, `<eq-number>` and the labels at the
  end of the last cell.
- `extern` in macros runs only "secure" Scheme. An inline lambda may use
  only list primitives (`car`, `cons`…; no `tree->stree`, `map` or `let`),
  so it cannot inspect a tree. Real helpers are `tm-define`d with
  `(:secure #t)` in a module, e.g. TeXmacs' own `tmhtml-eqnarray*` →
  `ext-tmhtml-eqnarray*`. `tmhtml-` variants of primitives (e.g. `label`)
  are ignored.
- `\ref`/`\eqref` inside a tikzpicture: the TikZ plugin compiles the
  picture standalone, so `prep.py` substitutes the numbers before writing
  the picture source (otherwise "??" in the figure).
- **Check for undefined tags** after a conversion: `tagcheck.scm`
  (`(tm-tagcheck "/abs/doc.tm")`) lists the tags without a definition in the
  document's style (`style-has?`). Ignore primitives (`concat`, `rsub`,
  `around`, `with`, `table`, `next-line`, `big`, `wide`, `image`, …); anything
  else (e.g. `gathered`) is a conversion error.
- HTML with MathJax: **labels inside equations get no anchor** (the MathJax
  pass `latex-mathjax` drops `label`), so every `eqref` link is dead (a
  quarter of the internal links in one set of notes). Check links after an
  export.
- Known cosmetic gaps of the converter: booktabs rules are dropped and table
  cells are centred.
- **A PDF much shorter than expected = an unclosed tag swallowed the rest.**
  An unclosed inline `<math|…` (or `around*`, `wide`) can be closed by a stray
  `>` far away (e.g. `</proof>>`), turning everything after it into an
  argument that is never typeset: a merged book stopped at p. 115 of 247
  with no error. Detect: dump the stree and look for a huge top-level node,
  or check the last PDF page against the source. Fix both ends.
- Bibliography from the attached database (`<\bibliography|bib|tm-alpha|>`
  with empty file and `bib-bibliography` attachment) is only generated when
  the preference `database tool` is `on` (`supports-db?`); headless,
  `(set-preference "database tool" "on")` before `generate-all-aux`
  (otherwise "Could not load BibTeX file"). Needs three typesetting runs
  (bib-list, then citations). `<\db-entry>` blocks not separated by a blank
  line become one `concat` paragraph and the generator silently skips them.
- Merged documents: rename duplicate labels per part; check
  `<reference|…>`/`eqref` targets exist, "Section" vs "Chapter" after
  promoting the hierarchy, and leftover `<with|color|red|…>` scratch blocks.
  Apply fixes as exact replacements with occurrence counts (a space in the
  pattern should also match a line break).
- LaTeX `\mathscr{F}` is imported as `<with|math-font|cal*|F>`, which does not
  select a different letter under fonts without a script alphabet (Pagella,
  Fira): it silently prints the italic F. Preserve the distinct script
  alphabet with `<with|mode|text|font|cal*|F>` inside math; this selects the
  Ralph Smith font correctly. `post_notes.py` does this now. Do not replace
  script letters indiscriminately by `<cal-F>`: that collapses `\mathscr`
  and `\mathcal`, which may denote different objects. Check the rendered letters, including their subscripts.
- Paragraph titles: write them without the final full stop and set
  `<assign|paragraph-post-sep|<macro|.<sectional-sep>>>` in the style, so
  the TOC (PDF and HTML) shows bare titles while the text keeps the stop.
- Theorem frames on slides: redefine `render-theorem` in the slide style as
  `<myframed-2|<old-render-theorem|which|body>>` (save the old one with
  `<assign|old-render-theorem|<value|render-theorem>>`); the HTML export
  follows through the tmhtml rendering of myframed-2.
- Without `:overwrite`, headless `export-buffer-main` silently keeps an
  existing target, so the second (post-aux) export of a typesetting run and
  every later pass were lost and pass-to-pass comparisons compared one stale
  file (all citations stayed `[?]`). Export with `(list :overwrite)`, as
  `scripts/latex2tm/dump.scm` does; check the PDF timestamp if a build looks
  unchanged.
- TikZ plugin images: run `latex` then plain `dvips -q x.dvi -o x.eps` on the standalone class. `dvips -E` writes a wrong BoundingBox next to the standalone page size and the image comes out blank in TeXmacs (seen 2026-11-01).
- Check figures by rendering the PDF page; a blank EPS gives no typesetting error, only white space above the caption.
- A bare `|` inside a tag argument is an argument separator: a restriction written `<math|f|<rsub|A>>` gives `math` two arguments and the restriction `|_A` silently disappears from the PDF. Write it `<math|<around*|.|f|\|><rsub|A>>` (or `\|` for a literal bar); grep hand-written `.tm` for `|<rsub|`.
- **`tm-typeset` saves the buffer, so typesetting a malformed file destroys it.** One extra `>` in a hand-edited `.tm` made TeXmacs drop the whole body, and the save in `tm-typeset` wrote back only the header, `<initial>` and `<references>` (49 KB → 3.6 KB, no error). Before typesetting an edited file, check that `<` and `>` balance in each top-level paragraph of the body; typeset a copy in a scratch folder and install it only if the PDF is complete. Never chain an edit and a typesetting run with `;`: a failed edit must stop the run. (A stray `>` that only closes the opening of `<\big-table|…>` early is silent too: the table renders, the caption is lost.)
- Conditional expectations: `rebracket.py` can remove the conditioning bar
  when flattening `\left[\left. ... \right| ... \right]`. Prefer
  `\left[ ... \mid ... \right]` in the import source, and check the bar
  in the final native tree and PDF. Likewise, review the norm type when
  a sized double bar imports as a `mid` node.
- `\lhook\joinrel\longrightarrow` can import as undefined `lhook` and
  `joinrel` tags. Use `\hookrightarrow`, or replace the imported sequence
  by the native `\<hookrightarrow\>` symbol.
- When renaming notation before import, a LaTeX line break such as
  `\\[4pt]` is not the beginning of display math. Exclude these line
  breaks from math-span detection; otherwise replacements can leak into
  intervening prose. Protect styled letters and distinguish local uses
  of the same symbol before applying any mathematical renaming.

- Parameterized LaTeX macro expansion must preserve control-word boundaries:
  `\newcommand{\ip}[2]{\langle#1,#2\rangle}` can become the unknown
  `\langleh` under textual substitution. Put a separating space before the
  parameter (or preserve TeX tokens) before running `prep.py`.
- Sized norm delimiters such as `\left\|...\right\|` can import as single
  bars or malformed nested `around` nodes. For a large conversion, protect
  each matched norm as a one-argument marker before import and replace that
  marker by native `around`/`around*` with both delimiters `<||>` after import.
  Check nested norms, and compare statement/proof counts before typesetting.
- A norm-token scanner must reject a backslash preceded by another backslash:
  in `\\|x-y|`, the first two backslashes are a row break, followed by an
  absolute-value bar. Treating its second backslash as the start of `\|`
  reverses later norm pairing across entire sections. Validate that protected
  norm pairs stay inside their math environments and keep braces balanced.
- Symbols are written with backslashes inside the angle brackets:
  `\<frak-d\>`, `\<frak-S\>`, `\<alpha\>`. Writing `<frak-d>` calls an
  undefined macro and prints a red placeholder in the PDF; no error is raised.
  After a scripted rename, grep the .tm for `<frak-`/`<cal-` without the
  leading backslash and check the rendered page.
