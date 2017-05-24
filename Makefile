#!/usr/bin/make -f

############################################################
### get all the ./configure arguments into this Makefile ###
############################################################

# install architecture-independent files in PREFIX [/usr/local]
prefix:=/usr
# install architecture-dependent files in EPREFIX [PREFIX]
exec_prefix:=${prefix}
# user executables [EPREFIX/bin]
bindir:=${exec_prefix}/bin
# system admin executables [EPREFIX/sbin]
sbindir:=${exec_prefix}/sbin
# program executables [EPREFIX/libexec]
libexecdir:=${prefix}/lib/simbuto
# read-only single-machine data [PREFIX/etc]
sysconfdir:=/etc
# modifiable architecture-independent data [PREFIX/com]
sharedstatedir:=${prefix}/com
# modifiable single-machine data [PREFIX/var]
localstatedir:=/var
# modifiable per-process data [LOCALSTATEDIR/run]
runstatedir:=${localstatedir}/run
# object code libraries [EPREFIX/lib]
libdir:=${exec_prefix}/lib
# C header files [PREFIX/include]
includedir:=${prefix}/include
# C header files for non-gcc [/usr/include]
oldincludedir:=/usr/include
# read-only arch.-independent data root [PREFIX/share]
datarootdir:=${prefix}/share
# read-only architecture-independent data [DATAROOTDIR]
datadir:=${datarootdir}
# info documentation [DATAROOTDIR/info]
infodir:=${prefix}/share/info
# locale-dependent data [DATAROOTDIR/locale]
localedir:=${datarootdir}/locale
# man documentation [DATAROOTDIR/man]
mandir:=${prefix}/share/man
# documentation root [DATAROOTDIR/doc/simbuto]
docdir:=${datarootdir}/doc/${PACKAGE_TARNAME}
# html documentation [DOCDIR]
htmldir:=${docdir}
# dvi documentation [DOCDIR]
dvidir:=${docdir}
# pdf documentation [DOCDIR]
pdfdir:=${docdir}
# ps documentation [DOCDIR]
psdir:=${docdir}

configure_dirs = bindir sbindir libexecdir sysconfdir sharedstatedir \
	localstatedir runstatedir libdir includedir oldincludedir datarootdir \
	datadir infodir localedir mandir docdir htmldir dvidir pdfdir psdir

$(foreach configure_dir,$(configure_dirs),\
	$(eval $(configure_dir) := $(abspath $(DESTDIR)/$($(configure_dir)))))
# $(foreach configure_dir,$(configure_dirs),\
# 	$(info $(configure_dir) := $($(configure_dir))))

#############################
### The local directories ###
#############################

local_sysconfdir = etc
local_mandir = man
local_bindir = bin
local_localedir = locale
local_datarootdir = share
local_libdir = lib

installed_files_file = installed_files.tmp

# all pofiles
POFILES = $(shell find $(local_localedir) -type f -iname '*.po')
# the corresponding mofiles
MOFILES = $(POFILES:.po=.mo)
# temporary pot-file template
POTFILE = $(local_localedir)/simbuto.pot

# all markdown manpages
MDMANPAGES = $(shell find $(local_mandir) -type f -iname '*.1.md')
# corresponding groff manpages
GFMANPAGES = $(MDMANPAGES:.1.md=.1)

# source files that contain translatable text - the _(...) function
# that is, all python files
PYTHONFILES = $(shell find $(local_bindir) $(local_libdir) -type f -exec file {} \; | perl -ne 'print if s/^([^:]+):.*python.*$$/$$1/ig')

# pandoc options for manpage creation
PANDOCOPTS = -f markdown -t man --standalone
 
# default target
.PHONY: all
all: $(MOFILES) $(GFMANPAGES) $(SIMBUTOPYTHONINIT)


# create rule to install a FILE into the TARGET_DIRECTORY
# FILE can be a relative path from here
# $(call install_rule,FILE,TARGET_DIRECTORY)
define install_rule
$$(eval _target = $$(abspath $$(addprefix $(2)/,$$(shell echo $(1) | perl -pe 's|^[^/]*/+||g'))))
$$(_target): $(1) | $$(dir $$(_target))
	cp -L $$< $$@
	@echo $$@ >> $(installed_files_file)
$$(eval install_target_dirs = $$(install_target_dirs) $$(dir $$(_target)))
$$(eval install_targets = $$(install_targets) $$(_target))
endef

# define the local content that is to install
local_datarootdir_toinstall = $(shell find $(local_datarootdir) -not -type d)
local_mandir_toinstall = $(GFMANPAGES)
local_localedir_toinstall = $(MOFILES)
local_sysconfdir_toinstall = $(shell find $(local_sysconfdir) -not -type d)
local_bindir_toinstall = $(shell find $(local_bindir) -not -type d)
local_libdir_toinstall = $(shell find $(local_libdir) -not -type d)

# set up install rules for all configure directories
$(foreach configure_dir,$(configure_dirs),\
	$(foreach file,$(local_$(configure_dir)_toinstall),\
		$(eval $(call install_rule,$(file),$($(configure_dir))))))

# build the manpages
# manpages:
%.1: %.1.md 
	pandoc $(PANDOCOPTS) -Vfooter='Version $(SIMBUTOVERSION)' -Vdate='$(SIMBUTODATE)' -o $@ $<

# create the pot-file with all translatable strings from the srcfiles
$(POTFILE): $(PYTHONFILES)
	xgettext -L Python -o $(POTFILE) $(PYTHONFILES)

# update the translated catalog
%.po: $(POTFILE)
	VERSION_CONTROL=off msgmerge -U --backup=off $@ $<
	touch $@ # make sure timestamp was updated

# compile the translations
%.mo: %.po
	msgfmt -o $@ $<

$(sort $(install_target_dirs)): % :
	mkdir -p $@
	@echo $@ >> $(installed_files_file)

.PHONY: install
install: $(sort $(install_targets))
	-@sort -u $(installed_files_file) -o $(installed_files_file)
	
# remove a file/folder without asking
# $(call remove,PATH)
# This is only to display a newline after the command
define remove
rm -rf $(1)

endef

.PHONY: uninstall
uninstall:
	$(foreach file,$(sort $(install_targets) $(shell cat $(installed_files_file))),$(call remove,$(file)))
	rm -f $(installed_files_file)
	@echo WARNING: There might still be some empty folders left. This should not be a problem.
	
.PHONY: clean
clean:
	rm -f $(MOFILES) $(POTFILE) $(GFMANPAGES)
	rm -rf $(addprefix $(DEBIAN)/,files *.substvars *.debhelper simbuto debhelper-build-stamp *.debhelper.log)
	rm -f $(installed_files_file)


	
