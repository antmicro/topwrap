# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    ?= -W --keep-going
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

IR_CLASSES    = $(BUILDDIR)/ir_classes.mmd

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

$(IR_CLASSES):
	@mkdir -p $(BUILDDIR)
	@(cd ..; pyreverse --output-directory docs/$(BUILDDIR)/ --output mmd topwrap.model --no-standalone)
	@echo "%%{init: {'theme': 'neutral', 'layout': 'elk'}}%%" > $@
	@cat $(BUILDDIR)/classes.mmd >> $@
	@rm $(BUILDDIR)/classes.mmd $(BUILDDIR)/packages.mmd

.PHONY: help Makefile $(IR_CLASSES)

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile $(IR_CLASSES)
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
