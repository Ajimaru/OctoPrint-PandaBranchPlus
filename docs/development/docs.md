# Building the docs

The docs are MkDocs Material; the API pages are generated (mkdocstrings for
Python, jsdoc-to-markdown for JavaScript).

## Local build

```bash
pip install -r requirements-docs.txt
pip install octoprint       # mkdocstrings imports the package
pip install -e .

# optional: regenerate the JS API page
npm install --no-save jsdoc-to-markdown
./scripts/generate-jsdocs.sh

mkdocs serve                # live preview at http://127.0.0.1:8000
mkdocs build --strict       # what CI runs; fails on warnings
```

## Deployment

`.github/workflows/docs.yml` builds and deploys to GitHub Pages on every
push to `main` that touches docs, the mkdocs config, or the plugin sources
(the API pages depend on them). It can also be run manually via
_workflow_dispatch_.

One-time repository setup: _Settings → Pages → Source: GitHub Actions_.

## Conventions

- `docs/api/python.md` contains mkdocstrings directives (`::: module.Class`)
  — it is excluded from pre-commit's Prettier pass so the directive
  indentation survives. Edit prose there carefully.
- `docs/api/javascript.md` is fully generated; do not edit by hand.
- `mkdocs build --strict` treats broken nav entries and links as errors —
  add new pages to the `nav:` section in `mkdocs.yml`.
