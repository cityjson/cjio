# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    = -E -a
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = cjio
SOURCEDIR     = source
BUILDDIR      = ../../cjio-docs

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
api:
	sphinx-apidoc -f -o ./source ../cjio ../cjio/*cjio* ../cjio/*convert* ../cjio/*errors* ../cjio/*geom_help* ../cjio/*remove_textures* ../cjio/*subset* ../cjio/*utils* ../cjio/*validation*
buildandcommithtml: html
	cd $(BUILDDIR)/html; git add . ; git commit -m "rebuilt docs"; git push origin gh-pages
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
