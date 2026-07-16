# Third-Party Notices

MoneyFlow depends on open-source software. Ordinary Python dependencies are
declared in `pyproject.toml` and installed via pip; their licences are
distributed with those packages and are not reproduced here. This file records
third-party material that warrants explicit attribution because it is loaded or
referenced directly by the application.

## Bundled at runtime via CDN

### `@google/model-viewer`

The optional animated 3D logo component
(`src/moneyflow/ui/components/logo_animation.py`) loads Google's
`<model-viewer>` web component from a public CDN at runtime:

- Project: https://modelviewer.dev / https://github.com/google/model-viewer
- Licence: Apache License 2.0
- Copyright: © Google LLC

`model-viewer` is not vendored into this repository; it is fetched by the browser
when the (optional) logo asset is present. No Google trademark or asset is
redistributed here.

## Notes on assets

- The original branded 3D logo asset is **not** included in this open-source
  edition. The logo component degrades gracefully when the asset is absent. Any
  logo you add is your own responsibility to licence.

## Reporting

If you believe attribution is missing or incorrect, please open an issue or a
pull request updating this file.
