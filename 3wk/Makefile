CP=cp
CD=cd
RM=rm
EDITOR=vim
NSDIR=ns-allinone-3.17/ns-3.17
SCRATCHDIR=scratch
WAFRUN=./waf --run
SOURCEDIR=src
SOURCEFILE=lab3-task2-timmermanm.cc
EXECFILE=$(patsubst %.cc,%,$(SOURCEFILE))

run:
	$(CP) $(SOURCEDIR)/$(SOURCEFILE) $(NSDIR)/$(SCRATCHDIR)/ && \
	$(CD) $(NSDIR) && \
	$(WAFRUN) $(SCRATCHDIR)/$(EXECFILE)

edit:
	$(EDITOR) $(SOURCEDIR)/$(SOURCEFILE)

clean:
	$(RM) $(NSDIR)/$(SCRATCHDIR)/$(SOURCEFILE)
