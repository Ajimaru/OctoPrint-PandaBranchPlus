# Contributing

The short version — the full text lives in
[CONTRIBUTING.md](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/blob/main/CONTRIBUTING.md).

## Workflow

- Branch from `dev`, open PRs **into `dev`** (never directly into `main`).
- Rebase on `dev` before requesting review — merges are fast-forward only,
  squash/merge-commits are disabled.
- Keep commits focused; Conventional-Commit-style subjects are appreciated.

## Hooks and gates

```bash
git config core.hooksPath .githooks   # once, after cloning
```

Do **not** run `pre-commit install` — the repo drives pre-commit through its
own hook wrapper. The suite includes black, isort, ruff, flake8 (88 cols,
E203/W503/E265 ignored), pyupgrade, bandit, eslint, prettier, djlint,
shellcheck, codespell, lessc (compiles + minifies the CSS) and the
translation sync check.

## Style notes

- `rules.py` stays **pure** — no OctoPrint imports, no I/O. New rule logic
  needs unit tests next to it.
- The generated `static/css/pandabranchplus.css` is written by the lessc
  hook; edit `static/less/pandabranchplus.less` instead.
- User-visible strings go through the translation layer (`_()` / `gettext`)
  — never hardcode.
