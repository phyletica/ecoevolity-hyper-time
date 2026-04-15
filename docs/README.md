This directory contains the source files for the project documentation, which
are built via quarto.
Quarto is included in the project conda environment, so to build and/or publish
the documentation using the quarto commands below, you can activate the project
conda environment:

    micromamba activate hyper-time

To build the html documentation from the source files, you can use the
following quarto command from inside this directory:

    quarto render --to html

After running this command, the generated HTML files will be in the `_build`
directory.
To publish the documentation via GitHub Pages (via the gh-pages branch of the
repo), use the following command from inside this directory:

    quarto publish gh-pages
