# User Manual

The end-user manual is a multi-page [Quarto](https://quarto.org/) website
describing how to use the Fair Data Finder application. The site is configured
by `_quarto.yml` and composed of one `.qmd` file per tab.

## Structure

| Page | File |
|------|------|
| Introduction & Logging in | `index.qmd` |
| Search | `search.qmd` |
| Register | `register.qmd` |
| Domains | `domains.qmd` |
| Keywords | `keywords.qmd` |
| Groups | `groups.qmd` |
| Concepts | `concepts.qmd` |
| Data model | `data-model.qmd` |
| Metadata schema | `metadata-schema.qmd` |
| STAC | `stac.qmd` |
| API | `api.qmd` |

## Render locally

1. [Install pixi](https://pixi.sh/latest/installation/)

2. `cd` into this folder:

   ```bash
   cd docs/manual
   ```

3. Preview the site with hot-reload (recommended during authoring):

   ```bash
   pixi run preview
   ```

4. Or render the full site to `_site/`:

   ```bash
   pixi run render
   ```

The rendered site opens in your browser automatically when using `preview`.
The `render` command writes output to `_site/` (git-ignored).
