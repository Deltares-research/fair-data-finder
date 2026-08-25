# User Manual

The end-user manual is written in [Quarto](https://quarto.org/) (`user_manual.qmd`) and describes how to use the Fair Data Finder application.

## Render locally

1. [Install pixi](https://pixi.sh/latest/installation/)

2. `cd` into this folder:

   ```bash
   cd docs/manual
   ```

3. Render as HTML:

   ```bash
   pixi run render_html
   ```

4. Render as PDF:

   ```bash
   pixi run install_tinytex
   pixi run render_pdf
   ```
