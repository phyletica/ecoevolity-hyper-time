# Project docs and manuscript

This directory contains the source files for the project documentation and
manuscript, which are both built separately via quarto.
Quarto is included in the project conda environment, so to build and/or publish
the documentation using the quarto commands below, you can activate the project
conda environment:

    conda activate hyper-time

Or, if you are using micromamba:

    micromamba activate hyper-time

## Building and publishing the project's documentation

The source content for the documentation is in the `.qmd` markdown-formatted
files in this directory.
To build the html documentation from these source files, you can use the
following quarto command from inside this directory:

    quarto render --profile docs --to html

After running this command, the generated HTML files will be in the `_docs`
directory.
To publish the HTML documentation in the `_docs` directory to GitHub Pages
(via the gh-pages branch of the repo), use the following command from inside
this directory:

    quarto publish gh-pages --profile docs --no-render

## Building the project's manuscript

The source content for the project's manuscript is in the `manuscript.qmd`
markdown-formatted file.
To render the manuscript in PDF, HTML, and docx formats, use:

    quarto render --profile ms

The PDF, HTML, and docx output files will be in the `_ms` directory.

**NOTE**: don't `publish` the manuscript to `gh-pages`, because this would
overwrite the documentation.
