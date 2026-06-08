# Project docs and manuscript

This directory contains the source files for the project documentation and
manuscript, which are both built separately via quarto.
Quarto is included in the project conda environment, so to build and/or publish
the documentation using the quarto commands below, you can activate the project
conda environment:

    micromamba activate hyper-time

## Building and publishing the project's documentation

To build the html documentation from the source files, you can use the
following quarto command from inside this directory:

    quarto render --profile docs --to html

After running this command, the generated HTML files will be in the `_docs`
directory.
To publish the HTML documentation in the `_docs` directory to GitHub Pages
(via the gh-pages branch of the repo), use the following command from inside
this directory:

    quarto publish gh-pages --profile docs --no-render

## Building the project's manuscript

To build the project's manuscript, use:

    quarto render --profile ms

This will render the manuscript source content (in the `manuscript.qmd` file)
into PDF, HTML, and docx formats. The outputs will be in the
`_ms` directory.

**NOTE**: don't `publish` the manuscript to `gh-pages`, because this would
overwrite the documentation.
