# texmacs-skill

An agent skill for working with [GNU TeXmacs](https://www.texmacs.org)
documents: reading and writing the `.tm` format (Cork encoding), running
TeXmacs headless from Scheme, typesetting and exporting to PDF and HTML,
converting LaTeX articles and beamer talks to native TeXmacs, restructuring
series of documents, writing style packages and plugins, and checking the
result (unresolved references, undefined tags, bracket markup, MathJax).

`SKILL.md` is the guide; `scripts/` holds the companion tools:

- `scripts/latex2tm/`: headless driver (`run.sh`, `dump.scm`), stree
  reader/writer (`stree.py`), the LaTeX and beamer conversion pipeline, and
  typesetting helpers.
- `scripts/restructure/`: tools on stree dumps: bracket markup (`scan.py`,
  `fixaround.py`, `around_pairs.py`, `rebracket.py`, `bars.py`), non-breaking
  spaces (`nbsp.py`), outlines, reports and slide-fit checks.
- `scripts/mathjax-check/`: render every formula of an HTML export with
  MathJax and group the errors.

## Installation

For Claude Code, clone it as a skill, either for the user or for a project:

```sh
git clone https://github.com/mgubi/texmacs-skill ~/.claude/skills/texmacs
# or, inside a repository
git submodule add https://github.com/mgubi/texmacs-skill skills/texmacs
```

Keep the relative layout of `scripts/` intact: the restructuring tools import
`stree.py` from the sibling `latex2tm/` directory. Project-specific
additions are best kept in a separate local skill that refers to this one.
The conventions in `SKILL.md` (slanted inequalities, upright differentials
and derivative operators, non-breaking spaces before references, brackets as
`around`) are mandatory for every document.

The scripts assume macOS paths for TeXmacs (`run.sh`), Python 3 and, for some
checks, `mutool` (MuPDF) and ImageMagick.

## License

MIT; see [LICENSE](LICENSE).
